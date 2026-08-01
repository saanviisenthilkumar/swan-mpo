from __future__ import annotations
import json, re
from importlib.resources import files
from pathlib import Path
from .errors import InputValidationError
from .io import read_json

PUBLISHED_ONCOLOGY = {
  "name":"published-oncology",
  "expected_grid_centers":20,
  "candidate_docking_seed":2026,
  "reference_redocking_seed":2026,
  "panels": {
    "Colon":["ComplexI","EGFR","mTOR"],
    "Prostate":["5AR2","AR","Bcl-2","EGFR","mTOR"],
    "RCC":["AKT1","Bcl-2","Caspase3","PI3Ka","mTOR"]
  },
  "pdb_ids": {"mTOR":"4JSP","5AR2":"3V3N","AR":"2AMA","Bcl-2":"4LVT","PI3Ka":"6OAC","AKT1":"3MVH","Caspase3":"1QX3","EGFR":"1IVO","ComplexI":"5LNK"},
  "bestnode_tie_priority": {
    "Colon":["mTOR"],
    "Prostate":["AR","5AR2","mTOR","Bcl-2"],
    "RCC":["AKT1","mTOR","Bcl-2","PI3Ka"]
  }
}

def normalize_key(v): return re.sub(r'[^a-z0-9]+','',str(v).lower())

def normalize_target(v):
    k=normalize_key(str(v).replace('α','alpha'))
    aliases={
      '4jsp':'mTOR','mtor':'mTOR','3v3n':'5AR2','5ar2':'5AR2','srd5a2':'5AR2','5alphareductase2':'5AR2',
      '2ama':'AR','ar':'AR','androgenreceptor':'AR','4lvt':'Bcl-2','bcl2':'Bcl-2',
      '6oac':'PI3Ka','pi3ka':'PI3Ka','pi3k':'PI3Ka','pi3kalpha':'PI3Ka',
      '3mvh':'AKT1','akt1':'AKT1','1qx3':'Caspase3','caspase3':'Caspase3',
      '1ivo':'EGFR','egfr':'EGFR','5lnk':'ComplexI','complexi':'ComplexI','complex1':'ComplexI'}
    return aliases.get(k, str(v).strip())

def normalize_panel(v):
    k=normalize_key(v); aliases={'colon':'Colon','colorectal':'Colon','crc':'Colon','prostate':'Prostate','rcc':'RCC','renalcellcarcinoma':'RCC','kidney':'RCC'}
    return aliases.get(k,str(v).strip())

def load_config(value):
    if value in {None,'published-oncology','published'}: return json.loads(json.dumps(PUBLISHED_ONCOLOGY))
    cfg=read_json(value)
    if not isinstance(cfg,dict) or not isinstance(cfg.get('panels'),dict): raise InputValidationError('Config must contain a panels mapping.')
    cfg.setdefault('expected_grid_centers',20); cfg.setdefault('pdb_ids',{}); cfg.setdefault('bestnode_tie_priority',cfg['panels'])
    return cfg
