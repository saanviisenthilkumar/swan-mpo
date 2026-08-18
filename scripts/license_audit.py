from pathlib import Path
import hashlib
import sys

root = Path(__file__).resolve().parents[1]
blocked_suffixes = {".pdb", ".pdbqt", ".sdf", ".mol", ".mol2", ".cif", ".mmcif"}
findings = []
for path in root.rglob("*"):
    if not path.is_file() or ".git" in path.parts or ".venv" in path.parts:
        continue
    if path.suffix.lower() in blocked_suffixes:
        findings.append(f"blocked structural asset: {path.relative_to(root)}")

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

expected = {
    "src/swan_mpo/resources/manuscript_swissadme_canonical_full.csv": "a1b6339695bba431239def8969d56244cecd978e195e5eaf2a3019ca21ec7ab1",
    "src/swan_mpo/resources/manuscript_swissadme_original_incomplete.csv": "a90b7c3cdee1d9b10257ccdf368dab6bedbe31520031113f6b1255b79deba7ca",
    "src/swan_mpo/resources/manuscript_protox_raw.csv": "4ef8ea376f89533ad3bd3afb9d810aab9c8fccc3f216179414d6de776b3f08ee",
}
for rel, digest in expected.items():
    path=root/rel
    if not path.is_file(): findings.append(f"missing licensed reproducibility input: {rel}")
    elif sha256(path) != digest: findings.append(f"licensed upstream input changed bytes: {rel}")

license_text=(root/'DATA_LICENSE.md').read_text(encoding='utf-8')
for marker in ['CC BY 4.0','CC BY-ND 4.0','SwissADME','ProTox']:
    if marker not in license_text: findings.append(f"missing license/attribution marker: {marker}")

print("LICENSE/REDISTRIBUTION AUDIT:", "PASS" if not findings else "FAIL")
print("Source-code license: MIT")
print("Repository-authored data/docs: CC BY 4.0 unless file-specific upstream notice applies")
print("SwissADME bundled exports: exact hashes + CC BY 4.0 attribution")
print("ProTox bundled raw export: exact unchanged hash + upstream CC BY-ND 4.0 notice")
print("Bundled blocked structural assets:", sum(x.startswith('blocked structural asset') for x in findings))
for item in findings: print("  FINDING:", item)
sys.exit(1 if findings else 0)
