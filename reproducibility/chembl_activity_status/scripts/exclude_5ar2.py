#!/usr/bin/env python3
"""Drop 5AR2 from the distributed ChEMBL analysis tables.

The original ChEMBL descriptor source and provenance lock are historical
evidence and are intentionally not modified by this operation.

Usage (from repository root):
    python reproducibility/chembl_activity_status/scripts/exclude_5ar2.py
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "primary_activity_status_records.csv": (190, 188),
    "secondary_activity_status_records.csv": (251, 249),
    "chembl37_external_status_cohort.csv": (251, 249),
}


def remove_target(path: Path, previous: int, current: int) -> None:
    lines = path.read_bytes().splitlines(keepends=True)
    if not lines or lines[0].split(b",", 1)[0] != b"target_label":
        raise ValueError(f"Unexpected header in {path}")
    records = lines[1:]
    if len(records) not in {previous, current}:
        raise ValueError(f"Unexpected row count in {path}: {len(records)}")

    included = [r for r in records if r.split(b",", 1)[0].upper() != b"5AR2"]
    if len(included) != current:
        raise ValueError(f"Expected {current} retained records in {path}, got {len(included)}")
    if len(included) == len(records):
        print(f"UNCHANGED {path.name}: {len(included)} records")
        return

    fd, temp_path = tempfile.mkstemp(prefix=".filter_", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.writelines([lines[0], *included])
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    print(f"FILTERED {path.name}: removed {len(records) - len(included)}, retained {len(included)}")


if __name__ == "__main__":
    for filename, counts in FILES.items():
        remove_target(ROOT / "inputs" / filename, *counts)
