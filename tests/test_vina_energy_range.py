import json, stat
from pathlib import Path
from swan_mpo.vina_redocking import load_vina_redocking_config, run_vina_reference_redocking

NATIVE="""ROOT\nATOM      1  C1  LIG A   1       0.000   0.000   0.000  0.00  0.00    0.000 C\nENDROOT\nTORSDOF 0\n"""
RECEPTOR="""ATOM      1  C1  REC A   1      10.000  10.000  10.000  0.00  0.00    0.000 C\n"""
POSE="""MODEL 1\nREMARK VINA RESULT:    -8.000      0.000      0.000\nROOT\nATOM      1  C1  LIG A   1       0.100   0.000   0.000  0.00  0.00    0.000 C\nENDROOT\nENDMDL\n"""

def test_energy_range_is_loaded_and_passed(tmp_path):
    receptor=tmp_path/'rec.pdbqt'; ligand=tmp_path/'lig.pdbqt'
    receptor.write_text(RECEPTOR); ligand.write_text(NATIVE)
    fake=tmp_path/'fake_vina.py'
    fake.write_text('#!/usr/bin/env python3\nimport sys\nfrom pathlib import Path\na=sys.argv[1:]\nPath(a[a.index("--out")+1]).write_text('+repr(POSE)+')\n')
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    cfg={'defaults':{'energy_range':4},'targets':[{'target':'T1','pdb_id':'1ABC','receptor_pdbqt':str(receptor),'native_ligand_pdbqt':str(ligand),'center':[0,0,0],'size':[20,20,20]}]}
    cp=tmp_path/'cfg.json'; cp.write_text(json.dumps(cfg))
    normalized=load_vina_redocking_config(cp)
    assert normalized['targets'][0]['energy_range']==4
    rows,cal,runs=run_vina_reference_redocking(cp,tmp_path/'out',vina_executable=str(fake))
    assert runs[0]['energy_range']==4
    assert '--energy_range 4.0' in runs[0]['command']
