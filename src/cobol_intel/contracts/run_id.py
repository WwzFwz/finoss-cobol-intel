"""run_id generation and validation.

Format: run_YYYYMMDD_HHMMSS_XXXX
- Timestamp in UTC for sortability and human readability
- 4-char hex suffix for uniqueness within the same second

See ADR-014 in docs/DECISIONS.md.
"""

from __future__ import annotations

import re
import secrets
from datetime import datetime, timezone

_RUN_ID_PATTERN = re.compile(r"^run_\d{8}_\d{6}_[0-9a-f]{4}$")


def generate_run_id() -> str:
    """Generate a new run_id with current UTC timestamp."""
    now = datetime.now(timezone.utc)
    suffix = secrets.token_hex(2)  # 4 hex chars
    return f"run_{now:%Y%m%d_%H%M%S}_{suffix}"


def is_valid_run_id(run_id: str) -> bool:
    """Check if a string matches the run_id format."""
    return bool(_RUN_ID_PATTERN.match(run_id))
