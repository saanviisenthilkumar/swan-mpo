import json
from pathlib import Path
from swan_mpo.domain_warnings import collect_domain_warnings
from swan_mpo.provenance import input_hashes


def test_outside_anchor_warning_is_nonfatal_and_explicit():
    adme=[{'compound':'A','MW':'1200','Consensus Log P':'15','TPSA':'250','Num. rotatable bonds':'35','Num. H-bond acceptors':'20','Num. H-bond donors':'10','PAINS #alerts':'0','GI absorption':'Low','Synthetic Accessibility':'9'}]
    tox=[{'compound':'A','LD50 (mg/kg)':'20000','Toxicity class':'6','Hepatotoxicity':'Inactive (0.8)','Neurotoxicity':'Inactive (0.8)','Nephrotoxicity':'Inactive (0.8)','Respiratory toxicity':'Inactive (0.8)','Cardiotoxicity':'Inactive (0.8)','Blood-Brain Barrier':'Inactive (0.8)','Complex I':'Inactive (0.8)'}]
    warnings=collect_domain_warnings(adme,list(adme[0]),tox,list(tox[0]))
    assert any(w['field']=='mw' for w in warnings)
    assert any(w['field']=='ld50_mgkg' for w in warnings)
    assert all(w['code']=='OUTSIDE_FROZEN_ANCHOR_RANGE' for w in warnings)


def test_input_hash_metadata_does_not_persist_absolute_path(tmp_path):
    p=tmp_path/'input.csv'; p.write_text('a,b\n1,2\n')
    rows=input_hashes([p])
    assert rows[0]['name']=='input.csv'
    assert 'path' not in rows[0]
    assert len(rows[0]['sha256'])==64
