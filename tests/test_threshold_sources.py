import json
from importlib.resources import files


def test_threshold_source_registry_is_bundled_and_classifies_design_anchors():
    data=json.loads((files('swan_mpo.resources')/'threshold_sources.json').read_text())
    text=json.dumps(data).lower()
    assert 'lipinski' in text
    assert 'veber' in text
    assert 'design' in text
