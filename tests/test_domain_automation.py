from importlib.resources import files
from swan_mpo.io import read_csv, read_json
from swan_mpo.domain_audit import calculate_domain_audit_tables
from swan_mpo.locked_model import calculate_adme, calculate_safety, calculate_liability


def test_raw_inputs_are_transformed_automatically():
    r=files('swan_mpo.resources')
    ar,af=read_csv(r/'example_adme.csv')
    tr,tf=read_csv(r/'example_toxicity.csv')
    cfg=read_json(r/'example_config.json')
    domains, liabilities=calculate_domain_audit_tables(ar,af,tr,tf,cfg,selected_panels=['Colon'])
    alpha=[x for x in domains if x['compound']=='Alpha'][0]
    expected_adme=calculate_adme(mw=450,consensus_logp=3.2,tpsa=110,rotatable_bonds=6,hba=6,hbd=2,pains_alerts=0,gi_absorption='High',synthetic_accessibility=3.0)
    expected_safety=calculate_safety(ld50_mgkg=1500,toxicity_class=5,hepato='Inactive (0.80)',neuro='Inactive (0.75)',nephro='Inactive (0.70)',respi='Inactive (0.80)',cardio='Inactive (0.85)')
    expected_liability=calculate_liability(panel='Colon',bbb='Inactive (0.70)',complex_i='Inactive (0.75)',neuro='Inactive (0.75)')
    assert abs(alpha['adme_score']-expected_adme['adme_score'])<1e-15
    assert abs(alpha['safety_score']-expected_safety['safety_score'])<1e-15
    li=[x for x in liabilities if x['compound']=='Alpha' and x['panel']=='Colon'][0]
    assert abs(li['liability_score']-expected_liability['liability_score'])<1e-15
    assert 'd_ld50' in alpha and 'd_mw' in alpha and 'd_bbb' in li
