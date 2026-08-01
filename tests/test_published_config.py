from importlib.resources import files
import hashlib
from swan_mpo.calibration import load_published_calibration
from swan_mpo.config import load_config

def test_exact_published_calibration_resource_hash():
    p=files('swan_mpo.resources')/'published_target_redocking_calibration.csv'
    assert hashlib.sha256(p.read_bytes()).hexdigest()=='e7584f10c0f970bb54ddf39cfdacbb6cb061bc6a3d2bd795e2d5f119efc7287c'

def test_published_reference_values():
    d={r['target']:r for r in load_published_calibration()}
    assert float(d['Bcl-2']['reference_dg']) == -11.060
    assert float(d['AR']['reference_dg']) == -11.090
    assert float(d['PI3Ka']['reference_dg']) == -8.804
    assert float(d['AKT1']['reference_dg']) == -11.370
    assert float(d['mTOR']['reference_dg']) == -6.578
    assert float(d['5AR2']['reference_dg']) == -8.963
    assert d['EGFR']['reference_dg'] == ''
    assert d['Caspase3']['reference_dg'] == ''
    assert d['ComplexI']['reference_dg'] == ''

def test_published_panel_membership():
    c=load_config('published-oncology')
    assert c['panels']['Colon']==['ComplexI','EGFR','mTOR']
    assert c['panels']['Prostate']==['5AR2','AR','Bcl-2','EGFR','mTOR']
    assert c['panels']['RCC']==['AKT1','Bcl-2','Caspase3','PI3Ka','mTOR']
