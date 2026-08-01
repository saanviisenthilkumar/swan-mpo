from swan_mpo.columns import resolve_columns, ADME_ALIASES, TOX_ALIASES
def test_swissadme_aliases():
 fields=['compound','MW','Consensus Log P','TPSA','Num. rotatable bonds','Num. H-bond acceptors','Num. H-bond donors','PAINS #alerts','GI absorption','Synthetic Accessibility']; m=resolve_columns(fields,ADME_ALIASES); assert m['consensus_logp']=='Consensus Log P' and m['synthetic_accessibility']=='Synthetic Accessibility'
def test_protox_aliases():
 fields=['compound','LD50 (mg/kg)','Toxicity class','Hepatotoxicity','Neurotoxicity','Nephrotoxicity','Respiratory toxicity','Cardiotoxicity','Blood-Brain Barrier','Complex I']; m=resolve_columns(fields,TOX_ALIASES); assert m['ld50_mgkg']=='LD50 (mg/kg)' and m['complex_i']=='Complex I'
