from __future__ import annotations
from collections import defaultdict
from .columns import ADME_ALIASES, TOX_ALIASES
from .pipeline import standardize_compound_table, standardize_toxicity_table, validate_predictor_values
from .locked_model import calculate_adme, calculate_safety, calculate_liability
from .errors import InputValidationError


def calculate_domain_audit_tables(adme_rows, adme_fields, tox_rows, tox_fields, config, *, adme_map=None, tox_map=None, selected_panels=None, allow_missing=False):
    adme=standardize_compound_table(adme_rows,adme_fields,ADME_ALIASES,adme_map,'ADME')
    tox=standardize_toxicity_table(tox_rows,tox_fields,tox_map,'toxicity')
    validate_predictor_values(adme,tox,allow_missing=allow_missing)
    aidx={r['compound_key']:r for r in adme}; tidx={r['compound_key']:r for r in tox}
    if set(aidx)!=set(tidx):
        only_a=sorted(set(aidx)-set(tidx)); only_t=sorted(set(tidx)-set(aidx))
        raise InputValidationError(f"ADME/toxicity compound mismatch. ADME-only keys={only_a[:10]}, toxicity-only keys={only_t[:10]}")
    compound=[]
    for ck in sorted(aidx):
        a=aidx[ck]; t=tidx[ck]
        ad=calculate_adme(mw=a['mw'],consensus_logp=a['consensus_logp'],tpsa=a['tpsa'],rotatable_bonds=a['rotatable_bonds'],hba=a['hba'],hbd=a['hbd'],pains_alerts=a['pains_alerts'],gi_absorption=a['gi_absorption'],synthetic_accessibility=a['synthetic_accessibility'])
        sa=calculate_safety(ld50_mgkg=t['ld50_mgkg'],toxicity_class=t['toxicity_class'],hepato=t['hepato'],neuro=t['neuro'],nephro=t['nephro'],respi=t['respi'],cardio=t['cardio'])
        compound.append({'compound':a['compound'],'compound_key':ck,
          'raw_mw':a['mw'],'raw_consensus_logp':a['consensus_logp'],'raw_tpsa':a['tpsa'],'raw_rotatable_bonds':a['rotatable_bonds'],
          'raw_hba':a['hba'],'raw_hbd':a['hbd'],'raw_pains_alerts':a['pains_alerts'],'raw_gi_absorption':a['gi_absorption'],'raw_synthetic_accessibility':a['synthetic_accessibility'],
          'raw_ld50_mgkg':t['ld50_mgkg'],'raw_toxicity_class':t['toxicity_class'],'raw_hepato':t['hepato'],'raw_neuro':t['neuro'],'raw_nephro':t['nephro'],'raw_respi':t['respi'],'raw_cardio':t['cardio'],
          **sa,**ad})
    panels=selected_panels or list(config['panels'])
    liability=[]
    for ck in sorted(tidx):
        t=tidx[ck]
        for panel in panels:
            li=calculate_liability(panel=panel,bbb=t['bbb'],complex_i=t['complex_i'],neuro=t['neuro'])
            liability.append({'compound':t['compound'],'compound_key':ck,'panel':panel,'raw_bbb':t['bbb'],'raw_complex_i':t['complex_i'],'raw_neuro':t['neuro'],**li})
    return compound,liability
