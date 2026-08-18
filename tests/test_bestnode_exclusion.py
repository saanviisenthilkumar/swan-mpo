from swan_mpo.calibration import load_published_calibration
from swan_mpo.config import load_config
from swan_mpo.pipeline import aggregate_candidate_docking, build_target_binding, bestnode_by_panel

def make_rows(target_energy):
    rows=[]
    pdb={'ComplexI':'5LNK','EGFR':'1IVO','mTOR':'4JSP'}
    for t,e in target_energy.items():
        for i in range(20): rows.append({'compound':'X','target':t,'pdb_id':pdb[t],'grid_id':str(i+1),'dg':str(e+i*0.001)})
    return rows

def test_comparative_targets_cannot_win_primary_bestnode():
    rows=make_rows({'ComplexI':-20.0,'EGFR':-20.0,'mTOR':-5.0})
    ds=aggregate_candidate_docking(rows,list(rows[0]),expected_grids=20)
    cal=load_published_calibration(); tb=build_target_binding(ds,cal)
    out=bestnode_by_panel(tb,load_config('published-oncology'),cal,['Colon'],True)
    assert out[0]['selected_best_node']=='mTOR'
    assert out[0]['n_calibrated_panel_targets']==1
