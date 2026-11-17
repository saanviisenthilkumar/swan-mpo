#!/usr/bin/env python3
"""
Offline reproduction of the frozen SWAN-MPO descriptor-compatible MPO comparator benchmark.

The script reads the publication-facing 3,980-profile compound-level score table,
recomputes tie-averaged ROC-AUC/BEDROC/EF metrics, performs paired DeLong tests,
and compares both outputs against the archived expected tables.

It does not regenerate molecular descriptors or framework scores.
"""

from __future__ import annotations

import argparse
import hashlib
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.metrics import roc_auc_score

BEDROC_ALPHA = 20.0
EXPECTED_INPUT_SHA256 = "71fd4a0b39e0e7f4ad4aadf7cd1e4328203bd853434ef94f520e9cc79923a974"

FRAMEWORKS = [
    ("Descriptor-compatible SWAN variant", "swan_score"),
    ("CNS-MPO", "cns_mpo_inspired_oncology_proxy"),
    ("LE–QED composite proxy", "le_qed_composite_proxy"),
    ("QED", "qed_score"),
    ("QEPPI", "qeppi_score"),
]

DELONG_COMPARATORS = [
    (
        "Descriptor-compatible SWAN variant vs CNS-MPO-inspired oncology proxy",
        "cns_mpo_inspired_oncology_proxy",
    ),
    (
        "Descriptor-compatible SWAN variant vs LE–QED composite proxy",
        "le_qed_composite_proxy",
    ),
    (
        "Descriptor-compatible SWAN variant vs QED",
        "qed_score",
    ),
    (
        "Descriptor-compatible SWAN variant vs QEPPI-inspired proxy",
        "qeppi_score",
    ),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def clean_binary(y_true, scores) -> tuple[np.ndarray, np.ndarray]:
    y = np.asarray(list(y_true), dtype=int)
    s = np.asarray(list(scores), dtype=float)
    if y.shape != s.shape:
        raise ValueError("Labels and scores must have identical shapes.")
    mask = np.isfinite(s)
    y, s = y[mask], s[mask]
    if len(y) == 0:
        raise ValueError("No finite scores.")
    if not set(np.unique(y)).issubset({0, 1}):
        raise ValueError("Labels must be binary 0/1.")
    return y, s


def tie_averaged_enrichment_factor(y_true, scores, fraction: float) -> float:
    """Expected EF when tied score blocks are randomly permuted."""
    y, s = clean_binary(y_true, scores)
    if not (0 < fraction <= 1):
        raise ValueError("fraction must be in (0, 1].")
    n = len(y)
    n_active = int(y.sum())
    if n_active == 0:
        return float("nan")

    k = max(1, int(math.ceil(fraction * n)))
    order = np.argsort(-s, kind="mergesort")
    s, y = s[order], y[order]

    cutoff = s[k - 1]
    above = s > cutoff
    tied = s == cutoff
    slots = int(k - above.sum())
    expected_active = float(
        y[above].sum() + slots * (y[tied].sum() / tied.sum())
    )
    return float((expected_active / k) / (n_active / n))


def tie_averaged_bedroc(y_true, scores, alpha: float = BEDROC_ALPHA) -> float:
    """Exact expected BEDROC across all within-tie permutations."""
    y, s = clean_binary(y_true, scores)
    if alpha <= 0:
        raise ValueError("alpha must be positive.")

    order = np.argsort(-s, kind="mergesort")
    s, y = s[order], y[order]
    n = len(y)
    n_active = int(y.sum())
    if n_active == 0:
        return 0.0

    weighted_active_sum = 0.0
    start = 0
    while start < n:
        end = start + 1
        while end < n and s[end] == s[start]:
            end += 1
        block_size = end - start
        block_active = int(y[start:end].sum())
        if block_active:
            rank_weights = np.exp(-alpha * np.arange(start + 1, end + 1) / n)
            weighted_active_sum += (
                block_active / block_size
            ) * float(rank_weights.sum())
        start = end

    denom = (1.0 / n) * (
        (1.0 - math.exp(-alpha)) / (math.exp(alpha / n) - 1.0)
    )
    rie = weighted_active_sum / (n_active * denom)
    ratio = n_active / n
    rie_max = (
        (1.0 - math.exp(-alpha * ratio))
        / (ratio * (1.0 - math.exp(-alpha)))
    )
    rie_min = (
        (1.0 - math.exp(alpha * ratio))
        / (ratio * (1.0 - math.exp(alpha)))
    )
    return (
        float((rie - rie_min) / (rie_max - rie_min))
        if rie_max != rie_min
        else 1.0
    )


def metric_row(df: pd.DataFrame, display_name: str, score_col: str) -> dict:
    sub = df[["label", score_col]].dropna()
    sub = sub[sub["label"].isin([0, 1])]
    y, s = clean_binary(sub["label"], sub[score_col])

    return {
        "Framework": display_name,
        "ROC-AUC": round(float(roc_auc_score(y, s)), 3),
        "BEDROC alpha=20": round(tie_averaged_bedroc(y, s, BEDROC_ALPHA), 3),
        "EF@1%": round(tie_averaged_enrichment_factor(y, s, 0.01), 2),
        "EF@5%": round(tie_averaged_enrichment_factor(y, s, 0.05), 2),
    }


def compute_midrank(x: np.ndarray) -> np.ndarray:
    j = np.argsort(x)
    z = x[j]
    n = len(x)
    t = np.zeros(n, dtype=float)
    i = 0
    while i < n:
        k = i
        while k < n and z[k] == z[i]:
            k += 1
        t[i:k] = 0.5 * (i + k - 1) + 1
        i = k
    t2 = np.empty(n, dtype=float)
    t2[j] = t
    return t2


def fast_delong(
    predictions_sorted_transposed: np.ndarray,
    label_1_count: int,
):
    m = label_1_count
    n = predictions_sorted_transposed.shape[1] - m
    positive_examples = predictions_sorted_transposed[:, :m]
    negative_examples = predictions_sorted_transposed[:, m:]
    k = predictions_sorted_transposed.shape[0]

    tx = np.empty((k, m), dtype=float)
    ty = np.empty((k, n), dtype=float)
    tz = np.empty((k, m + n), dtype=float)

    for r in range(k):
        tx[r] = compute_midrank(positive_examples[r])
        ty[r] = compute_midrank(negative_examples[r])
        tz[r] = compute_midrank(predictions_sorted_transposed[r])

    aucs = (
        tz[:, :m].sum(axis=1) / m / n
        - (m + 1.0) / (2.0 * n)
    )
    v01 = (tz[:, :m] - tx) / n
    v10 = 1.0 - (tz[:, m:] - ty) / m

    sx = np.cov(v01)
    sy = np.cov(v10)
    if np.ndim(sx) == 0:
        sx = np.array([[float(sx)]])
    if np.ndim(sy) == 0:
        sy = np.array([[float(sy)]])
    delong_cov = sx / m + sy / n
    return aucs, delong_cov


def delong_pair(
    y: np.ndarray,
    score_a: np.ndarray,
    score_b: np.ndarray,
) -> dict[str, float]:
    order = np.argsort(-y, kind="mergesort")
    label_1_count = int(y.sum())
    preds = np.vstack([score_a, score_b])[:, order]
    aucs, cov = fast_delong(preds, label_1_count)

    contrast = np.array([1.0, -1.0])
    variance = float(contrast @ cov @ contrast.T)
    variance = max(variance, 0.0)
    se = math.sqrt(variance)
    delta = float(aucs[0] - aucs[1])
    z = delta / se if se > 0 else (math.inf if delta != 0 else 0.0)
    p = 2.0 * norm.sf(abs(z)) if math.isfinite(z) else 0.0

    return {
        "auc_a": float(aucs[0]),
        "auc_b": float(aucs[1]),
        "delta_auc": delta,
        "se": float(se),
        "z": float(z),
        "p_two_sided": float(p),
        "ci95_low": float(delta - norm.ppf(0.975) * se),
        "ci95_high": float(delta + norm.ppf(0.975) * se),
    }


def delong_table(df: pd.DataFrame) -> pd.DataFrame:
    required = {"label", "swan_score"} | {col for _, col in DELONG_COMPARATORS}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Input missing required DeLong columns: {missing}")

    rows = []
    for comparison, comparator_col in DELONG_COMPARATORS:
        sub = df[["label", "swan_score", comparator_col]].dropna()
        sub = sub[sub["label"].isin([0, 1])]
        y = sub["label"].astype(int).to_numpy()
        swan = sub["swan_score"].astype(float).to_numpy()
        comparator = sub[comparator_col].astype(float).to_numpy()

        result = delong_pair(y, swan, comparator)
        rows.append(
            {
                "comparison": comparison,
                "auc_swan": result["auc_a"],
                "auc_comparator": result["auc_b"],
                "delta_auc": result["delta_auc"],
                "standard_error": result["se"],
                "z_statistic": result["z"],
                "p_value": result["p_two_sided"],
                "ci95_low": result["ci95_low"],
                "ci95_high": result["ci95_high"],
            }
        )
    return pd.DataFrame(rows)


def compare_table(
    observed: pd.DataFrame,
    expected_path: Path,
    *,
    key: str,
    atol: float = 1e-12,
    rtol: float = 1e-10,
) -> list[str]:
    expected = pd.read_csv(expected_path)

    missing = [c for c in expected.columns if c not in observed.columns]
    if missing:
        return [f"{expected_path.name}: missing observed columns {missing}"]

    observed = observed[expected.columns].copy()
    observed = observed.sort_values(key, kind="mergesort").reset_index(drop=True)
    expected = expected.sort_values(key, kind="mergesort").reset_index(drop=True)

    if len(observed) != len(expected):
        return [
            f"{expected_path.name}: row count {len(observed)} "
            f"!= expected {len(expected)}"
        ]

    failures = []
    for col in expected.columns:
        if pd.api.types.is_numeric_dtype(expected[col]):
            a = pd.to_numeric(observed[col], errors="coerce").to_numpy(dtype=float)
            b = pd.to_numeric(expected[col], errors="coerce").to_numpy(dtype=float)
            same = np.isclose(
                a, b, atol=atol, rtol=rtol, equal_nan=True
            )
            if not np.all(same):
                idx = int(np.where(~same)[0][0])
                failures.append(
                    f"{expected_path.name}: mismatch in {col!r}, row {idx}: "
                    f"observed={a[idx]!r}, expected={b[idx]!r}"
                )
        else:
            a = observed[col].fillna("").astype(str).tolist()
            b = expected[col].fillna("").astype(str).tolist()
            if a != b:
                idx = next(
                    i for i, (x, y) in enumerate(zip(a, b)) if x != y
                )
                failures.append(
                    f"{expected_path.name}: mismatch in {col!r}, row {idx}: "
                    f"observed={a[idx]!r}, expected={b[idx]!r}"
                )
    return failures


def main() -> int:
    here = Path(__file__).resolve().parent
    root = here.parent

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--input",
        default=root / "inputs" / "comparator_compound_scores.csv",
        type=Path,
    )
    ap.add_argument(
        "--expected-dir",
        default=root / "expected_outputs",
        type=Path,
    )
    ap.add_argument(
        "--output-dir",
        default=root / "reproduced_outputs",
        type=Path,
    )
    ap.add_argument(
        "--skip-input-hash-check",
        action="store_true",
        help="Allow a noncanonical input table for exploratory use.",
    )
    args = ap.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(args.input)

    if not args.skip_input_hash_check:
        actual_hash = sha256_file(args.input)
        if actual_hash != EXPECTED_INPUT_SHA256:
            raise SystemExit(
                "Frozen comparator input hash mismatch.\n"
                f"Expected: {EXPECTED_INPUT_SHA256}\n"
                f"Observed: {actual_hash}"
            )

    df = pd.read_csv(args.input, low_memory=False)
    required = {"label"} | {col for _, col in FRAMEWORKS}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Input missing required columns: {missing}")

    metrics = pd.DataFrame(
        [metric_row(df, display, col) for display, col in FRAMEWORKS]
    )
    delong = delong_table(df)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(args.output_dir / "comparator_metrics.csv", index=False)
    delong.to_csv(args.output_dir / "comparator_delong.csv", index=False)

    failures = []
    failures.extend(
        compare_table(
            metrics,
            args.expected_dir / "comparator_metrics.csv",
            key="Framework",
        )
    )
    failures.extend(
        compare_table(
            delong,
            args.expected_dir / "comparator_delong.csv",
            key="comparison",
        )
    )

    if failures:
        print("MPO COMPARATOR REPRODUCTION: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("MPO COMPARATOR REPRODUCTION: PASS")
    print(f"Profiles: {len(df)}")
    print(f"Actives: {int(df['label'].sum())}")
    print(f"Inactives/decoys: {int((df['label'] == 0).sum())}")
    print(f"Input SHA-256: {sha256_file(args.input)}")
    print(f"Outputs: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
