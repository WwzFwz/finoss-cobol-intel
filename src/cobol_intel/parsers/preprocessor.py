"""COBOL source preprocessor.

Handles:
- Fixed-format detection and normalization (strip columns 1-6, 7, 73-80)
- Comment removal (* in column 7)
- Continuation line joining (- in column 7)
- COPY statement resolution (basic, from configurable directories)
- PIC string normalization (wrap in quotes for parser)
- Uppercase conversion
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PreprocessedSource:
    """Output of preprocessing: clean text ready for parser + metadata."""

    text: str
    original_lines: list[str]
    source_format: str  # "fixed" or "free"
    copybooks_resolved: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class COBOLPreprocessor:
    """Preprocesses COBOL source files for parsing."""

    def __init__(
        self,
        copybook_dirs: list[str | Path] | None = None,
        source_format: str = "auto",
    ):
        self.copybook_dirs = [Path(d) for d in (copybook_dirs or [])]
        self.source_format = source_format  # "fixed", "free", "auto"

    def preprocess(self, source: str, file_path: str = "") -> PreprocessedSource:
        """Preprocess COBOL source text into clean text for the parser."""
        return self._preprocess_internal(source, file_path=file_path, copy_stack=[])

    def _preprocess_internal(
        self,
        source: str,
        file_path: str = "",
        copy_stack: list[str] | None = None,
    ) -> PreprocessedSource:
        """Internal preprocessing with COPY stack tracking for cycle detection."""
        original_lines = source.splitlines()
        warnings: list[str] = []
        copybooks_resolved: list[str] = []
        copy_stack = copy_stack or []

        # Detect format
        fmt = self.source_format
        if fmt == "auto":
            fmt = self._detect_format(original_lines)

        # Phase 1: fixed-format handling
        if fmt == "fixed":
            lines = self._handle_fixed_format(original_lines, warnings)
        else:
            lines = [line.rstrip() for line in original_lines]

        # Phase 2: remove blank lines (keep structure clean)
        lines = [line for line in lines if line.strip()]

        # Phase 3: uppercase (COBOL is case-insensitive, simplifies parsing)
        lines = [self._uppercase_preserving_strings(line) for line in lines]

        # Phase 4: resolve COPY statements
        lines, resolved = self._resolve_copybooks(lines, warnings, copy_stack)
        copybooks_resolved.extend(resolved)

        # Phase 5: join into single text
        text = "\n".join(lines)

        # Phase 6: normalize PIC strings (wrap in quotes for parser)
        text = self._normalize_pic_strings(text)

        return PreprocessedSource(
            text=text,
            original_lines=original_lines,
            source_format=fmt,
            copybooks_resolved=copybooks_resolved,
            warnings=warnings,
        )

    def _detect_format(self, lines: list[str]) -> str:
        """Heuristic to detect fixed vs free format.

        Key insight: in fixed format, columns 1-6 never contain COBOL keywords
        or source code — they're sequence numbers (digits or spaces). So if the
        very first non-blank line starts with a letter at column 1, it must be
        free format.
        """
        for line in lines:
            if not line.strip():
                continue
            # If first content character is a letter at column 1, free format
            if line[0].isalpha():
                return "free"
            # Column 7 indicators are unique to fixed format
            if len(line) >= 7 and line[6] in ("*", "-", "/"):
                return "fixed"
            # Columns 1-6 are spaces/digits with content starting at col 7+
            if len(line) >= 7:
                prefix = line[:6]
                if prefix.strip() == "" or prefix.strip().isdigit():
                    col7 = line[6]
                    if col7 == " ":
                        return "fixed"
        return "free"

    def _handle_fixed_format(
        self, lines: list[str], warnings: list[str]
    ) -> list[str]:
        """Process fixed-format COBOL lines."""
        result: list[str] = []

        for i, line in enumerate(lines):
            # Pad short lines
            padded = line.ljust(80) if len(line) < 80 else line

            # Column 7: indicator
            if len(padded) >= 7:
                indicator = padded[6]
            else:
                indicator = " "

            # Comment line: skip
            if indicator in ("*", "/"):
                continue

            # Extract source area (columns 8-72, 0-indexed: 7-71)
            source_area = padded[7:72].rstrip()

            # Skip empty source area
            if not source_area.strip():
                continue

            # Continuation line: append to previous
            if indicator == "-" and result:
                # Remove leading spaces and append
                continued = source_area.lstrip()
                result[-1] = result[-1] + continued
            else:
                result.append(source_area)

        return result

    def _uppercase_preserving_strings(self, line: str) -> str:
        """Convert to uppercase but preserve string literal contents."""
        result = []
        in_string = False
        quote_char = None

        for char in line:
            if in_string:
                result.append(char)
                if char == quote_char:
                    in_string = False
            else:
                if char in ('"', "'"):
                    in_string = True
                    quote_char = char
                    result.append(char)
                else:
                    result.append(char.upper())

        return "".join(result)

    def _resolve_copybooks(
        self,
        lines: list[str],
        warnings: list[str],
        copy_stack: list[str],
    ) -> tuple[list[str], list[str]]:
        """Resolve COPY statements by inlining copybook content."""
        resolved: list[str] = []
        result: list[str] = []

        for line in lines:
            match = re.match(
                r"\s*COPY\s+(\S+?)(?:\s+REPLACING\s+(.+?))?\s*\.\s*$",
                line,
                re.IGNORECASE,
            )
            if match:
                copybook_name = match.group(1).upper()
                replacements = self._parse_copy_replacements(
                    match.group(2) or "",
                    warnings,
                )
                if copybook_name in copy_stack:
                    chain = " -> ".join([*copy_stack, copybook_name])
                    warnings.append(
                        f"Circular COPY dependency detected: {chain}"
                    )
                    result.append(line)
                    continue

                found = self._find_copybook(copybook_name)
                if found is not None:
                    content, _path = found
                    resolved.append(copybook_name)
                    # Preprocess copybook content (recursive, same format)
                    sub = COBOLPreprocessor(
                        copybook_dirs=self.copybook_dirs,
                        source_format=self.source_format,
                    )
                    sub_result = sub._preprocess_internal(
                        content,
                        copy_stack=[*copy_stack, copybook_name],
                    )
                    warnings.extend(sub_result.warnings)
                    resolved.extend(sub_result.copybooks_resolved)
                    replaced_text = self._apply_copy_replacements(
                        sub_result.text,
                        replacements,
                    )
                    result.extend(replaced_text.splitlines())
                else:
                    warnings.append(
                        f"COPYBOOK '{copybook_name}' not found in {self.copybook_dirs}"
                    )
                    result.append(line)  # Keep original COPY line
            else:
                result.append(line)

        return result, resolved

    def _find_copybook(self, name: str) -> tuple[str, Path] | None:
        """Search for a copybook file in configured directories."""
        extensions = [".cpy", ".CPY", ".cbl", ".CBL", ".copy", ".COPY", ""]
        for directory in self.copybook_dirs:
            for ext in extensions:
                path = directory / f"{name}{ext}"
                if path.exists():
                    return path.read_text(encoding="utf-8", errors="replace"), path
        return None

    def _normalize_pic_strings(self, text: str) -> str:
        """Wrap PIC clause strings in quotes so the parser can handle them.

        Transforms:  PIC 9(7)V99       ->  PIC "9(7)V99"
                     PICTURE IS X(20)  ->  PICTURE IS "X(20)"
        """
        pattern = r"\b(PIC(?:TURE)?)\s+(?:IS\s+)?([A-Z0-9()VSX]+)"
        return re.sub(pattern, r'\1 "\2"', text)

    def _parse_copy_replacements(
        self,
        clause: str,
        warnings: list[str],
    ) -> list[tuple[str, str]]:
        """Parse COPY ... REPLACING pairs from a single-line clause."""
        if not clause.strip():
            return []

        token_pattern = r'==.*?==|"[^"]*"|\'[^\']*\'|[A-Z0-9:-]+'
        tokens = re.findall(token_pattern, clause)
        replacements: list[tuple[str, str]] = []
        idx = 0

        while idx + 2 < len(tokens):
            source = tokens[idx]
            by_token = tokens[idx + 1]
            target = tokens[idx + 2]
            if by_token != "BY":
                warnings.append(f"Unsupported COPY REPLACING clause fragment: {clause}")
                break
            replacements.append(
                (source, self._strip_pseudo_text(target))
            )
            idx += 3

        if idx != len(tokens):
            warnings.append(f"Unparsed COPY REPLACING tokens in clause: {clause}")

        return replacements

    def _apply_copy_replacements(
        self,
        text: str,
        replacements: list[tuple[str, str]],
    ) -> str:
        """Apply COPY REPLACING substitutions to resolved copybook text."""
        result = text
        for source, target in replacements:
            if source.startswith("==") or source.startswith('"') or source.startswith("'"):
                result = result.replace(source, target)
                continue

            pattern = rf"(?<![A-Z0-9-]){re.escape(source)}(?![A-Z0-9-])"
            result = re.sub(pattern, target, result)
        return result

    def _strip_pseudo_text(self, token: str) -> str:
        """Remove pseudo-text delimiters used by COPY REPLACING."""
        if token.startswith("==") and token.endswith("=="):
            return token[2:-2]
        return token
