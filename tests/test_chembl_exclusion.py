"""The revised ChEMBL benchmark excludes 5AR2 without rewriting history."""

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "reproducibility" / "chembl_activity_status"


def _rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_active_chembl_tables_exclude_5ar2():
    expected = {
        "primary_activity_status_records.csv": 188,
        "secondary_activity_status_records.csv": 249,
        "chembl37_external_status_cohort.csv": 249,
    }
    for filename, count in expected.items():
        rows = _rows(BENCHMARK / "inputs" / filename)
        assert len(rows) == count
        assert all(row["target_label"].upper() != "5AR2" for row in rows)


def test_original_chembl_source_remains_historical():
    provenance = json.loads((BENCHMARK / "provenance" / "original_analysis_lock.json").read_text())
    assert "5AR2" in provenance["primary_targets"]
    source = BENCHMARK / "inputs" / "chembl37_descriptor_source.csv"
    assert source.is_file()
    assert hashlib.sha256(source.read_bytes()).hexdigest() == provenance["input_sha256"]


def test_expected_outputs_exclude_5ar2():
    counts = _rows(BENCHMARK / "expected_outputs" / "group_counts_by_target.csv")
    assert all(row["target_label"].upper() != "5AR2" for row in counts)
    stratified = _rows(BENCHMARK / "expected_outputs" / "target_stratified_metrics.csv")
    assert all(row["target_label"].upper() != "5AR2" for row in stratified)
