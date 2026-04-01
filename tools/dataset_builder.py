"""Fine-tuning dataset builder for COBOL explanation models.

Walks COBOL samples through the full analysis pipeline and generates
instruction-tuning pairs in JSONL format suitable for HuggingFace
fine-tuning (Alpaca/ShareGPT style).

Each sample produces multiple training pairs:
1. Program-level: full artifacts prompt → expected program summary
2. Paragraph-level: paragraph context → expected paragraph explanation
3. Business rules: rules context → expected rules explanation

Usage:
    python tools/dataset_builder.py --samples-dir samples --output dataset/
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cobol_intel.analysis.cfg_builder import build_cfg
from cobol_intel.analysis.data_flow import analyze_data_flow
from cobol_intel.analysis.dead_code import detect_dead_code
from cobol_intel.analysis.reference_indexer import build_reference_index
from cobol_intel.analysis.rules_extractor import extract_rules
from cobol_intel.contracts.explanation_output import ExplanationMode
from cobol_intel.llm.context_builder import (
    build_paragraph_prompt,
    build_program_prompt,
    build_system_prompt,
)
from cobol_intel.parsers.antlr_parser import ANTLR4Parser
from cobol_intel.parsers.preprocessor import COBOLPreprocessor
from cobol_intel.service.pipeline import discover_cobol_files, to_ast_output


@dataclass
class TrainingSample:
    """A single instruction-tuning sample."""

    instruction: str
    input: str
    output: str
    metadata: dict


def build_dataset(
    samples_dir: Path,
    copybook_dirs: list[Path] | None = None,
    modes: list[ExplanationMode] | None = None,
) -> list[TrainingSample]:
    """Generate training samples from COBOL source files.

    For each successfully parsed program, generates:
    - Program-level samples (one per explanation mode)
    - Paragraph-level samples for each paragraph
    - Analysis summary samples (data flow, dead code)
    """
    modes = modes or list(ExplanationMode)
    samples: list[TrainingSample] = []

    cobol_files = discover_cobol_files(samples_dir)
    if not cobol_files:
        print(f"No COBOL files found in {samples_dir}")
        return samples

    parser = ANTLR4Parser()
    preprocessor = COBOLPreprocessor(
        copybook_dirs=[str(d) for d in (copybook_dirs or [])],
    )

    for cobol_file in cobol_files:
        source = cobol_file.read_text(encoding="utf-8")
        preprocessed = preprocessor.preprocess(source, file_path=str(cobol_file))
        result = parser.parse(preprocessed.text, file_path=str(cobol_file))

        if not result.success:
            print(f"  SKIP (parse failed): {cobol_file.name}")
            continue

        ast = to_ast_output(result, file_path=str(cobol_file))
        rules = extract_rules(result, file_path=str(cobol_file))
        ref_index = build_reference_index(ast)
        cfg = build_cfg(ast)
        data_flow = analyze_data_flow(ast, reference_index=ref_index)
        dead_code = detect_dead_code(ast, cfg=cfg, reference_index=ref_index)

        program_id = ast.program_id or cobol_file.stem
        meta_base = {
            "program_id": program_id,
            "file": cobol_file.name,
            "paragraphs": len(ast.paragraphs),
            "data_items": len(ast.data_items),
            "rules": len(rules.rules),
        }

        # 1. Program-level samples (one per mode)
        program_prompt = build_program_prompt(ast, rules=rules)
        for mode in modes:
            system = build_system_prompt(mode)
            instruction = _program_instruction(mode, program_id)
            expected = _program_expected_output(
                ast, rules, cfg, data_flow, dead_code, mode,
            )
            samples.append(TrainingSample(
                instruction=instruction,
                input=f"{system}\n\n{program_prompt}",
                output=expected,
                metadata={**meta_base, "type": "program", "mode": mode.value},
            ))

        # 2. Paragraph-level samples
        for para in ast.paragraphs:
            para_prompt = build_paragraph_prompt(ast, para.name, rules=rules)
            if not para_prompt:
                continue
            expected_para = _paragraph_expected_output(para, rules, program_id)
            samples.append(TrainingSample(
                instruction=(
                    f"Explain what the paragraph {para.name} does in "
                    f"COBOL program {program_id}."
                ),
                input=para_prompt,
                output=expected_para,
                metadata={
                    **meta_base, "type": "paragraph",
                    "paragraph": para.name,
                },
            ))

        # 3. Data flow summary sample
        if data_flow.edges:
            df_input = data_flow.to_mermaid()
            df_expected = _data_flow_expected_output(data_flow, program_id)
            samples.append(TrainingSample(
                instruction=(
                    f"Describe the data flow in COBOL program {program_id} "
                    f"based on this data flow diagram."
                ),
                input=df_input,
                output=df_expected,
                metadata={**meta_base, "type": "data_flow"},
            ))

        # 4. Dead code summary sample
        if dead_code.items:
            dc_input = json.dumps(
                [item.model_dump() for item in dead_code.items], indent=2,
            )
            dc_expected = _dead_code_expected_output(dead_code, program_id)
            samples.append(TrainingSample(
                instruction=(
                    f"Summarize the dead code findings for COBOL program "
                    f"{program_id}."
                ),
                input=dc_input,
                output=dc_expected,
                metadata={**meta_base, "type": "dead_code"},
            ))

        print(f"  OK: {cobol_file.name} ({program_id})")

    return samples


def _program_instruction(mode: ExplanationMode, program_id: str) -> str:
    mode_desc = {
        ExplanationMode.TECHNICAL: "a technical explanation for developers",
        ExplanationMode.BUSINESS: "a business-level explanation for stakeholders",
        ExplanationMode.AUDIT: "an audit/compliance explanation for regulators",
    }
    return (
        f"Given the following structured analysis artifacts from COBOL program "
        f"{program_id}, provide {mode_desc[mode]}."
    )


def _program_expected_output(ast, rules, cfg, data_flow, dead_code, mode):
    """Build a structured expected output from analysis artifacts.

    This is a template-based output that the model should learn to produce.
    For real fine-tuning, these would be replaced with human-written or
    LLM-generated gold-standard explanations.
    """
    lines = []
    program_id = ast.program_id or "UNKNOWN"

    lines.append(f"## {program_id}")
    lines.append("")

    # Structure summary
    lines.append(
        f"This program contains {len(ast.paragraphs)} paragraph(s) and "
        f"{len(ast.data_items)} top-level data item(s)."
    )
    if ast.procedure_using:
        lines.append(
            f"It accepts parameters via PROCEDURE DIVISION USING: "
            f"{', '.join(ast.procedure_using)}."
        )
    if ast.copybooks_used:
        lines.append(f"Copybooks used: {', '.join(ast.copybooks_used)}.")
    lines.append("")

    # Rules summary
    if rules.rules:
        lines.append(f"### Business Rules ({len(rules.rules)} found)")
        lines.append("")
        for rule in rules.rules[:10]:  # Cap for training
            lines.append(
                f"- **{rule.rule_id}** ({rule.type}): `{rule.condition}`"
            )
        lines.append("")

    # Control flow summary
    if cfg.blocks:
        lines.append(
            f"### Control Flow: {len(cfg.blocks)} block(s), "
            f"{len(cfg.edges)} edge(s)"
        )
        if cfg.perform_targets:
            targets = []
            for caller, callees in cfg.perform_targets.items():
                for callee in callees:
                    targets.append(f"{caller} -> {callee}")
            lines.append(f"PERFORM targets: {', '.join(targets[:10])}")
        if cfg.unsupported_constructs:
            lines.append(
                f"Warning: uses {', '.join(cfg.unsupported_constructs)}"
            )
        lines.append("")

    # Data flow summary
    if data_flow.edges:
        lines.append(
            f"### Data Flow: {len(data_flow.edges)} edge(s)"
        )
        if data_flow.entry_fields:
            lines.append(f"Entry fields: {', '.join(data_flow.entry_fields)}")
        if data_flow.output_fields:
            lines.append(f"Output fields: {', '.join(data_flow.output_fields)}")
        lines.append("")

    # Dead code
    if dead_code.items:
        lines.append(
            f"### Dead Code: {dead_code.total_dead} finding(s), "
            f"{dead_code.dead_code_percentage}% unreachable"
        )
        for item in dead_code.items[:5]:
            lines.append(f"- {item.type.value}: {item.name} ({item.reason})")
        lines.append("")

    return "\n".join(lines)


def _paragraph_expected_output(para, rules, program_id):
    lines = [f"**{para.name}** in program {program_id}:", ""]
    stmt_types = [s.type for s in para.statements]

    if not stmt_types:
        lines.append("This paragraph is empty.")
    else:
        lines.append(f"Contains {len(stmt_types)} statement(s): {', '.join(stmt_types)}.")

    # Mention relevant rules
    relevant = [r for r in rules.rules if r.paragraph == para.name]
    if relevant:
        lines.append("")
        lines.append(f"Business rules in this paragraph:")
        for r in relevant:
            lines.append(f"- {r.rule_id}: `{r.condition}`")

    return "\n".join(lines)


def _data_flow_expected_output(data_flow, program_id):
    lines = [f"Data flow analysis for {program_id}:", ""]
    lines.append(f"Total flow edges: {len(data_flow.edges)}")

    if data_flow.entry_fields:
        lines.append(f"Entry fields: {', '.join(data_flow.entry_fields)}")
    if data_flow.output_fields:
        lines.append(f"Output fields: {', '.join(data_flow.output_fields)}")

    # Summarize by type
    from collections import Counter
    type_counts = Counter(e.flow_type.value for e in data_flow.edges)
    lines.append("")
    lines.append("Flow breakdown:")
    for ft, count in type_counts.most_common():
        lines.append(f"- {ft}: {count}")

    return "\n".join(lines)


def _dead_code_expected_output(dead_code, program_id):
    lines = [f"Dead code findings for {program_id}:", ""]
    lines.append(
        f"{dead_code.total_dead} issue(s) found, "
        f"{dead_code.dead_code_percentage}% of paragraphs unreachable."
    )

    from collections import Counter
    type_counts = Counter(i.type.value for i in dead_code.items)
    for dtype, count in type_counts.most_common():
        lines.append(f"- {dtype}: {count}")

    if dead_code.warnings:
        lines.append("")
        lines.append("Warnings:")
        for w in dead_code.warnings:
            lines.append(f"- {w}")

    return "\n".join(lines)


def write_jsonl(samples: list[TrainingSample], output_path: Path) -> None:
    """Write samples as JSONL (Alpaca format)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for sample in samples:
            record = {
                "instruction": sample.instruction,
                "input": sample.input,
                "output": sample.output,
                "metadata": sample.metadata,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_sharegpt(samples: list[TrainingSample], output_path: Path) -> None:
    """Write samples in ShareGPT conversation format."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    conversations = []
    for sample in samples:
        conversations.append({
            "conversations": [
                {"from": "system", "value": sample.instruction},
                {"from": "human", "value": sample.input},
                {"from": "gpt", "value": sample.output},
            ],
            "metadata": sample.metadata,
        })
    output_path.write_text(
        json.dumps(conversations, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Build fine-tuning dataset from COBOL samples")
    ap.add_argument("--samples-dir", default="samples", help="COBOL samples directory")
    ap.add_argument("--copybook-dir", default="copybooks", help="Copybook directory")
    ap.add_argument("--output", default="dataset", help="Output directory")
    ap.add_argument(
        "--format", choices=["alpaca", "sharegpt", "both"], default="both",
        help="Output format",
    )
    args = ap.parse_args()

    samples_dir = Path(args.samples_dir)
    copybook_dirs = [Path(args.copybook_dir)] if Path(args.copybook_dir).exists() else []
    output_dir = Path(args.output)

    print(f"Building dataset from {samples_dir}...")
    samples = build_dataset(samples_dir, copybook_dirs)
    print(f"\nGenerated {len(samples)} training samples")

    if args.format in ("alpaca", "both"):
        alpaca_path = output_dir / "cobol_instruct_alpaca.jsonl"
        write_jsonl(samples, alpaca_path)
        print(f"Alpaca JSONL: {alpaca_path}")

    if args.format in ("sharegpt", "both"):
        sharegpt_path = output_dir / "cobol_instruct_sharegpt.json"
        write_sharegpt(samples, sharegpt_path)
        print(f"ShareGPT JSON: {sharegpt_path}")

    # Stats
    from collections import Counter
    type_counts = Counter(s.metadata["type"] for s in samples)
    print("\nSample distribution:")
    for stype, count in type_counts.most_common():
        print(f"  {stype}: {count}")


if __name__ == "__main__":
    main()
