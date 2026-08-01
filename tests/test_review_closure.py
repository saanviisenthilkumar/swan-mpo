import csv
import json
from importlib.resources import files

from swan_mpo.domain_audit import calculate_domain_audit_tables
from swan_mpo.method_warnings import collect_method_warnings
from swan_mpo.calibration import load_published_calibration
from swan_mpo.config import PUBLISHED_ONCOLOGY
from swan_mpo.verification import run_manuscript_reproduction
from swan_mpo.pipeline import standardize_adme_table


def test_colon_liability_audit_explicitly_marks_complex_i_excluded():
    adme=[{'compound':'A','MW':'400','Consensus Log P':'3','TPSA':'80','#Rotatable bonds':'4','#H-bond acceptors':'4','#H-bond donors':'1','PAINS #alerts':'0','GI absorption':'High','Synthetic Accessibility':'3'}]
    tox=[{'compound':'A','LD50 (mg/kg)':'5000','Tox Class':'6','Hepato':'Inactive (0.8)','Neuro':'Inactive (0.8)','Nephro':'Inactive (0.8)','Respi':'Inactive (0.8)','Cardio':'Inactive (0.8)','BBB':'Inactive (0.8)','NADH-QO':'Active (0.99)'}]
    _, liability=calculate_domain_audit_tables(adme,list(adme[0]),tox,list(tox[0]),PUBLISHED_ONCOLOGY,selected_panels=['Colon'])
    row=liability[0]
    assert row['complex_i_included_in_liability'] is False
    assert row['liability_inputs_used']=='BBB + neurotoxicity'


def test_published_colon_single_node_warning_is_emitted():
    warnings=collect_method_warnings(PUBLISHED_ONCOLOGY,load_published_calibration(),selected_panels=['Colon'])
    match=[w for w in warnings if w['code']=='PANEL_SINGLE_NODE_BESTNODE']
    assert len(match)==1
    assert match[0]['value']=='mTOR'


def test_missing_predictor_mode_is_marked_nonstandard():
    warnings=collect_method_warnings(PUBLISHED_ONCOLOGY,load_published_calibration(),allow_missing_predictors=True)
    assert any(w['code']=='NONSTANDARD_MODE_ACTIVATED' for w in warnings)


def test_packaged_manuscript_reproduction_matches_all_177_rows():
    report=run_manuscript_reproduction()
    assert report['status']=='PASS', report['failures'][:5]
    assert report['rows_observed']==177
    assert report['rows_expected']==177
    assert report['target_level_rows']==531
    assert report['target_level_rows_expected']==531
    mur={r['panel']:r for r in report['muricatacin']}
    assert mur['Colon']['rank']==1
    assert mur['Prostate']['rank']==2
    assert mur['RCC']['rank']==2
    assert mur['Colon']['binding_rank']==47
    assert mur['Prostate']['binding_rank']==47
    assert mur['RCC']['binding_rank']==47


def test_manuscript_packaged_resource_hashes_are_exact():
    """Guard the exact frozen reproduction bytes against accidental replacement."""
    import hashlib
    resources = files("swan_mpo.resources")
    expected = {
        "manuscript_source_manifest.json": "8e48007744de8ec50e7ba9941f4b71970161fea31034a8df231ed5502bb45561",
        "manuscript_swissadme_canonical_full.csv": "a1b6339695bba431239def8969d56244cecd978e195e5eaf2a3019ca21ec7ab1",
        "manuscript_swissadme_original_incomplete.csv": "a90b7c3cdee1d9b10257ccdf368dab6bedbe31520031113f6b1255b79deba7ca",
        "manuscript_protox_raw.csv": "4ef8ea376f89533ad3bd3afb9d810aab9c8fccc3f216179414d6de776b3f08ee",
        "manuscript_candidate_docking.csv": "6172ccc65f3ffddf07ce835ab5b5f45803f1b708f36499f5e5260971ed47530b",
        "manuscript_expected_panel_scores.csv": "cd94a21ed3bb9160220ef0d7c4897bba045c7c3eb6fd45ded717f209a073f8ca",
        "manuscript_expected_target_level_binding.csv": "8148755f8085c0d17ca5abde608ef62fd2c8621545e9f03225ef994c29f00641",
    }
    for name, digest in expected.items():
        data = (resources / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == digest, name


def test_incomplete_swissadme_export_is_rejected_not_imputed():
    """The historical blank-Consensus-LogP file must never silently enter scoring."""
    from swan_mpo.io import read_csv
    from swan_mpo.pipeline import standardize_toxicity_table, validate_predictor_values
    from swan_mpo.errors import InputValidationError
    import pytest

    resources = files("swan_mpo.resources")
    adme_rows, adme_fields = read_csv(resources / "manuscript_swissadme_original_incomplete.csv")
    tox_rows, tox_fields = read_csv(resources / "manuscript_protox_raw.csv")
    adme = standardize_adme_table(adme_rows, adme_fields, table_name="ADME")
    tox = standardize_toxicity_table(tox_rows, tox_fields, table_name="toxicity")
    with pytest.raises(InputValidationError, match="consensus_logp"):
        validate_predictor_values(adme, tox, allow_missing=False)
