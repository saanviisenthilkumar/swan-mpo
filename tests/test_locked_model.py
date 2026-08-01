from swan_mpo.locked_model import model_source_sha256, reference_calibrated_binding
def test_locked_hash(): assert model_source_sha256()=='97799e91f23803de3b9a477aea3bbcfb061f1b1d9abebdecfdadcd1b537f4454'
def test_binding_cap(): assert reference_calibrated_binding(-9,-8)==1.0
def test_binding_ratio(): assert abs(reference_calibrated_binding(-4,-8)-0.5)<1e-12
