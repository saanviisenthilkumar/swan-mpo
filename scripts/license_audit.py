from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
blocked_suffixes = {".pdb", ".pdbqt", ".sdf", ".mol", ".mol2", ".cif", ".mmcif"}
allowed_context = {"examples", "tests"}
findings = []
for path in root.rglob("*"):
    if not path.is_file() or ".git" in path.parts or ".venv" in path.parts:
        continue
    if path.suffix.lower() in blocked_suffixes:
        # Unit-test fixtures may use temporary files generated at runtime; no structural
        # assets should be committed into the repository itself.
        findings.append(str(path.relative_to(root)))
print("LICENSE/REDISTRIBUTION AUDIT:", "PASS" if not findings else "FAIL")
print("Declared source-code license: MIT")
print("Declared repository-authored data/docs license: CC BY 4.0")
print("Bundled third-party structural files:", len(findings))
for item in findings:
    print("  BLOCKED STRUCTURAL FILE:", item)
sys.exit(1 if findings else 0)
