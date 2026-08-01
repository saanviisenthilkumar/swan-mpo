import csv, json, io
from importlib.resources import files
from swan_mpo.io import read_csv, read_json
from swan_mpo.calibration import calibrate_from_redocking
from swan_mpo.pipeline import score_pipeline, aggregate_candidate_docking, build_target_binding, bestnode_by_panel

def _inputs():
 r=files('swan_mpo.resources'); ar,af=read_csv(r/'example_adme.csv'); tr,tf=read_csv(r/'example_toxicity.csv'); dr,df=read_csv(r/'example_candidate_docking.csv'); rr,rf=read_csv(r/'example_reference_redocking.csv'); cfg=read_json(r/'example_config.json'); cal=calibrate_from_redocking(rr,rf); return ar,af,tr,tf,dr,df,cfg,cal
def test_grid_median_and_bestnode():
 ar,af,tr,tf,dr,df,cfg,cal=_inputs(); scores,target=score_pipeline(ar,af,tr,tf,dr,df,cal,cfg,selected_panels=['Colon']); a=[x for x in scores if x['compound']=='Alpha'][0]; b=[x for x in scores if x['compound']=='Beta'][0]; assert a['selected_best_node']=='T2'; assert b['selected_best_node']=='T1'; assert len(target)==4
def test_scores_finite_and_ranked():
 ar,af,tr,tf,dr,df,cfg,cal=_inputs(); scores,_=score_pipeline(ar,af,tr,tf,dr,df,cal,cfg,selected_panels=['Colon']); assert all(0.01<=x['SWAN_MPO_score']<=1 for x in scores); assert sorted(x['SWAN_MPO_rank'] for x in scores)==[1,2]
def test_exact_20_grid_requirement():
 ar,af,tr,tf,dr,df,cfg,cal=_inputs(); dr=dr[:-1]
 import pytest
 with pytest.raises(Exception): score_pipeline(ar,af,tr,tf,dr,df,cal,cfg,selected_panels=['Colon'])
