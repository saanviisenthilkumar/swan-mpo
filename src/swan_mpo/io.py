from __future__ import annotations
import csv, json
from pathlib import Path
from .errors import InputValidationError

def read_csv(path):
    p=Path(path)
    if not p.is_file(): raise InputValidationError(f"CSV file not found: {p}")
    with p.open('r',encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f)
        if not r.fieldnames: raise InputValidationError(f"CSV has no header: {p}")
        return [dict(x) for x in r], list(r.fieldnames)

def write_csv(path, rows, fieldnames=None):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); rows=list(rows)
    if fieldnames is None:
        if not rows: raise InputValidationError('Cannot write an empty table without explicit fieldnames.')
        fieldnames=[]
        for r in rows:
            for k in r:
                if k not in fieldnames: fieldnames.append(k)
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fieldnames,extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    return p

def read_json(path):
    p=Path(path)
    if not p.is_file(): raise InputValidationError(f"JSON file not found: {p}")
    return json.loads(p.read_text(encoding='utf-8'))

def write_json(path, obj):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(obj,indent=2)+"\n",encoding='utf-8'); return p
