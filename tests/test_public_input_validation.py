import pytest
from swan_mpo.pipeline import standardize_toxicity_table, validate_predictor_values


def tox_row():
    return {
        'Compound':'A', 'LD50 (mg/kg)':'1000', 'Toxicity class':'4',
        'Hepatotoxicity':'Inactive', 'Hepatotoxicity confidence':'0.81',
        'Neurotoxicity':'Inactive', 'Neurotoxicity confidence':'0.82',
        'Nephrotoxicity':'Inactive', 'Nephrotoxicity confidence':'0.83',
        'Respiratory toxicity':'Inactive', 'Respiratory toxicity confidence':'0.84',
        'Cardiotoxicity':'Inactive', 'Cardiotoxicity confidence':'0.85',
        'BBB':'Inactive', 'BBB confidence':'0.86',
        'Complex I':'Inactive', 'Complex I confidence':'0.87',
    }


def test_separate_protox_confidence_columns_are_combined():
    row=tox_row()
    std=standardize_toxicity_table([row], list(row))[0]
    assert std['neuro'] == 'Inactive (0.82)'
    assert std['complex_i'] == 'Inactive (0.87)'
    adme=[{'compound':'A','mw':'350','consensus_logp':'3','tpsa':'80','rotatable_bonds':'5','hba':'4','hbd':'2','pains_alerts':'0','gi_absorption':'High','synthetic_accessibility':'3'}]
    assert validate_predictor_values(adme,[std])


def test_missing_endpoint_confidence_fails_loudly():
    row=tox_row()
    row.pop('Neurotoxicity confidence')
    std=standardize_toxicity_table([row], list(row))[0]
    adme=[{'compound':'A','mw':'350','consensus_logp':'3','tpsa':'80','rotatable_bonds':'5','hba':'4','hbd':'2','pains_alerts':'0','gi_absorption':'High','synthetic_accessibility':'3'}]
    with pytest.raises(Exception, match='no prediction confidence'):
        validate_predictor_values(adme,[std])


def test_conflicting_embedded_and_companion_confidence_fails():
    row=tox_row()
    row['Neurotoxicity']='Inactive (0.75)'
    with pytest.raises(Exception, match='unambiguous confidence'):
        standardize_toxicity_table([row], list(row))
