#!/usr/bin/env python3
"""Check or regenerate the repository's SHA-256 file manifest.

The manifest covers all version-controlled and newly added, non-ignored files
other than itself. Generated analysis outputs, local environments, and Git
metadata are excluded. The default action is read-only verification.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests/FILE_SHA256_MANIFEST.csv"


def files_in_checkout() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT, check=True, capture_output=True,
    )
    names = set(result.stdout.decode("utf-8").strip("\0").split("\0"))
    return sorted((ROOT / name for name in names
                   if name and name != str(MANIFEST.relative_to(ROOT)) and (ROOT / name).is_file()),
                  key=lambda p: p.relative_to(ROOT).as_posix())


def expected() -> list[dict[str, str]]:
    records = []
    for path in files_in_checkout():
        data = path.read_bytes()
        records.append({
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": str(len(data)),
        })
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Regenerate the manifest from the current checkout")
    args = parser.parse_args()
    target = expected()
    if args.write:
        with MANIFEST.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=("path", "sha256", "bytes"), lineterminator="\n")
            writer.writeheader()
            writer.writerows(target)
        print(f"RELEASE FILE MANIFEST: WRITTEN ({len(target)} entries)")
        return
    with MANIFEST.open(encoding="utf-8", newline="") as stream:
        actual = list(csv.DictReader(stream))
    if actual != target:
        old = {r["path"]: r for r in actual}
        current = {r["path"]: r for r in target}
        issues = sorted(path for path in (set(old) | set(current)) if old.get(path) != current.get(path))
        print(f"RELEASE FILE MANIFEST: FAIL ({len(issues)} changed/missing/unlisted files)")
        for name in issues[:35]:
            print(name)
        raise SystemExit(1)
    print(f"RELEASE FILE MANIFEST: PASS ({len(target)} entries)")


if __name__ == "__main__":
    main()
