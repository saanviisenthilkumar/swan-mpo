from __future__ import annotations
import math
from importlib.resources import files
from .columns import REDOCK_ALIASES, resolve_columns
from .config import normalize_target
from .errors import InputValidationError
from .locked_model import as_float
from .io import read_csv

def calibrate_from_redocking(rows, fields, column_map=None, rmsd_cutoff=2.0):
    m=resolve_columns(fields,REDOCK_ALIASES,column_map,table='reference redocking')
    groups={}
    for i,r in enumerate(rows,start=2):
        t=normalize_target(r[m['target']]); pdb=str(r[m['pdb_id']]).strip().upper(); mode=as_float(r[m['mode']]); dg=as_float(r[m['dg']]); rmsd=as_float(r[m['rmsd']])
        if not t or not pdb or not math.isfinite(mode) or int(mode)!=mode or mode<1: raise InputValidationError(f"Reference redocking row {i}: target, PDB, and positive integer mode are required.")
        if not math.isfinite(dg) or dg>=0: raise InputValidationError(f"Reference redocking row {i}: docking energy must be finite and negative.")
        if not math.isfinite(rmsd) or rmsd<0: raise InputValidationError(f"Reference redocking row {i}: RMSD must be finite and non-negative.")
        groups.setdefault((t,pdb),[]).append({'mode':int(mode),'dg':float(dg),'rmsd':float(rmsd)})
    out=[]
    for (t,pdb), vals in sorted(groups.items()):
        vals=sorted(vals,key=lambda x:x['mode']); top=vals[0]
        if top['rmsd']<=rmsd_cutoff:
            selected=top; cls='strict_top_pose'; status='reference_calibrated'
        else:
            selected=min(vals,key=lambda x:(x['rmsd'],x['mode']))
            if selected['rmsd']<=rmsd_cutoff: cls='generated_mode_recovery'; status='reference_calibrated'
            else: cls='comparative_only'; status='comparative_target_relative_only'; selected=None
        out.append({
          'target':t,'pdb_id':pdb,'calibration_status':status,'validation_class':cls,
          'reference_mode':selected['mode'] if selected else '', 'reference_dg':selected['dg'] if selected else '',
          'reference_rmsd_A':selected['rmsd'] if selected else '', 'rmsd_cutoff_A':rmsd_cutoff,
          'n_generated_modes':len(vals)})
    return out

def load_published_calibration():
    path=files('swan_mpo.resources')/'published_target_redocking_calibration.csv'
    rows,fields=read_csv(path)
    out=[]
    for r in rows:
        ref=as_float(r.get('reference_dg_for_binding_calibration'))
        status='reference_calibrated' if math.isfinite(ref) else 'comparative_target_relative_only'
        source_class=r.get('validation_class_fixed','')
        source_lower=str(source_class).lower()
        if 'strict top-pose' in source_lower:
            validation_class='strict_top_pose'
        elif 'generated-mode' in source_lower:
            validation_class='generated_mode_recovery'
        else:
            validation_class='comparative_only'
        out.append({
          'target':normalize_target(r['target']), 'pdb_id':str(r['pdb_id']).upper(), 'calibration_status':status,
          'validation_class':validation_class, 'validation_class_source':source_class,
          'reference_mode':r.get('reference_mode_for_binding_calibration',''),
          'reference_dg':ref if math.isfinite(ref) else '', 'reference_rmsd_A':r.get('reference_rmsd_for_binding_calibration',''),
          'reference_energy_source':r.get('reference_energy_source',''), 'manuscript_interpretation':r.get('manuscript_interpretation','')})
    return out

def calibration_index(rows):
    idx={}
    for r in rows:
        t=normalize_target(r['target'])
        if t in idx:
            raise InputValidationError(f"Calibration contains more than one row for target {t!r}; use one receptor/calibration record per target in a scoring run.")
        idx[t]=r
    return idx
