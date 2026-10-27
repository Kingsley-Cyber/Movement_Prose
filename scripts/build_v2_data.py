#!/usr/bin/env python3
"""Retired data generator wrapper — delegates to scripts/validate_v2_data.py (Owner Decision D15).

Per D15 (§6.10): JSON files in `data/` and `cards/v2/` are canonical and hand-editable.
`build_v2_data.py` no longer overwrites `data/` or `cards/v2/`.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_v2_data import main as validate_main  # noqa: E402

if __name__ == "__main__":
    sys.exit(validate_main())
