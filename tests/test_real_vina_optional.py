import os
from pathlib import Path
import pytest
from swan_mpo.verification import run_real_vina_integration


@pytest.mark.real_vina
def test_real_vina_1_2_7_integration_when_configured(tmp_path):
    config=os.environ.get('SWAN_REAL_VINA_CONFIG')
    if not config:
        pytest.skip('Set SWAN_REAL_VINA_CONFIG to a verified redocking config to run the real Vina integration test.')
    report=run_real_vina_integration(config, output_dir=tmp_path)
    assert report['status']=='PASS'
    assert report['runs'] >= 1
    assert report['modes'] >= 1
