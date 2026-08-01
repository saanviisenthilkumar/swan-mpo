#!/usr/bin/env python3
"""Create a local, git-ignored canonical mTOR/4JSP real-Vina config.

The script never copies structural files.  It searches the canonical project
location first, verifies the historical tight-box config when available, records
fresh hashes/sizes for the receptor/native ligand, and writes a local JSON config.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path

EXPECTED_CONFIG_TIGHT_SHA256 = "af0147f5f1b7e516d2612bcd31923fd360f17931461255cb4934a7373ac51506"
EXPECTED_RECEPTOR_SIZE = 2171840
EXPECTED_LIGAND_SIZE = 4681


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def candidate_dirs():
    home=Path.home()
    preferred=home/'Desktop'/'mpo_project'/'phase3_target_pdb_validation'/'redocking'/'4JSP'
    yield preferred
    desktop=home/'Desktop'
    if desktop.exists():
        for receptor in desktop.rglob('4JSP_receptor.pdbqt'):
            yield receptor.parent

seen=set(); chosen=None
for directory in candidate_dirs():
    try: directory=directory.resolve()
    except Exception: continue
    if directory in seen: continue
    seen.add(directory)
    receptor=directory/'4JSP_receptor.pdbqt'
    ligand=directory/'AGS_native.pdbqt'
    if receptor.is_file() and ligand.is_file():
        chosen=(directory,receptor,ligand)
        break
if not chosen:
    raise SystemExit(
        "Could not find 4JSP_receptor.pdbqt and AGS_native.pdbqt under the expected "
        "Desktop project tree. Locate those two canonical phase3 redocking files and "
        "pass their directory by editing this local helper or the template config."
    )

directory,receptor,ligand=chosen
config_tight=directory/'config_tight.txt'
config_hash=sha256(config_tight) if config_tight.is_file() else None
if config_hash is not None and config_hash != EXPECTED_CONFIG_TIGHT_SHA256:
    raise SystemExit(
        f"STOP: config_tight.txt hash mismatch. Observed {config_hash}; expected "
        f"{EXPECTED_CONFIG_TIGHT_SHA256}. Do not run canonical verification from this directory."
    )

size_warnings=[]
if receptor.stat().st_size != EXPECTED_RECEPTOR_SIZE:
    size_warnings.append(f"4JSP_receptor.pdbqt size {receptor.stat().st_size} != audited {EXPECTED_RECEPTOR_SIZE}")
if ligand.stat().st_size != EXPECTED_LIGAND_SIZE:
    size_warnings.append(f"AGS_native.pdbqt size {ligand.stat().st_size} != audited {EXPECTED_LIGAND_SIZE}")

payload={
  "rmsd_cutoff_A":2.0,
  "required_vina_version":"1.2.7",
  "local_input_provenance":{
    "source_directory":"$HOME/"+str(directory.relative_to(Path.home())) if Path.home() in directory.parents else str(directory),
    "canonical_config_tight_sha256":config_hash,
    "receptor_sha256":sha256(receptor),
    "receptor_size_bytes":receptor.stat().st_size,
    "native_ligand_sha256":sha256(ligand),
    "native_ligand_size_bytes":ligand.stat().st_size,
    "warnings":size_warnings,
  },
  "targets":[{
    "target":"mTOR","pdb_id":"4JSP",
    "receptor_pdbqt":str(receptor),"native_ligand_pdbqt":str(ligand),
    "center":[49.224,-1.763,-45.895],"size":[16,16,16],
    "exhaustiveness":64,"num_modes":20,"energy_range":4,
    "seed":2026,"cpu":0,"scoring":"vina","rmsd_backend":"symmetry"
  }]
}
out=Path.cwd()/'my_real_vina_mtor.json'
out.write_text(json.dumps(payload,indent=2)+"\n",encoding='utf-8')
print(f"Wrote local config: {out}")
print(f"Canonical tight-box config hash: {config_hash or 'not found'}")
print(f"Receptor: {receptor.name} | {receptor.stat().st_size} bytes | {sha256(receptor)}")
print(f"Native ligand: {ligand.name} | {ligand.stat().st_size} bytes | {sha256(ligand)}")
if size_warnings:
    print("WARNINGS:")
    for item in size_warnings: print(" -",item)
else:
    print("Audited file sizes match the July 28 inventory.")
