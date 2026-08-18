import pytest
from swan_mpo.pipeline import aggregate_candidate_docking, standardize_compound_table
from swan_mpo.columns import ADME_ALIASES
from swan_mpo.calibration import calibrate_from_redocking

def test_duplicate_grid_rejected():
    rows=[{'compound':'A','target':'T','pdb_id':'P','grid_id':'1','dg':'-7'}, {'compound':'A','target':'T','pdb_id':'P','grid_id':'1','dg':'-8'}]
    with pytest.raises(Exception, match='Duplicate grid_id'): aggregate_candidate_docking(rows,list(rows[0]),expected_grids=None,require_exact_grids=False)

def test_nonnegative_individual_grid_energies_are_allowed():
    # Canonical docking ledgers may contain weak/positive individual grid scores.
    # SWAN validates the compound-target median at the reference-calibration stage.
    rows=[{'compound':'A','target':'T','pdb_id':'P','grid_id':str(i),'dg':('1' if i == 0 else '-7')} for i in range(20)]
    result=aggregate_candidate_docking(rows,list(rows[0]),expected_grids=20,require_exact_grids=True)
    assert result[0]['n_nonnegative_grid_energies'] == 1
    assert result[0]['median_dg'] < 0

def test_nonnegative_calibrated_median_is_rejected():
    from swan_mpo.pipeline import build_target_binding
    dock=[{'compound':'A','compound_key':'a','target':'T','pdb_id':'P','n_grid_centers':20,'best_dg':0.1,'median_dg':1.0,'mean_dg':1.0}]
    cal=[{'target':'T','pdb_id':'P','calibration_status':'reference_calibrated','validation_class':'strict_top_pose','reference_dg':-8}]
    with pytest.raises(Exception, match='negative median energy'):
        build_target_binding(dock,cal)

def test_duplicate_compound_properties_rejected():
    rows=[{'compound':'A','MW':'1','Consensus Log P':'1','TPSA':'1','Num. rotatable bonds':'1','Num. H-bond acceptors':'1','Num. H-bond donors':'1','PAINS #alerts':'0','GI absorption':'High','Synthetic Accessibility':'1'}]*2
    with pytest.raises(Exception, match='duplicate compound'): standardize_compound_table(rows,list(rows[0]),ADME_ALIASES,None,'ADME')

def test_bad_redocking_mode_rejected():
    rows=[{'target':'A','pdb_id':'P','mode':'0','dg':'-8','rmsd':'1'}]
    with pytest.raises(Exception): calibrate_from_redocking(rows,list(rows[0]))

def test_candidate_pdb_must_match_calibration():
    from swan_mpo.pipeline import build_target_binding
    dock=[{'compound':'A','compound_key':'a','target':'T','pdb_id':'WRONG','n_grid_centers':20,'best_dg':-8,'median_dg':-7.5,'mean_dg':-7.5}]
    cal=[{'target':'T','pdb_id':'RIGHT','calibration_status':'reference_calibrated','reference_dg':-8}]
    with pytest.raises(Exception, match='does not match calibration PDB'): build_target_binding(dock,cal)

def test_missing_target_calibration_rejected():
    from swan_mpo.pipeline import bestnode_by_panel
    binding=[{'compound':'A','compound_key':'a','target':'T1','pdb_id':'P1','binding_reference_calibrated':0.5}]
    config={'panels':{'Colon':['T1','T2']},'bestnode_tie_priority':{'Colon':['T1','T2']}}
    cal=[{'target':'T1','pdb_id':'P1','calibration_status':'reference_calibrated','reference_dg':-8}]
    with pytest.raises(Exception, match='lack a redocking/calibration record'): bestnode_by_panel(binding,config,cal,['Colon'],False)

def test_missing_raw_predictor_rejected_by_default():
    from swan_mpo.pipeline import validate_predictor_values
    a=[{'compound':'A','mw':'','consensus_logp':'1','tpsa':'1','rotatable_bonds':'1','hba':'1','hbd':'1','pains_alerts':'0','gi_absorption':'High','synthetic_accessibility':'1'}]
    t=[{'compound':'A','ld50_mgkg':'100','toxicity_class':'3','hepato':'Inactive','neuro':'Inactive','nephro':'Inactive','respi':'Inactive','cardio':'Inactive','bbb':'Inactive','complex_i':'Inactive'}]
    with pytest.raises(Exception, match='is missing'): validate_predictor_values(a,t)

def test_missing_raw_predictor_can_be_explicitly_allowed():
    from swan_mpo.pipeline import validate_predictor_values
    a=[{'compound':'A','mw':'','consensus_logp':'1','tpsa':'1','rotatable_bonds':'1','hba':'1','hbd':'1','pains_alerts':'0','gi_absorption':'High','synthetic_accessibility':'1'}]
    t=[{'compound':'A','ld50_mgkg':'100','toxicity_class':'3','hepato':'Inactive','neuro':'Inactive','nephro':'Inactive','respi':'Inactive','cardio':'Inactive','bbb':'Inactive','complex_i':'Inactive'}]
    assert validate_predictor_values(a,t,allow_missing=True)
