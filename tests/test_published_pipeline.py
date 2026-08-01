from swan_mpo.calibration import load_published_calibration
from swan_mpo.config import load_config
from swan_mpo.pipeline import score_pipeline

def test_full_published_pipeline_has_expected_calibrated_counts_and_excludes_comparative():
    targets={'ComplexI':'5LNK','EGFR':'1IVO','mTOR':'4JSP','5AR2':'3V3N','AR':'2AMA','Bcl-2':'4LVT','AKT1':'3MVH','Caspase3':'1QX3','PI3Ka':'6OAC'}
    docking=[]
    for t,pdb in targets.items():
        # Make comparative-only targets absurdly favorable; they still cannot enter primary BestNode.
        base=-20 if t in {'ComplexI','EGFR','Caspase3'} else -7
        for i in range(20): docking.append({'compound':'X','target':t,'pdb_id':pdb,'grid_id':str(i+1),'dg':str(base+i*.001)})
    adme=[{'compound':'X','mw':'450','consensus_logp':'3','tpsa':'90','rotatable_bonds':'5','hba':'5','hbd':'2','pains_alerts':'0','gi_absorption':'High','synthetic_accessibility':'3'}]
    tox=[{'compound':'X','ld50_mgkg':'1000','toxicity_class':'4','hepato':'Inactive 0.8','neuro':'Inactive 0.8','nephro':'Inactive 0.8','respi':'Inactive 0.8','cardio':'Inactive 0.8','bbb':'Inactive 0.8','complex_i':'Inactive 0.8'}]
    cfg=load_config('published-oncology'); cal=load_published_calibration()
    scores,target=score_pipeline(adme,list(adme[0]),tox,list(tox[0]),docking,list(docking[0]),cal,cfg)
    assert len(scores)==3
    by={x['panel']:x for x in scores}
    assert by['Colon']['n_calibrated_panel_targets']==1 and by['Colon']['selected_best_node']=='mTOR'
    assert by['Prostate']['n_calibrated_panel_targets']==4 and by['Prostate']['selected_best_node'] in {'5AR2','AR','Bcl-2','mTOR'}
    assert by['RCC']['n_calibrated_panel_targets']==4 and by['RCC']['selected_best_node'] in {'AKT1','Bcl-2','PI3Ka','mTOR'}
    assert all(x['selected_best_node'] not in {'ComplexI','EGFR','Caspase3'} for x in scores)
