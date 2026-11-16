"""Reproduce frozen Supplementary Table S24 without modifying release inputs."""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
ABLATION = ROOT / "reproducibility/domain_ablation"


def test_frozen_ablation_reproduces_tables(tmp_path: Path):
    pytest.importorskip("pandas")
    pytest.importorskip("scipy")
    cmd = [
        sys.executable,
        str(ABLATION / "run_four_stage_ablation.py"),
        "--outdir", str(tmp_path),
        "--check-expected",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert "DOMAIN ABLATION REPRODUCTION: PASS" in result.stdout

    with (tmp_path / "sequential_rank_transition_metrics.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 9
    assert {row["panel"] for row in rows} == {"Colon", "Prostate", "RCC"}
    for panel in ("Colon", "Prostate", "RCC"):
        steps = [row for row in rows if row["panel"] == panel]
        assert [int(row["top10_replaced"]) for row in steps] == [6, 4, 3]
