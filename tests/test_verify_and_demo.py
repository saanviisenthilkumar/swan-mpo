import json
import os
import subprocess
import sys


def run(*args):
    env=dict(os.environ)
    env['PYTHONPATH']='src' + (os.pathsep + env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
    return subprocess.run([sys.executable,'-m','swan_mpo',*args], text=True, capture_output=True, env=env)


def test_verify_command_passes_core_checks():
    p=run('verify')
    assert p.returncode==0, p.stderr
    payload=json.loads(p.stdout)
    assert payload['status']=='PASS'
    assert payload['checks']['locked_model_hash']['status']=='PASS'
    assert payload['checks']['published_calibration_hash']['status']=='PASS'


def test_score_demo_writes_full_audit_package(tmp_path):
    p=run('score','--demo','--output-dir',str(tmp_path))
    assert p.returncode==0, p.stderr
    expected={
        'swan_panel_scores.csv','compound_safety_adme_desirabilities.csv',
        'panel_liability_desirabilities.csv','target_level_binding.csv',
        'target_calibration_used.csv','warnings.csv','run_metadata.json',
        'run_manifest.json','run.log'
    }
    assert expected.issubset({x.name for x in tmp_path.iterdir()})
    metadata=json.loads((tmp_path/'run_metadata.json').read_text())
    assert metadata['locked_model_sha256']=='97799e91f23803de3b9a477aea3bbcfb061f1b1d9abebdecfdadcd1b537f4454'
    assert metadata['demo'] is True
