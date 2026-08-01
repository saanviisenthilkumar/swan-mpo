from swan_mpo.calibration import calibrate_from_redocking, load_published_calibration
def test_strict_and_recovery():
 rows=[{'target':'A','pdb_id':'1AAA','mode':'1','dg':'-8','rmsd':'1.2'},{'target':'A','pdb_id':'1AAA','mode':'2','dg':'-7','rmsd':'0.8'},{'target':'B','pdb_id':'2BBB','mode':'1','dg':'-9','rmsd':'3.0'},{'target':'B','pdb_id':'2BBB','mode':'2','dg':'-8.5','rmsd':'1.4'}]
 out=calibrate_from_redocking(rows,list(rows[0]))
 assert out[0]['reference_mode']==1 and out[0]['validation_class']=='strict_top_pose'
 assert out[1]['reference_mode']==2 and out[1]['validation_class']=='generated_mode_recovery'
def test_failed_redocking_becomes_comparative():
 rows=[{'target':'A','pdb_id':'1AAA','mode':'1','dg':'-8','rmsd':'3.0'}]; out=calibrate_from_redocking(rows,list(rows[0])); assert out[0]['calibration_status']=='comparative_target_relative_only' and out[0]['reference_dg']==''
def test_published_classes():
 d={x['target']:x for x in load_published_calibration()}; assert d['Bcl-2']['calibration_status']=='reference_calibrated'; assert d['mTOR']['calibration_status']=='reference_calibrated'; assert d['EGFR']['calibration_status']=='comparative_target_relative_only'
