#!/usr/bin/env python3
"""Reproduce the model-frozen 177-row SWAN-MPO domain-ranking ablation.

This evaluates internal ranking sensitivity, NOT independent biological validation.
It does not retrain scores, revise inputs, or change the locked model.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE = HERE.parents[1] / "src/swan_mpo/resources/manuscript_expected_panel_scores.csv"
DEFAULT_OUT = HERE / "reproduced_outputs"
EXPECTED_OUT = HERE / "expected_outputs"
FLOOR = 0.01
DOMAINS = ["bestnode_binding", "adme_score", "safety_score", "liability_score"]
STAGES = {
    "1_binding_only": DOMAINS[:1],
    "2_binding_adme": DOMAINS[:2],
    "3_binding_adme_safety": DOMAINS[:3],
    "4_full_swan_mpo": DOMAINS[:4],
}


def geometric(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    values = df[cols].astype(float)
    if values.isna().any().any():
        raise ValueError(f"Missing model domain in {cols}")
    return pd.Series(
        np.exp(np.log(values.clip(lower=FLOOR, upper=1.0)).mean(axis=1)),
        index=df.index,
    )


def compare(g: pd.DataFrame, left: str, right: str) -> dict:
    rank_left = g["rank__" + left]
    rank_right = g["rank__" + right]
    top_left = set(g.nsmallest(10, "rank__" + left).Compound)
    top_right = set(g.nsmallest(10, "rank__" + right).Compound)
    return {
        "earlier": left,
        "later": right,
        "top10_overlap": len(top_left & top_right),
        "top10_replaced": len(top_left - top_right),
        "mean_absolute_rank_change": float((rank_left - rank_right).abs().mean()),
        "max_absolute_rank_change": int((rank_left - rank_right).abs().max()),
        "spearman_rho": float(spearmanr(rank_left, rank_right).statistic),
        "new_top10_compounds": sorted(top_right - top_left),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_SOURCE,
                        help="Canonical manuscript expected-panel score CSV or supplementary Table S8B CSV")
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUT,
                        help="Directory for generated ablation tables and summary")
    parser.add_argument("--check-expected", action="store_true",
                        help="Compare all three regenerated supplementary tables against frozen expectations")
    args = parser.parse_args()
    output = args.outdir
    output.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(args.input)
    assert len(d) == 177
    assert set(d.panel) == {"Colon", "Prostate", "RCC"}
    assert d.groupby("panel").Compound.nunique().to_dict() == {
        "Colon": 59, "Prostate": 59, "RCC": 59
    }
    assert d.duplicated(["panel", "Compound"]).sum() == 0

    for name, columns in STAGES.items():
        d[name] = geometric(d, columns)
        d["rank__" + name] = (
            d.groupby("panel")[name].rank(method="min", ascending=False).astype(int)
        )
    err = (d["4_full_swan_mpo"] - d["SWAN_BestNode"]).abs().max()
    if err > 1e-12 or not (d["rank__4_full_swan_mpo"] == d["rank_SWAN_BestNode"]).all():
        raise AssertionError(f"Full reconstruction/rank mismatch: max error {err}")
    summary = {
        "n_compounds": 59,
        "n_panels": 3,
        "n_panel_rows": 177,
        "max_absolute_reconstruction_error": float(err),
        "reproduced_all_published_full_ranks": True,
        "stages": STAGES,
        "panels": {},
        "model_limitations": [
            "Ablation quantifies rank sensitivity, not experimental correctness.",
            "Every single BestNode in all three panels is mTOR: binding scores are panel-invariant.",
            "ADME and general safety are also panel-invariant.",
            "Prostate and RCC use identical liability formulas, so their final scores and ranks are identical.",
            "Panel-specific liability shares the neurotoxicity input with general safety.",
            "All inputs and rankings are based on computational predictions, not independent outcomes.",
        ],
    }
    stage_names = list(STAGES)
    transitions = []
    leave_one_out = []
    panel_rows = []
    for panel, g in d.groupby("panel", sort=False):
        panel_data = {
            "selected_best_node": g.selected_best_node.value_counts().to_dict(),
            "top5_by_stage": {
                st: g.nsmallest(5, "rank__" + st).Compound.tolist()
                for st in stage_names
            },
        }
        for a, b in zip(stage_names[:-1], stage_names[1:]):
            comp = compare(g, a, b)
            transitions.append({"panel": panel, **comp})
        panel_data["binding_vs_full"] = compare(g, stage_names[0], stage_names[-1])
        panel_data["muricatacin_ranks"] = {
            st: int(g.loc[g.Compound == "Muricatacin", "rank__" + st].iloc[0])
            for st in stage_names
        }
        summary["panels"][panel] = panel_data

        for missing in DOMAINS:
            label = "full_without_" + missing
            g = g.copy()
            g[label] = geometric(g, [x for x in DOMAINS if x != missing])
            g["rank__" + label] = g[label].rank(method="min", ascending=False).astype(int)
            cmp = compare(g, label, stage_names[-1])
            leave_one_out.append({"panel": panel, "ablated_domain": missing, **cmp})
        panel_rows.extend(
            g[
                ["panel", "Compound", "selected_best_node", *DOMAINS]
                + stage_names + ["rank__" + x for x in stage_names]
            ].to_dict("records")
        )

    full_pivot = d.pivot(index="Compound", columns="panel", values="4_full_swan_mpo")
    summary["prostate_rcc_identical_full_scores"] = bool(
        np.allclose(full_pivot.Prostate, full_pivot.RCC, atol=1e-12, rtol=0)
    )
    binding_pivot = d.pivot(index="Compound", columns="panel", values="bestnode_binding")
    summary["all_three_panels_identical_bestnode_binding"] = bool(
        np.allclose(binding_pivot.Colon, binding_pivot.Prostate, atol=1e-12, rtol=0)
        and np.allclose(binding_pivot.Prostate, binding_pivot.RCC, atol=1e-12, rtol=0)
    )
    pd.DataFrame(panel_rows).to_csv(output / "all_177_four_stage_scores_and_ranks.csv", index=False)
    pd.DataFrame(transitions).to_csv(output / "sequential_rank_transition_metrics.csv", index=False)
    pd.DataFrame(leave_one_out).to_csv(output / "leave_one_domain_out_metrics.csv", index=False)
    with (output / "four_stage_ablation_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    if args.check_expected:
        expected_files = (
            "all_177_four_stage_scores_and_ranks.csv",
            "sequential_rank_transition_metrics.csv",
            "leave_one_domain_out_metrics.csv",
        )
        for name in expected_files:
            actual = pd.read_csv(output / name)
            expected = pd.read_csv(EXPECTED_OUT / name)
            pd.testing.assert_frame_equal(actual, expected, check_exact=False, atol=1e-12,
                                          rtol=0, check_dtype=False)
        print("DOMAIN ABLATION REPRODUCTION: PASS")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
