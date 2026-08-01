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
