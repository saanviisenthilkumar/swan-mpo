import json, stat
from swan_mpo.vina_redocking import run_vina_reference_redocking

NATIVE="""ROOT
ATOM      1  C1  LIG A   1       0.000   0.000   0.000  0.00  0.00    0.000 C
ATOM      2  O1  LIG A   1       1.000   0.000   0.000  0.00  0.00    0.000 OA
ENDROOT
TORSDOF 0
"""
RECEPTOR="""ATOM      1  C1  REC A   1      10.000  10.000  10.000  0.00  0.00    0.000 C
"""
POSES="""MODEL 1
REMARK VINA RESULT:    -8.000      0.000      0.000
ROOT
ATOM      1  C1  LIG A   1       0.100   0.000   0.000  0.00  0.00    0.000 C
ATOM      2  O1  LIG A   1       1.100   0.000   0.000  0.00  0.00    0.000 OA
ENDROOT
ENDMDL
MODEL 2
REMARK VINA RESULT:    -7.500      0.000      0.000
ROOT
ATOM      1  C1  LIG A   1       3.000   0.000   0.000  0.00  0.00    0.000 C
ATOM      2  O1  LIG A   1       4.000   0.000   0.000  0.00  0.00    0.000 OA
ENDROOT
ENDMDL
"""

def test_vina_runner_builds_reference_calibration(tmp_path):
    receptor=tmp_path/'rec.pdbqt'; ligand=tmp_path/'lig.pdbqt'
    receptor.write_text(RECEPTOR); ligand.write_text(NATIVE)
    fake=tmp_path/'fake_vina.py'
    fake.write_text(
        '#!/usr/bin/env python3\n'
        'import sys\n'
        'from pathlib import Path\n'
        'args=sys.argv[1:]\n'
        'if "--out" in args:\n'
        '    p=Path(args[args.index("--out")+1])\n'
        f'    p.write_text({POSES!r})\n'
        'print("fake vina")\n'
    )
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    cfg={
        'rmsd_cutoff_A':2.0,
        'defaults':{'exhaustiveness':12,'num_modes':9,'seed':2026,'cpu':1,'scoring':'vina'},
        'targets':[{'target':'T1','pdb_id':'1ABC','receptor_pdbqt':str(receptor),'native_ligand_pdbqt':str(ligand),'center':[0,0,0],'size':[20,20,20]}]
    }
    cp=tmp_path/'cfg.json'; cp.write_text(json.dumps(cfg))
    rows,cal,runs=run_vina_reference_redocking(cp,tmp_path/'out',vina_executable=str(fake))
    assert len(rows)==2
    assert abs(rows[0]['rmsd_A']-0.1)<1e-9
    assert cal[0]['validation_class']=='strict_top_pose'
    assert cal[0]['reference_dg']==-8.0
    assert (tmp_path/'out'/'target_calibration.csv').is_file()

def test_redock_reference_cli(tmp_path):
    import subprocess, sys
    receptor=tmp_path/'rec.pdbqt'; ligand=tmp_path/'lig.pdbqt'
    receptor.write_text(RECEPTOR); ligand.write_text(NATIVE)
    fake=tmp_path/'fake_vina.py'
    fake.write_text(
        '#!/usr/bin/env python3\n'
        'import sys\n'
        'from pathlib import Path\n'
        'args=sys.argv[1:]\n'
        'if "--out" in args:\n'
        '    p=Path(args[args.index("--out")+1])\n'
        f'    p.write_text({POSES!r})\n'
    )
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    cfg={'targets':[{'target':'T1','pdb_id':'1ABC','receptor_pdbqt':str(receptor),'native_ligand_pdbqt':str(ligand),'center':[0,0,0],'size':[20,20,20]}]}
    cp=tmp_path/'cfg.json'; cp.write_text(json.dumps(cfg)); out=tmp_path/'cli_out'
    p=subprocess.run([sys.executable,'-m','swan_mpo','redock-reference','--targets-config',str(cp),'--vina-executable',str(fake),'--output-dir',str(out)],text=True,capture_output=True)
    assert p.returncode==0, p.stderr
    assert (out/'reference_redocking.csv').is_file()
    assert (out/'target_calibration.csv').is_file()
