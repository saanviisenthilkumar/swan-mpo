from pathlib import Path
from swan_mpo.provenance import base_run_metadata, portable_argv, portable_text


def test_portable_argv_redacts_home_and_console_script():
    home=str(Path.home())
    argv=[home+'/.venv/bin/swan-mpo','score','--docking',home+'/data/docking.csv']
    got=portable_argv(argv)
    assert got[0]=='swan-mpo'
    assert got[-1]=='$HOME/data/docking.csv'
    meta=base_run_metadata(command='score', argv=argv)
    assert ('/'+'Users'+'/') not in meta['command_line']
    assert home not in meta['command_line']
    assert '$HOME/data/docking.csv' in meta['command_line']
