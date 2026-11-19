#!/usr/bin/env python3
"""Reproduce percentile 95% ROC-AUC intervals for OR2 Tables S11/S13B/S14A.

Usage:
    python reproduce_auc_confidence_intervals.py <OR2-archive.zip> [--check]

This script only reads the frozen record-level vectors. The broad ChEMBL and
comparator cohorts use 2,000 class-stratified bootstrap resamples; the curated
cohort uses 2,000 parent-molecule-cluster resamples. Both use NumPy PCG64
seed 2026, and two-sided percentile (2.5%, 97.5%) limits. Each cohort starts
its own random generator; all methods on a cohort use paired draws.
"""
import argparse
import io
import sys
import zipfile

import numpy as np
import pandas as pd
from scipy.stats import rankdata

SEED = 2026
N_BOOT = 2000

BROAD = {
    "SWAN-MPO": "swan_corrected_symmetric",
    "Binding-only": "d_binding",
    "ADME-only": "d_adme",
}
COMPARATORS = {
    "Descriptor-compatible SWAN variant": "swan_score",
    "CNS-MPO": "cns_mpo_inspired_oncology_proxy",
    "LE–QED composite proxy": "le_qed_composite_proxy",
    "QED": "qed_score",
    "QEPPI": "qeppi_score",
}


def auc(y, score):
    y = np.asarray(y, dtype=np.int8)
    n_pos = int(y.sum())
    n_neg = len(y) - n_pos
    if n_pos == 0 or n_neg == 0:
        raise ValueError("Both classes are required in an ROC-AUC resample")
    ranks = rankdata(np.asarray(score, dtype=float), method="average")
    return float((ranks[y == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def bootstrap(frame, label, columns, parent=None):
    rng = np.random.default_rng(SEED)
    y = frame[label].to_numpy(dtype=np.int8)
    scores = frame[columns].to_numpy(dtype=float)
    samples = np.empty((N_BOOT, len(columns)), dtype=float)

    if parent is None:
        positives = np.flatnonzero(y == 1)
        negatives = np.flatnonzero(y == 0)

        def draw():
            return np.r_[rng.choice(positives, len(positives), replace=True),
                         rng.choice(negatives, len(negatives), replace=True)]
    else:
        parents = frame[parent].fillna(frame.index.to_series().astype(str)).to_numpy()
        unique_parents = pd.unique(parents)
        groups = [np.flatnonzero(parents == p) for p in unique_parents]

        def draw():
            picked = rng.integers(0, len(groups), size=len(groups))
            return np.concatenate([groups[k] for k in picked])

    i = 0
    while i < N_BOOT:
        index = draw()
        yy = y[index]
        if yy.min() == yy.max():
            continue
        values = scores[index]
        for col in range(len(columns)):
            samples[i, col] = auc(yy, values[:, col])
        i += 1

    return {
        name: (auc(y, scores[:, col]), *map(float, np.quantile(samples[:, col], [0.025, 0.975])))
        for col, name in enumerate(columns)
    }


def read_csv(z, path):
    return pd.read_csv(io.BytesIO(z.read(path)))


def reproduce(z):
    broad = read_csv(z, "Reproduction_inputs/S11_S12_broad_chembl_corrected_profiles_3980.csv")
    comp = read_csv(z, "Table_S14C_MPO_comparator_compound_level_scores.csv")
    curated = read_csv(z, "Table_S13A_ChEMBL_activity_status_records.csv")
    s13b = read_csv(z, "Table_S13B_ChEMBL_activity_status_performance.csv")
    curated_cols = s13b.loc[s13b.section == "primary_performance", "score_implementation"].tolist()
    columns = ["structure_derived_liability" if c == "liability_only" else c for c in curated_cols]
    return {
        "Table_S11_broad_ChEMBL_metrics.csv": bootstrap(broad, "label", list(BROAD.values())),
        "Table_S14A_MPO_comparator_metrics.csv": bootstrap(comp, "label", list(COMPARATORS.values())),
        "Table_S13B_ChEMBL_activity_status_performance.csv": {
            method: result for method, result in zip(
                curated_cols,
                bootstrap(curated, "benchmark_y", columns, "parent_chembl_id").values()
            )
        },
    }


def check(z, estimates):
    mappings = {
        "Table_S11_broad_ChEMBL_metrics.csv": ("Scoring method", "ROC-AUC", BROAD),
        "Table_S14A_MPO_comparator_metrics.csv": ("Framework", "ROC-AUC", COMPARATORS),
        "Table_S13B_ChEMBL_activity_status_performance.csv": ("score_implementation", "roc_auc", None),
    }
    for filename, (key_field, auc_field, lookup) in mappings.items():
        table = read_csv(z, filename)
        for _, row in table.iterrows():
            key = row[key_field]
            if pd.isna(key) or (lookup is not None and key not in lookup):
                continue
            if lookup is None and row["section"] != "primary_performance":
                continue
            result_key = lookup[key] if lookup else key
            observed, low, high = estimates[filename][result_key]
            # Published point estimates have 3 decimals in S11 and S14A.
            tolerance = 0.00051 if lookup else 1e-6
            assert abs(float(row[auc_field]) - observed) <= tolerance, (filename, key, "point estimate")
            if "ci_lower" in table.columns:
                assert abs(float(row["ci_lower"]) - low) < 1e-9, (filename, key, "lower CI")
                assert abs(float(row["ci_upper"]) - high) < 1e-9, (filename, key, "upper CI")
            print(f"{filename}: {key} | AUC {observed:.6f} | 95% CI [{low:.6f}, {high:.6f}]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", help="Input OR2 ZIP")
    parser.add_argument("--check", action="store_true", help="Check existing CI columns against recomputation")
    arguments = parser.parse_args()
    with zipfile.ZipFile(arguments.archive) as archive:
        ci = reproduce(archive)
        check(archive, ci)
    print("PASS: 2,000 resamples per cohort, seed 2026, three independent input cohorts")
