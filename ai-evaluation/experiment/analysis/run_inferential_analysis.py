"""
Reproducibility script for the inferential-statistics phase of the
Credential Scrubber AI evaluation experiment.

Reads the already-validated, already-scored CSVs:
  - ai-evaluation/experiment/analysis/paired_deltas.csv   (48 paired rows)
  - ai-evaluation/experiment/analysis/evaluation_dataset.csv (96 response rows,
    used only to identify which of the 48 pairs contain a response with a
    documented environmental-deviation failure-mode tag, for the sensitivity
    analysis in Step 8).

Writes:
  - ai-evaluation/experiment/analysis/inferential_results.csv

Does NOT modify any input file. Does NOT touch raw AI responses, human
evaluations, the rubric, the manifest, prompts, or fixtures.

Primary confirmatory analysis: two-sided Wilcoxon signed-rank test on the
paired (sanitized - original) difference, for each of the four
always-scored dimensions (Correctness, Completeness, Consistency,
Usefulness), across all 48 pairs (N=48 is the paired unit of analysis,
NOT 96 independent responses).

Zero-difference handling: scipy's `zero_method="wilcox"` (the classic
Wilcoxon treatment - pairs with a difference of exactly 0 are dropped
before ranking) is used throughout. This is documented explicitly wherever
it changes the effective N.

Multiple comparisons: Holm-Bonferroni step-down correction applied across
the primary dimensions that produced a valid p-value (Consistency is
degenerate - all 48 differences are exactly 0 - and is excluded from the
correction family rather than assigned a manufactured p-value).

Effect size: matched-pairs rank-biserial correlation, computed directly
from the signed ranks of the non-zero differences (Kerby 2014 "simple
difference formula"): r_rb = (W+ - W-) / (W+ + W-), where W+/W- are the
sums of ranks of |delta| for positive/negative differences respectively.

Confidence intervals: bootstrap (fixed seed, documented resample count),
for the MEDIAN paired difference, computed over ALL 48 pairs (including
zero differences - a bootstrap CI describes the paired-difference
distribution, not just the non-zero subset). BCa is attempted via
scipy.stats.bootstrap(method="BCa"); if BCa cannot be computed (degenerate
input, e.g. Consistency's all-zero data, or too few distinct values for a
valid jackknife/acceleration estimate), this script falls back to a
percentile bootstrap and states so explicitly in the output.
"""

import csv
import json
import sys
import platform

import numpy as np
import scipy
from scipy.stats import wilcoxon, bootstrap

APP = r"D:\New-credential-scrubber\credential-scrubber-app"
PAIRED_CSV = APP + r"\ai-evaluation\experiment\analysis\paired_deltas.csv"
DATASET_CSV = APP + r"\ai-evaluation\experiment\analysis\evaluation_dataset.csv"
OUT_CSV = APP + r"\ai-evaluation\experiment\analysis\inferential_results.csv"

RANDOM_SEED = 42
N_RESAMPLES = 10000
ALPHA = 0.05
DIMS = ["correctness", "completeness", "consistency", "usefulness"]

# ---------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------
with open(PAIRED_CSV, newline="", encoding="utf-8") as f:
    paired_rows = list(csv.DictReader(f))
assert len(paired_rows) == 48, f"expected 48 paired rows, got {len(paired_rows)}"

with open(DATASET_CSV, newline="", encoding="utf-8") as f:
    dataset_rows = list(csv.DictReader(f))
assert len(dataset_rows) == 96, f"expected 96 dataset rows, got {len(dataset_rows)}"

# Identify which (language, file, task) pairs contain >=1 response with an
# environmental_deviation failure-mode tag, for the Step 8 sensitivity analysis.
deviated_pair_keys = set()
for r in dataset_rows:
    if "environmental_deviation" in r["failure_modes"]:
        deviated_pair_keys.add((r["language"], r["file"], r["task"]))

for row in paired_rows:
    row["_key"] = (row["language"], row["file"], row["task"])
    row["_deviated"] = row["_key"] in deviated_pair_keys

n_deviated_pairs = sum(1 for r in paired_rows if r["_deviated"])

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def deltas_for(dim, rows=None):
    rows = rows if rows is not None else paired_rows
    return np.array([int(r[f"delta_{dim}"]) for r in rows], dtype=float)


def rank_biserial(deltas):
    """Matched-pairs rank-biserial correlation from signed ranks of |delta|
    for NON-ZERO differences (Kerby 2014 simple-difference formula)."""
    nz = deltas[deltas != 0]
    if nz.size == 0:
        return None, 0
    abs_ranks = _rank_average(np.abs(nz))
    w_pos = abs_ranks[nz > 0].sum()
    w_neg = abs_ranks[nz < 0].sum()
    denom = w_pos + w_neg
    r_rb = (w_pos - w_neg) / denom if denom > 0 else None
    return r_rb, nz.size


def _rank_average(x):
    """Average (mid) ranks, ties handled by averaging - matches scipy's
    default rank convention used internally by wilcoxon."""
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x), dtype=float)
    sorted_x = x[order]
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and sorted_x[j + 1] == sorted_x[i]:
            j += 1
        avg_rank = (i + 1 + j + 1) / 2.0
        ranks[order[i:j + 1]] = avg_rank
        i = j + 1
    return ranks


def bootstrap_median_ci(deltas, seed=RANDOM_SEED, n_resamples=N_RESAMPLES, alpha=ALPHA):
    """Returns (lower, upper, method_used, note)."""
    deltas = np.asarray(deltas, dtype=float)
    rng = np.random.default_rng(seed)

    # Degenerate case: all values identical (e.g. Consistency, all zeros).
    if np.all(deltas == deltas[0]):
        return float(deltas[0]), float(deltas[0]), "degenerate (all values identical)", \
            "All paired differences are identical; bootstrap resampling cannot produce any spread. CI collapses to a point at the constant value."

    # Try BCa first.
    try:
        data = (deltas,)
        res = bootstrap(
            data, np.median, n_resamples=n_resamples, method="BCa",
            confidence_level=1 - alpha, random_state=np.random.default_rng(seed),
        )
        lo, hi = float(res.confidence_interval.low), float(res.confidence_interval.high)
        if np.isnan(lo) or np.isnan(hi):
            raise ValueError("BCa produced NaN bounds")
        return lo, hi, "BCa (scipy.stats.bootstrap)", "BCa computed successfully."
    except Exception as e:
        # Fall back to manual percentile bootstrap with the same seed.
        boot_medians = np.empty(n_resamples)
        n = len(deltas)
        for i in range(n_resamples):
            sample = rng.choice(deltas, size=n, replace=True)
            boot_medians[i] = np.median(sample)
        lo = float(np.percentile(boot_medians, 100 * (alpha / 2)))
        hi = float(np.percentile(boot_medians, 100 * (1 - alpha / 2)))
        return lo, hi, "percentile bootstrap (manual, BCa unavailable/failed)", \
            f"BCa failed with: {e!r}. Fell back to percentile bootstrap with the same fixed seed."


def wilcoxon_report(deltas, dim_name):
    """Runs scipy wilcoxon with zero_method='wilcox' (drop zeros).
    Returns a dict of results, or a degenerate marker if not computable."""
    nz = deltas[deltas != 0]
    n_total = len(deltas)
    n_nonzero = len(nz)
    if n_nonzero == 0:
        return {
            "dimension": dim_name,
            "n_pairs": n_total,
            "nonzero_pairs": 0,
            "degenerate": True,
            "degenerate_reason": "all paired differences are exactly 0 - no basis for a signed-rank test",
            "statistic": None,
            "p_value": None,
            "direction": "no observed difference in any pair",
        }
    try:
        res = wilcoxon(deltas, zero_method="wilcox", alternative="two-sided", mode="auto")
        stat, p = float(res.statistic), float(res.pvalue)
        degenerate = False
        reason = None
        if n_nonzero < 6:
            # scipy still computes a result, but the normal approximation /
            # exact distribution is on very few points - flag explicitly,
            # do not silently present it with the same confidence as N=48.
            reason = f"only {n_nonzero} non-zero difference(s) out of {n_total} pairs; result reported but statistically very low-powered"
        median_delta = float(np.median(deltas))
        direction = (
            "no direction (median = 0)" if median_delta == 0
            else ("sanitized higher (positive)" if median_delta > 0 else "sanitized lower (negative)")
        )
        return {
            "dimension": dim_name,
            "n_pairs": n_total,
            "nonzero_pairs": n_nonzero,
            "degenerate": n_nonzero < 6,
            "degenerate_reason": reason,
            "statistic": stat,
            "p_value": p,
            "direction": direction,
        }
    except ValueError as e:
        return {
            "dimension": dim_name,
            "n_pairs": n_total,
            "nonzero_pairs": n_nonzero,
            "degenerate": True,
            "degenerate_reason": f"scipy.stats.wilcoxon raised: {e!r}",
            "statistic": None,
            "p_value": None,
            "direction": None,
        }


def holm_bonferroni(pvals_dict):
    """pvals_dict: {name: p}. Returns {name: (rank, adjusted_p, reject_at_alpha)}.
    Standard Holm step-down procedure."""
    items = sorted(pvals_dict.items(), key=lambda kv: kv[1])
    m = len(items)
    adjusted = {}
    running_max = 0.0
    for i, (name, p) in enumerate(items):
        rank = i + 1
        raw_adj = (m - rank + 1) * p
        running_max = max(running_max, raw_adj)
        adj_p = min(running_max, 1.0)
        adjusted[name] = adj_p
    return adjusted


# ---------------------------------------------------------------------
# STEP 1-4: primary confirmatory analysis (4 dimensions, all 48 pairs)
# ---------------------------------------------------------------------
print("=" * 70)
print("REPRODUCIBILITY / ENVIRONMENT")
print("=" * 70)
print("python:", sys.version)
print("platform:", platform.platform())
print("numpy:", np.__version__)
print("scipy:", scipy.__version__)
print("random seed:", RANDOM_SEED)
print("bootstrap resamples:", N_RESAMPLES)
print("wilcoxon zero_method: 'wilcox' (drop zero differences before ranking)")
print("multiple-comparison correction: Holm-Bonferroni step-down")

print()
print("=" * 70)
print("STEP 1-3: PRIMARY WILCOXON TESTS + EFFECT SIZE + BOOTSTRAP CI (N=48 pairs)")
print("=" * 70)

primary_results = {}
for dim in DIMS:
    deltas = deltas_for(dim)
    wr = wilcoxon_report(deltas, dim)
    r_rb, n_nz = rank_biserial(deltas)
    lo, hi, ci_method, ci_note = bootstrap_median_ci(deltas)
    mean_delta = float(np.mean(deltas))
    median_delta = float(np.median(deltas))
    primary_results[dim] = {
        **wr,
        "mean_delta": mean_delta,
        "median_delta": median_delta,
        "effect_size_rank_biserial": r_rb,
        "ci_lower": lo,
        "ci_upper": hi,
        "ci_method": ci_method,
        "ci_note": ci_note,
    }
    print(f"\n--- {dim} ---")
    for k, v in primary_results[dim].items():
        print(f"  {k}: {v}")

# ---------------------------------------------------------------------
# STEP 4: Holm-Bonferroni across dimensions with a valid p-value
# ---------------------------------------------------------------------
print()
print("=" * 70)
print("STEP 4: HOLM-BONFERRONI CORRECTION")
print("=" * 70)
testable = {d: primary_results[d]["p_value"] for d in DIMS if primary_results[d]["p_value"] is not None}
print("Dimensions included in correction family (valid p-value produced):", list(testable.keys()))
print("Dimensions EXCLUDED from correction family (degenerate, no p-value):",
      [d for d in DIMS if primary_results[d]["p_value"] is None])
holm_adj = holm_bonferroni(testable)
for dim in DIMS:
    if dim in holm_adj:
        adj = holm_adj[dim]
        sig = adj < ALPHA
        primary_results[dim]["holm_adjusted_p"] = adj
        primary_results[dim]["significant_after_holm"] = sig
        print(f"  {dim}: raw_p={testable[dim]:.6g}  holm_adj_p={adj:.6g}  significant(alpha=0.05)={sig}")
    else:
        primary_results[dim]["holm_adjusted_p"] = None
        primary_results[dim]["significant_after_holm"] = None
        print(f"  {dim}: excluded from correction family (degenerate/no p-value)")

# ---------------------------------------------------------------------
# Write inferential_results.csv
# ---------------------------------------------------------------------
fieldnames = [
    "dimension", "n_pairs", "nonzero_pairs", "median_delta", "mean_delta",
    "wilcoxon_statistic", "raw_p_value", "holm_adjusted_p_value",
    "effect_size", "ci_lower", "ci_upper", "ci_method", "alpha", "significant_after_holm",
]
with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for dim in DIMS:
        r = primary_results[dim]
        w.writerow({
            "dimension": dim,
            "n_pairs": r["n_pairs"],
            "nonzero_pairs": r["nonzero_pairs"],
            "median_delta": r["median_delta"],
            "mean_delta": round(r["mean_delta"], 6),
            "wilcoxon_statistic": r["statistic"] if r["statistic"] is not None else "NA",
            "raw_p_value": round(r["p_value"], 6) if r["p_value"] is not None else "NA",
            "holm_adjusted_p_value": round(r["holm_adjusted_p"], 6) if r.get("holm_adjusted_p") is not None else "NA",
            "effect_size": round(r["effect_size_rank_biserial"], 6) if r["effect_size_rank_biserial"] is not None else "NA",
            "ci_lower": r["ci_lower"],
            "ci_upper": r["ci_upper"],
            "ci_method": r["ci_method"],
            "alpha": ALPHA,
            "significant_after_holm": r.get("significant_after_holm") if r.get("significant_after_holm") is not None else "NA",
        })
print(f"\nWrote {OUT_CSV}")

# ---------------------------------------------------------------------
# STEP 5: Task-level exploratory analysis
# ---------------------------------------------------------------------
print()
print("=" * 70)
print("STEP 5: TASK-LEVEL EXPLORATORY ANALYSIS (labeled exploratory)")
print("=" * 70)
task_order = ["explain_code", "identify_bug", "security_analysis", "generate_unit_tests",
              "suggest_refactoring", "explain_config_relationships"]
task_results = {}
for task in task_order:
    rows = [r for r in paired_rows if r["task"] == task]
    task_results[task] = {}
    print(f"\n### {task}  (N pairs = {len(rows)})")
    for dim in DIMS:
        deltas = deltas_for(dim, rows)
        median_delta = float(np.median(deltas))
        mean_delta = float(np.mean(deltas))
        nz = deltas[deltas != 0]
        result = {"n": len(deltas), "nonzero": len(nz), "median_delta": median_delta, "mean_delta": mean_delta}
        # Only attempt Wilcoxon where there is at least some non-zero variation
        # and enough pairs to be worth reporting (exploratory, not confirmatory).
        if len(nz) >= 1 and len(rows) >= 5:
            try:
                res = wilcoxon(deltas, zero_method="wilcox", alternative="two-sided", mode="auto")
                result["wilcoxon_statistic"] = float(res.statistic)
                result["p_value_exploratory"] = float(res.pvalue)
            except Exception as e:
                result["wilcoxon_statistic"] = None
                result["p_value_exploratory"] = None
                result["wilcoxon_error"] = repr(e)
        else:
            result["wilcoxon_statistic"] = None
            result["p_value_exploratory"] = None
            result["note"] = "not computed: too few pairs or no non-zero differences for a meaningful exploratory test"
        task_results[task][dim] = result
        print(f"  {dim}: {result}")

# ---------------------------------------------------------------------
# STEP 6: Language/file-type exploratory analysis
# ---------------------------------------------------------------------
print()
print("=" * 70)
print("STEP 6: LANGUAGE/FILE-TYPE EXPLORATORY ANALYSIS (labeled exploratory)")
print("=" * 70)
lang_order = ["java", "python", "javascript", "typescript", "go", "csharp", "json", "yaml", "properties"]
lang_results = {}
for lang in lang_order:
    rows = [r for r in paired_rows if r["language"] == lang]
    lang_results[lang] = {}
    print(f"\n### {lang}  (N pairs = {len(rows)})")
    for dim in DIMS:
        deltas = deltas_for(dim, rows)
        median_delta = float(np.median(deltas))
        mean_delta = float(np.mean(deltas))
        nz = deltas[deltas != 0]
        result = {"n": len(deltas), "nonzero": len(nz), "median_delta": median_delta, "mean_delta": mean_delta}
        lang_results[lang][dim] = result
        print(f"  {dim}: {result}")

# ---------------------------------------------------------------------
# STEP 7: Properties negative-control analysis
# ---------------------------------------------------------------------
print()
print("=" * 70)
print("STEP 7: PROPERTIES NEGATIVE-CONTROL ANALYSIS")
print("=" * 70)
prop_rows = [r for r in paired_rows if r["language"] == "properties"]
print(f"N properties pairs = {len(prop_rows)} (byte-identical original/sanitized source input)")
changed_pairs = 0
for r in prop_rows:
    changes = {dim: int(r[f"delta_{dim}"]) for dim in DIMS if int(r[f"delta_{dim}"]) != 0}
    if changes:
        changed_pairs += 1
    print(f"  task={r['task']:28s} deltas: "
          f"C={r['delta_correctness']} Co={r['delta_completeness']} Cn={r['delta_consistency']} U={r['delta_usefulness']}"
          f"{'  <-- CHANGED despite identical input' if changes else ''}")
print(f"\nPairs with >=1 non-zero delta despite byte-identical input: {changed_pairs} of {len(prop_rows)}")

# ---------------------------------------------------------------------
# STEP 8: Environmental-deviation sensitivity analysis
# ---------------------------------------------------------------------
print()
print("=" * 70)
print("STEP 8: ENVIRONMENTAL-DEVIATION SENSITIVITY ANALYSIS (clearly labeled, excludes deviated pairs)")
print("=" * 70)
print(f"Pairs containing >=1 response with an environmental_deviation tag: {n_deviated_pairs}")
for r in paired_rows:
    if r["_deviated"]:
        print(f"  EXCLUDED in sensitivity analysis: {r['language']}/{r['task']}")

clean_rows = [r for r in paired_rows if not r["_deviated"]]
print(f"\nSensitivity-analysis N = {len(clean_rows)} pairs (48 - {n_deviated_pairs} = {len(clean_rows)})")

sensitivity_results = {}
for dim in DIMS:
    deltas = deltas_for(dim, clean_rows)
    wr = wilcoxon_report(deltas, dim)
    r_rb, n_nz = rank_biserial(deltas)
    lo, hi, ci_method, ci_note = bootstrap_median_ci(deltas)
    sensitivity_results[dim] = {
        **wr,
        "mean_delta": float(np.mean(deltas)),
        "median_delta": float(np.median(deltas)),
        "effect_size_rank_biserial": r_rb,
        "ci_lower": lo, "ci_upper": hi, "ci_method": ci_method,
    }
    print(f"\n--- {dim} (sensitivity, N={len(clean_rows)}) ---")
    for k, v in sensitivity_results[dim].items():
        print(f"  {k}: {v}")

testable_sens = {d: sensitivity_results[d]["p_value"] for d in DIMS if sensitivity_results[d]["p_value"] is not None}
holm_adj_sens = holm_bonferroni(testable_sens)
print("\nHolm-adjusted p-values (sensitivity analysis):")
for dim in DIMS:
    if dim in holm_adj_sens:
        adj = holm_adj_sens[dim]
        print(f"  {dim}: raw_p={testable_sens[dim]:.6g} holm_adj_p={adj:.6g} significant={adj < ALPHA}")
    else:
        print(f"  {dim}: excluded (degenerate)")

print("\n\nDone. All computations complete; see inferential_results.csv for the primary-analysis table.")
