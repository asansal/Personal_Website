#!/usr/bin/env python3
"""
scripts/fix_csv.py
──────────────────
One-time utility to repair a malformed personal_knowledge.csv.

Problem it solves
-----------------
If the CSV was written without quoting the Content column, rows like:

  personal,bio,I work at Acme, leading AI projects, based in Madrid.

are parsed as 5 fields instead of 3.  This script re-emits the file
with every Content field properly double-quoted and any internal
double-quotes escaped as "".

Usage
-----
  python scripts/fix_csv.py                          # uses default path
  python scripts/fix_csv.py data/my_knowledge.csv    # custom path
"""

import csv
import sys
from pathlib import Path

DEFAULT_PATH = Path("data/personal_knowledge.csv")
EXPECTED_COLS = 3   # Category, Topic, Content


def fix_csv(src: Path) -> None:
    if not src.exists():
        print(f"[ERROR] File not found: {src}")
        sys.exit(1)

    raw_lines = src.read_text(encoding="utf-8").splitlines()
    repaired_rows = []

    for i, line in enumerate(raw_lines):
        line = line.strip()
        if not line:
            continue

        # Try standard parsing first
        try:
            row = next(csv.reader([line]))
            if len(row) == EXPECTED_COLS:
                repaired_rows.append(row)
                continue
        except csv.Error:
            pass

        # Fallback: split on first two commas → everything after is the Content
        parts = line.split(",", EXPECTED_COLS - 1)
        if len(parts) < EXPECTED_COLS:
            print(f"[SKIP] Line {i+1} has fewer than {EXPECTED_COLS} fields: {line!r}")
            continue

        row = [p.strip().strip('"') for p in parts]
        repaired_rows.append(row)
        if i > 0:  # don't warn on header
            print(f"[FIXED] Line {i+1}: split into {len(row)} fields.")

    if not repaired_rows:
        print("[ERROR] No rows recovered. Check the file manually.")
        sys.exit(1)

    # Back up original
    backup = src.with_suffix(".csv.bak")
    backup.write_bytes(src.read_bytes())
    print(f"[OK] Backup saved to {backup}")

    # Write repaired file with QUOTE_ALL so every field is safely quoted
    with open(src, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(repaired_rows)

    print(f"[OK] Repaired CSV written to {src}  ({len(repaired_rows)-1} data rows)")


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PATH
    fix_csv(path)