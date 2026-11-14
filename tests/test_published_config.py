from importlib.resources import files
import hashlib
from swan_mpo.calibration import load_published_calibration
from swan_mpo.config import load_config, PUBLISHED_ONCOLOGY

def test_exact_published_calibration_resource_hash():
    p=files('swan_mpo.resources')/'published_target_redocking_calibration.csv'
    assert hashlib.sha256(p.read_bytes()).hexdigest()=='1c4d9b17a745792a38fd0b6a0fe3793730a991c3e621b0b5e10535297ea1f88e'

def test_published_reference_values():
    d={r['target']:r for r in load_published_calibration()}
    assert float(d['Bcl-2']['reference_dg']) == -11.060
    assert float(d['AR']['reference_dg']) == -11.090
    assert float(d['PI3Ka']['reference_dg']) == -8.804
    assert float(d['AKT1']['reference_dg']) == -11.370
    assert float(d['mTOR']['reference_dg']) == -6.578
    assert '5AR2' not in d
    assert d['EGFR']['reference_dg'] == ''
    assert d['Caspase3']['reference_dg'] == ''
    assert d['ComplexI']['reference_dg'] == ''

def test_published_panel_membership():
    c=load_config('published-oncology')
    assert c['panels']['Colon']==['ComplexI','EGFR','mTOR']
    assert c['panels']['Prostate']==['AR','Bcl-2','EGFR','mTOR']
    assert c['panels']['RCC']==['AKT1','Bcl-2','Caspase3','PI3Ka','mTOR']
    assert '5AR2' not in c['pdb_ids']


def test_embedded_published_config_matches_json_configuration():
    import json
    from pathlib import Path
    source_file = Path(__file__).resolve().parents[1] / 'configs/published_oncology.json'
    expected = json.loads(source_file.read_text(encoding='utf-8'))
    assert PUBLISHED_ONCOLOGY == expected
