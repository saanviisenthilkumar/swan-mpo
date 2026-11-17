#!/usr/bin/env python3
"""
Offline reproduction of the SWAN-MPO ChEMBL activity/status domain decomposition.

This secondary mechanism decomposition was performed after inspection of the
primary A-vs-(B+C) benchmark. It does not replace the primary benchmark and
does not change score definitions, labels, activity thresholds, or external
status definitions.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score
from tie_averaged_bedroc import tie_averaged_bedroc


RANDOM_SEED = 2026
BOOTSTRAP_REPS = 5000
BEDROC_ALPHA = 20.0

A = "A_active_approved_no_serious_warning"
B = "B_active_serious_warning"
C = "C_inactive_approved_no_serious_warning"

SCORE_COLUMNS = [
    "binding_only",
    "adme_only",
    "structure_derived_liability",
    "binding_adme_gm",
    "binding_liability_gm",
    "adme_liability_gm",
    "integrated_gm3",
    "integrated_arithmetic3",
    "integrated_min3",
    "qed",
]
SCORE_PUBLIC_NAMES = {"structure_derived_liability": "liability_only"}


def public_score_name(name: str) -> str:
    return SCORE_PUBLIC_NAMES.get(name, name)


def tie_aware_ef(y: np.ndarray, scores: np.ndarray, frac: float) -> float:
    y = np.asarray(y, dtype=int)
    scores = np.asarray(scores, dtype=float)
    ok = np.isfinite(scores)
    y, scores = y[ok], scores[ok]
    n = len(y)
    if n == 0 or y.sum() == 0:
        return np.nan
    k = max(1, int(math.ceil(frac * n)))
    order = np.argsort(-scores, kind="mergesort")
    ys, ss = y[order], scores[order]
    cutoff = ss[k - 1]
    above = ss > cutoff
    tied = ss == cutoff
    n_above = int(above.sum())
    slots = k - n_above
    act_above = float(ys[above].sum())
    act_tied_expected = (
        slots * float(ys[tied].mean()) if slots > 0 and tied.sum() else 0.0
    )
    top_active_expected = act_above + act_tied_expected
    top_rate = top_active_expected / k
    global_rate = float(y.mean())
    return top_rate / global_rate if global_rate > 0 else np.nan


def bedroc(y: np.ndarray, scores: np.ndarray, alpha: float = BEDROC_ALPHA) -> float:
    return tie_averaged_bedroc(y, scores, alpha)


def metrics(df: pd.DataFrame, score: str, y_col: str = "benchmark_y") -> dict:
    d = df[[y_col, score]].dropna()
    y = d[y_col].astype(int).to_numpy()
    s = d[score].astype(float).to_numpy()
    two_class = len(np.unique(y)) == 2
    return {
        "score": public_score_name(score),
        "n_rows": len(d),
        "n_positive_rows": int(y.sum()),
        "n_negative_rows": int((1 - y).sum()),
        "roc_auc": roc_auc_score(y, s) if two_class else np.nan,
        "pr_auc": average_precision_score(y, s) if two_class else np.nan,
        "bedroc_alpha20": bedroc(y, s) if two_class else np.nan,
        "ef_1pct": tie_aware_ef(y, s, 0.01),
        "ef_5pct": tie_aware_ef(y, s, 0.05),
    }


def weighted_metrics_balanced_negatives(df: pd.DataFrame, score: str) -> dict:
    d = df[["benchmark_group", "benchmark_y", score]].dropna().copy()
    n_a = int((d["benchmark_group"] == A).sum())
    n_b = int((d["benchmark_group"] == B).sum())
    n_c = int((d["benchmark_group"] == C).sum())
    if min(n_a, n_b, n_c) == 0:
        return {
            "score": score,
            "n_rows": len(d),
            "n_A_rows": n_a,
            "n_B_rows": n_b,
            "n_C_rows": n_c,
            "weighted_roc_auc": np.nan,
            "weighted_pr_auc": np.nan,
        }

    w = np.zeros(len(d), dtype=float)
    ga = d["benchmark_group"].to_numpy() == A
    gb = d["benchmark_group"].to_numpy() == B
    gc = d["benchmark_group"].to_numpy() == C
    w[ga] = 1.0 / n_a
    w[gb] = 0.5 / n_b
    w[gc] = 0.5 / n_c

    y = d["benchmark_y"].astype(int).to_numpy()
    s = d[score].astype(float).to_numpy()

    return {
        "score": public_score_name(score),
        "n_rows": len(d),
        "n_A_rows": n_a,
        "n_B_rows": n_b,
        "n_C_rows": n_c,
        "weighted_roc_auc": roc_auc_score(y, s, sample_weight=w),
        "weighted_pr_auc": average_precision_score(y, s, sample_weight=w),
    }


def cluster_bootstrap_delta_auc(
    df: pd.DataFrame,
    reference: str,
    comparators: Iterable[str],
    *,
    reps: int = BOOTSTRAP_REPS,
    seed: int = RANDOM_SEED,
    cluster_col: str = "parent_chembl_id",
) -> pd.DataFrame:
    comparators = list(comparators)
    d = df[[cluster_col, "benchmark_y", reference] + comparators].copy()
    d = d.dropna(subset=[cluster_col, "benchmark_y", reference])
    clusters = np.array(sorted(d[cluster_col].astype(str).unique()))
    cluster_labels = d[cluster_col].astype(str)
    cluster_parts = {cid: d.loc[cluster_labels == cid].copy() for cid in clusters}
    rng = np.random.default_rng(seed)
    vals = {c: [] for c in comparators}

    for _ in range(reps):
        sampled = rng.choice(clusters, size=len(clusters), replace=True)
        parts = []
        for draw_i, cid in enumerate(sampled):
            x = cluster_parts[str(cid)].copy()
            x["_draw"] = draw_i
            parts.append(x)
        b = pd.concat(parts, ignore_index=True)
        y = b["benchmark_y"].astype(int).to_numpy()
        if len(np.unique(y)) < 2:
            continue
        ref_auc = roc_auc_score(y, b[reference].astype(float).to_numpy())
        for c in comparators:
            if b[c].isna().any():
                continue
            auc = roc_auc_score(y, b[c].astype(float).to_numpy())
            vals[c].append(ref_auc - auc)

    rows = []
    for c, arr in vals.items():
        a = np.asarray(arr, dtype=float)
        rows.append(
            {
                "reference": reference,
                "comparator": public_score_name(c),
                "n_bootstrap_valid": len(a),
                "mean_delta_auc": np.mean(a) if len(a) else np.nan,
                "median_delta_auc": np.median(a) if len(a) else np.nan,
                "ci_2.5": np.quantile(a, 0.025) if len(a) else np.nan,
                "ci_97.5": np.quantile(a, 0.975) if len(a) else np.nan,
                "prob_delta_gt_0": np.mean(a > 0) if len(a) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def balanced_cluster_bootstrap(
    df: pd.DataFrame,
    reference: str,
    comparators: Iterable[str],
    *,
    reps: int = BOOTSTRAP_REPS,
    seed: int = RANDOM_SEED,
    cluster_col: str = "parent_chembl_id",
) -> pd.DataFrame:
    comparators = list(comparators)
    d = df[
        [cluster_col, "benchmark_group", "benchmark_y", reference] + comparators
    ].copy()
    d = d.dropna(
        subset=[cluster_col, "benchmark_group", "benchmark_y", reference]
    )

    parents = {
        g: np.array(
            sorted(
                d.loc[d["benchmark_group"] == g, cluster_col]
                .astype(str)
                .unique()
            )
        )
        for g in (A, B, C)
    }
    groups = d["benchmark_group"].to_numpy()
    cluster_labels = d[cluster_col].astype(str).to_numpy()
    cluster_parts = {
        (g, str(cid)): d.loc[(groups == g) & (cluster_labels == str(cid))].copy()
        for g in (A, B, C)
        for cid in parents[g]
    }
    rng = np.random.default_rng(seed)
    vals = {c: [] for c in comparators}

    for _ in range(reps):
        pieces = []
        draw_counter = 0
        for g in (A, B, C):
            pool = parents[g]
            sampled = rng.choice(pool, size=len(pool), replace=True)
            for cid in sampled:
                x = cluster_parts[(g, str(cid))].copy()
                x["_draw"] = draw_counter
                draw_counter += 1
                pieces.append(x)

        b = pd.concat(pieces, ignore_index=True)
        n_a = int((b["benchmark_group"] == A).sum())
        n_b = int((b["benchmark_group"] == B).sum())
        n_c = int((b["benchmark_group"] == C).sum())
        if min(n_a, n_b, n_c) == 0:
            continue

        weights = np.zeros(len(b), dtype=float)
        ga = b["benchmark_group"].to_numpy() == A
        gb = b["benchmark_group"].to_numpy() == B
        gc = b["benchmark_group"].to_numpy() == C
        weights[ga] = 1.0 / n_a
        weights[gb] = 0.5 / n_b
        weights[gc] = 0.5 / n_c

        y = b["benchmark_y"].astype(int).to_numpy()
        ref_auc = roc_auc_score(
            y, b[reference].astype(float).to_numpy(), sample_weight=weights
        )

        for c in comparators:
            if b[c].isna().any():
                continue
            auc = roc_auc_score(
                y, b[c].astype(float).to_numpy(), sample_weight=weights
            )
            vals[c].append(ref_auc - auc)

    rows = []
    for c, arr in vals.items():
        a = np.asarray(arr, dtype=float)
        rows.append(
            {
                "reference": reference,
                "comparator": public_score_name(c),
                "n_bootstrap_valid": len(a),
                "mean_delta_auc": np.mean(a) if len(a) else np.nan,
                "median_delta_auc": np.median(a) if len(a) else np.nan,
                "ci_2.5": np.quantile(a, 0.025) if len(a) else np.nan,
                "ci_97.5": np.quantile(a, 0.975) if len(a) else np.nan,
                "prob_delta_gt_0": np.mean(a > 0) if len(a) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def compare_table(
    observed: pd.DataFrame,
    expected_path: Path,
    *,
    sort_cols: list[str],
    atol: float = 1e-12,
    rtol: float = 1e-10,
) -> list[str]:
    expected = pd.read_csv(expected_path)
    observed = observed[expected.columns].copy()
    observed = observed.sort_values(sort_cols, kind="mergesort").reset_index(drop=True)
    expected = expected.sort_values(sort_cols, kind="mergesort").reset_index(drop=True)

    failures = []
    if len(observed) != len(expected):
        return [
            f"{expected_path.name}: row count {len(observed)} != expected {len(expected)}"
        ]

    for col in expected.columns:
        if pd.api.types.is_numeric_dtype(expected[col]):
            a = pd.to_numeric(observed[col], errors="coerce").to_numpy(dtype=float)
            b = pd.to_numeric(expected[col], errors="coerce").to_numpy(dtype=float)
            same = np.isclose(a, b, atol=atol, rtol=rtol, equal_nan=True)
            if not np.all(same):
                idx = int(np.where(~same)[0][0])
                failures.append(
                    f"{expected_path.name}: numeric mismatch in {col!r}, row {idx}: "
                    f"observed={a[idx]!r}, expected={b[idx]!r}"
                )
        else:
            a = observed[col].fillna("").astype(str).tolist()
            b = expected[col].fillna("").astype(str).tolist()
            if a != b:
                idx = next(i for i, (x, y) in enumerate(zip(a, b)) if x != y)
                failures.append(
                    f"{expected_path.name}: text mismatch in {col!r}, row {idx}: "
                    f"observed={a[idx]!r}, expected={b[idx]!r}"
                )
    return failures


def main() -> int:
    here = Path(__file__).resolve().parent
    root = here.parent

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--input",
        default=root / "inputs" / "primary_activity_status_records.csv",
        type=Path,
    )
    ap.add_argument(
        "--expected-dir",
        default=root / "expected_outputs" / "decomposition",
        type=Path,
    )
    ap.add_argument(
        "--output-dir",
        default=root / "reproduced_outputs" / "decomposition",
        type=Path,
    )
    ap.add_argument("--bootstrap-reps", type=int, default=BOOTSTRAP_REPS)
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    required = {
        "parent_chembl_id",
        "benchmark_group",
        "benchmark_y",
        *SCORE_COLUMNS,
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Input is missing required columns: {missing}")
    if "target_label" not in df.columns:
        raise ValueError("Input is missing required column: target_label")
    if df["target_label"].astype(str).str.upper().eq("5AR2").any():
        raise ValueError("Input contains excluded target 5AR2")

    primary_groups = df[df["benchmark_group"].isin([A, B, C])].copy()
    avb = primary_groups[primary_groups["benchmark_group"].isin([A, B])].copy()
    avc = primary_groups[primary_groups["benchmark_group"].isin([A, C])].copy()

    # The frozen primary table already encodes A=1 and B/C=0.
    args.output_dir.mkdir(parents=True, exist_ok=True)

    observed = {}
    observed["A_vs_B_metrics.csv"] = pd.DataFrame(
        [metrics(avb, score) for score in SCORE_COLUMNS]
    )
    observed["A_vs_C_metrics.csv"] = pd.DataFrame(
        [metrics(avc, score) for score in SCORE_COLUMNS]
    )

    comparators = [s for s in SCORE_COLUMNS if s != "integrated_gm3"]

    observed["A_vs_B_cluster_bootstrap_delta_auc.csv"] = (
        cluster_bootstrap_delta_auc(
            avb,
            "integrated_gm3",
            comparators,
            reps=args.bootstrap_reps,
            seed=RANDOM_SEED,
        )
    )
    observed["A_vs_C_cluster_bootstrap_delta_auc.csv"] = (
        cluster_bootstrap_delta_auc(
            avc,
            "integrated_gm3",
            comparators,
            reps=args.bootstrap_reps,
            seed=RANDOM_SEED,
        )
    )

    observed["balanced_negative_weighted_metrics.csv"] = pd.DataFrame(
        [weighted_metrics_balanced_negatives(primary_groups, score) for score in SCORE_COLUMNS]
    )

    observed["balanced_negative_bootstrap_delta_auc.csv"] = balanced_cluster_bootstrap(
        primary_groups,
        "integrated_gm3",
        comparators,
        reps=args.bootstrap_reps,
        seed=RANDOM_SEED,
    )

    avb_auc = observed["A_vs_B_metrics.csv"].set_index("score")["roc_auc"]
    avc_auc = observed["A_vs_C_metrics.csv"].set_index("score")["roc_auc"]
    bal_auc = observed["balanced_negative_weighted_metrics.csv"].set_index("score")[
        "weighted_roc_auc"
    ]

    observed["summary.csv"] = pd.DataFrame(
        {
            "score": [public_score_name(s) for s in SCORE_COLUMNS],
            "A_vs_B_roc_auc": [avb_auc[public_score_name(s)] for s in SCORE_COLUMNS],
            "A_vs_C_roc_auc": [avc_auc[public_score_name(s)] for s in SCORE_COLUMNS],
            "balanced_BC_weighted_roc_auc": [bal_auc[public_score_name(s)] for s in SCORE_COLUMNS],
        }
    )

    note = {
        "analysis_status": "POST HOC SENSITIVITY / MECHANISM DECOMPOSITION",
        "reason": (
            "Run after inspection of the locked primary A vs (B+C) benchmark. "
            "The purpose is to decompose the two complementary hard-negative "
            "mechanisms already encoded by groups B and C and to evaluate a "
            "B/C-balanced sensitivity."
        ),
        "score_definitions_changed": False,
        "labels_changed": False,
        "activity_thresholds_changed": False,
        "external_status_definition_changed": False,
        "primary_benchmark_replaced": False,
        "bootstrap_cluster": "parent_chembl_id",
        "bootstrap_reps": args.bootstrap_reps,
        "random_seed": RANDOM_SEED,
    }
    (args.output_dir / "analysis_note.json").write_text(
        json.dumps(note, indent=2) + "\n", encoding="utf-8"
    )

    for name, table in observed.items():
        table.to_csv(args.output_dir / name, index=False)

    contracts = {
        "A_vs_B_metrics.csv": ["score"],
        "A_vs_C_metrics.csv": ["score"],
        "A_vs_B_cluster_bootstrap_delta_auc.csv": ["reference", "comparator"],
        "A_vs_C_cluster_bootstrap_delta_auc.csv": ["reference", "comparator"],
        "balanced_negative_weighted_metrics.csv": ["score"],
        "balanced_negative_bootstrap_delta_auc.csv": ["reference", "comparator"],
        "summary.csv": ["score"],
    }

    failures = []
    for name, sort_cols in contracts.items():
        failures.extend(
            compare_table(
                observed[name],
                args.expected_dir / name,
                sort_cols=sort_cols,
            )
        )

    expected_note = json.loads((args.expected_dir / "analysis_note.json").read_text())
    if note != expected_note:
        failures.append("analysis_note.json: reproduced note does not match expected note")

    if failures:
        print("DOMAIN DECOMPOSITION REPRODUCTION: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("DOMAIN DECOMPOSITION REPRODUCTION: PASS")
    print(f"A vs B rows: {len(avb)}")
    print(f"A vs C rows: {len(avc)}")
    print(f"Bootstrap replicates: {args.bootstrap_reps}")
    print(f"Outputs: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
