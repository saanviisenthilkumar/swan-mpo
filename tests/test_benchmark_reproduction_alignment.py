"""Regression checks for the frozen ChEMBL and MPO comparator inputs."""

import csv
import hashlib
import importlib.util
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CHEMBL = ROOT / "reproducibility/chembl_activity_status"
COMPARATOR = ROOT / "reproducibility/mpo_comparator"


def test_corrected_comparator_cohort_and_checksum():
    path = COMPARATOR / "inputs/comparator_compound_scores.csv"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == (
        "71fd4a0b39e0e7f4ad4aadf7cd1e4328203bd853434ef94f520e9cc79923a974"
    )
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 3980
    assert sum(int(row["label"]) for row in rows) == 995


def test_s13_tie_bedroc_matches_or2_and_is_order_independent():
    helper_path = CHEMBL / "scripts/tie_averaged_bedroc.py"
    spec = importlib.util.spec_from_file_location("or2_tie_bedroc", helper_path)
    helper = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(helper)

    with (CHEMBL / "inputs/primary_activity_status_records.csv").open(
        newline="", encoding="utf-8-sig"
    ) as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 188
    assert "structure_derived_liability" in rows[0]
    y = np.asarray([int(row["benchmark_y"]) for row in rows])
    for field, published in (
        ("binding_only", 0.63626928093309687),
        ("adme_only", 0.24332733558361647),
    ):
        scores = np.asarray([float(row[field]) for row in rows])
        expected = helper.tie_averaged_bedroc(y, scores)
        assert abs(expected - published) < 5e-12
        reverse = np.arange(len(y))[::-1]
        assert abs(helper.tie_averaged_bedroc(y[reverse], scores[reverse]) - expected) < 1e-12
