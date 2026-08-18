import subprocess,sys
def run(*a): return subprocess.run([sys.executable,'-m','swan_mpo',*a],text=True,capture_output=True)
def test_help(): assert run('--help').returncode==0
def test_version(): assert run('--version').returncode==0
def test_reproduce():
 r=run('reproduce-example'); assert r.returncode==0 and '"status": "PASS"' in r.stdout

def test_explain_model_command():
    p=run('explain-model')
    assert p.returncode==0
    assert 'Raw SwissADME/property fields' in p.stdout
    assert 'Reference-ligand Vina redocking' in p.stdout


def test_version_exposes_expected_vina(capsys):
    import pytest
    from swan_mpo.cli import main
    with pytest.raises(SystemExit) as exc:
        main(['--version'])
    assert exc.value.code == 0
    out=capsys.readouterr().out
    assert 'expected-vina=1.2.7' in out
    assert 'sha256=97799e91f23803de3b9a477aea3bbcfb061f1b1d9abebdecfdadcd1b537f4454' in out

def test_explain_model_states_consensus_logp_is_required():
    p = run('explain-model')
    assert p.returncode == 0
    assert 'Consensus Log P is required' in p.stdout
    assert 'rejected rather than imputed' in p.stdout
