"""File-based explanation cache with composite cache keys."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from cobol_intel.contracts.explanation_output import ExplanationOutput

_CACHE_DIR_NAME = ".cobol_intel_cache"
_CONTEXT_VERSION = "explain-context-v1"


@dataclass(frozen=True)
class CacheKey:
    """Composite key capturing all dimensions that affect explanation output."""

    source_hash: str  # SHA-256 of COBOL source
    parser_version: str  # parser name + grammar version
    policy_config_hash: str  # SHA-256 of serialized PolicyConfig (or "none")
    backend: str  # "claude", "openai", "ollama"
    model: str  # model ID
    mode: str  # "technical", "business", "audit"
    context_version: str  # prompt/context builder revision

    def hex_digest(self) -> str:
        """Produce a single hash from all key components."""
        combined = "|".join([
            self.source_hash,
            self.parser_version,
            self.policy_config_hash,
            self.backend,
            self.model,
            self.mode,
            self.context_version,
        ])
        return hashlib.sha256(combined.encode()).hexdigest()


def make_cache_key(
    source_text: str,
    parser_version: str,
    policy_config_json: str | None,
    backend: str,
    model: str,
    mode: str,
    context_version: str = _CONTEXT_VERSION,
) -> CacheKey:
    """Build a CacheKey from raw inputs."""
    source_hash = hashlib.sha256(source_text.encode()).hexdigest()
    policy_hash = (
        hashlib.sha256(policy_config_json.encode()).hexdigest()
        if policy_config_json else "none"
    )
    return CacheKey(
        source_hash=source_hash,
        parser_version=parser_version,
        policy_config_hash=policy_hash,
        backend=backend,
        model=model,
        mode=mode,
        context_version=context_version,
    )


class ExplanationCache:
    """File-based cache storing ExplanationOutput keyed by composite CacheKey."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self._dir = cache_dir or (Path.cwd() / _CACHE_DIR_NAME)

    @property
    def cache_dir(self) -> Path:
        return self._dir

    def get(self, key: CacheKey) -> ExplanationOutput | None:
        """Retrieve cached explanation, or None on miss."""
        path = self._path_for(key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return ExplanationOutput(**data)
        except (json.JSONDecodeError, Exception):
            return None

    def put(self, key: CacheKey, explanation: ExplanationOutput) -> Path:
        """Store explanation in cache. Returns path to cache file."""
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._path_for(key)
        path.write_text(
            explanation.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return path

    def invalidate(self, key: CacheKey) -> bool:
        """Remove a single cached entry. Returns True if it existed."""
        path = self._path_for(key)
        if path.exists():
            path.unlink()
            return True
        return False

    def clear(self) -> int:
        """Remove all cached entries. Returns count of files removed."""
        if not self._dir.exists():
            return 0
        count = 0
        for f in self._dir.glob("*.json"):
            f.unlink()
            count += 1
        return count

    def _path_for(self, key: CacheKey) -> Path:
        return self._dir / f"{key.hex_digest()}.json"
