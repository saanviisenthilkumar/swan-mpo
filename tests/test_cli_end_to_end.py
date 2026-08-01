import csv
import subprocess, sys
from importlib.resources import files
from pathlib import Path

def run(*a): return subprocess.run([sys.executable,'-m','swan_mpo',*map(str,a)],text=True,capture_output=True)

def test_calibrate_targets_cli(tmp_path):
    r=files('swan_mpo.resources'); out=tmp_path/'cal.csv'
    p=run('calibrate-targets','--reference-redocking',r/'example_reference_redocking.csv','--output',out)
    assert p.returncode==0 and out.exists() and '2 target calibration row' in p.stdout

def test_validate_raw_cli():
    r=files('swan_mpo.resources')
    p=run('validate','--docking',r/'example_candidate_docking.csv','--adme',r/'example_adme.csv','--toxicity',r/'example_toxicity.csv','--config',r/'example_config.json','--reference-redocking',r/'example_reference_redocking.csv')
    assert p.returncode==0 and '"status": "PASS"' in p.stdout and '"compounds": 2' in p.stdout

def test_score_raw_cli(tmp_path):
    r=files('swan_mpo.resources'); out=tmp_path/'out'
    p=run('score','--docking',r/'example_candidate_docking.csv','--adme',r/'example_adme.csv','--toxicity',r/'example_toxicity.csv','--config',r/'example_config.json','--reference-redocking',r/'example_reference_redocking.csv','--panels','Colon','--output-dir',out)
    assert p.returncode==0
    for name in ['swan_panel_scores.csv','compound_safety_adme_desirabilities.csv','panel_liability_desirabilities.csv','target_level_binding.csv','target_calibration_used.csv','run_manifest.json']: assert (out/name).is_file()

def test_allow_missing_predictors_is_persisted_in_score_outputs(tmp_path):
    """Using the escape hatch must be impossible to hide in shareable artifacts."""
    import json
    from pathlib import Path
    from swan_mpo.cli import main
    import sys

    resources = files('swan_mpo.resources')
    outdir = tmp_path / 'nonstandard'
    old = sys.argv[:]
    try:
        sys.argv = [
            'swan-mpo', 'score',
            '--docking', str(resources / 'example_candidate_docking.csv'),
            '--adme', str(resources / 'example_adme.csv'),
            '--toxicity', str(resources / 'example_toxicity.csv'),
            '--config', str(resources / 'example_config.json'),
            '--reference-redocking', str(resources / 'example_reference_redocking.csv'),
            '--allow-missing-predictors',
            '--output-dir', str(outdir),
        ]
        main()
    finally:
        sys.argv = old

    metadata = json.loads((outdir / 'run_metadata.json').read_text(encoding='utf-8'))
    assert metadata['nonstandard_mode'] is True
    with (outdir / 'warnings.csv').open(newline='', encoding='utf-8') as handle:
        rows = list(csv.DictReader(handle))
    assert any(row['code'] == 'NONSTANDARD_MODE_ACTIVATED' for row in rows)
