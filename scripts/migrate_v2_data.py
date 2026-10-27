#!/usr/bin/env python3
"""One-time migration utility for BLOCK Simulator v2 data files (§6.10, D15).

Per Owner Decision D15:
- JSON files in `data/` and `cards/v2/` are canonical and hand-editable.
- Cards in `cards/v2/` are NEVER generated or overwritten by build scripts.
- Use `scripts/validate_v2_data.py` to validate data and cards against schemas.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="One-time v2.1 seed data migration tool (never touches cards/v2/).")
    parser.add_argument(
        "--apply-seed-data",
        action="store_true",
        help="Copy canonical seed schemas and data files from handoff_seed/ into schemas/ and data/ (never touches cards/v2/).",
    )
    args = parser.parse_args(argv)
    if not args.apply_seed_data:
        print("NOTE: data/*.json and cards/v2/*.json are canonical (D15). Running validate_v2_data.py...")
        from scripts.validate_v2_data import validate_all

        validate_all(ROOT, verbose=True)
        return 0

    seed_dir = ROOT / "handoff_seed"
    if not seed_dir.exists():
        print("ERROR: handoff_seed/ directory not found.", file=sys.stderr)
        return 1

    for spath in sorted((seed_dir / "schemas").glob("*.schema.json")):
        shutil.copy2(spath, ROOT / "schemas" / spath.name)
    for dpath in sorted((seed_dir / "data").glob("*.json")):
        shutil.copy2(dpath, ROOT / "data" / dpath.name)

    print("Copied schemas and data from handoff_seed/ (cards/v2/ untouched).")
    from scripts.validate_v2_data import validate_all

    validate_all(ROOT, verbose=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
