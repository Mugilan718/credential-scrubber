"""
Reproducibility script: generates the four research figures for the
Credential Scrubber AI evaluation experiment.

Reads ONLY the existing, already-validated CSVs:
  - ai-evaluation/experiment/analysis/evaluation_dataset.csv  (96 rows)
  - ai-evaluation/experiment/analysis/paired_deltas.csv        (48 rows)

Writes PNG files to:
  - ai-evaluation/experiment/analysis/figures/

Modifies no input file. No new statistic, test, or score is computed -
every figure is a direct visualization of already-completed analysis
results (evaluation_dataset.csv's scores and paired_deltas.csv's
deltas, both frozen and produced in earlier phases).

Before drawing anything, this script:
  1. Loads evaluation_dataset.csv and asserts 96 rows, 48 original / 48
     sanitized.
  2. Loads paired_deltas.csv and asserts 48 rows.
  3. Independently RECOMPUTES sanitized-original deltas for the four
     always-scored dimensions directly from evaluation_dataset.csv and
     asserts they match paired_deltas.csv EXACTLY. If any mismatch is
     found, the script raises and stops - it does not silently repair
     or proceed.
  4. Asserts none of the four always-scored dimensions contains "N/A"
     anywhere in evaluation_dataset.csv (they must always be numeric).
  5. Recomputes failure-mode tag counts from evaluation_dataset.csv and
     asserts them against the fixed reference counts already reported
     in descriptive_results.md / inferential_results.md. Any mismatch
     halts the script rather than being silently absorbed into a chart.

Determinism: no random jitter is used anywhere. Overlapping discrete
observations (ordinal 1-5 scores, or many pairs sharing the same delta)
are rendered as deterministic dot grids (fixed row/column layout, no
RNG), so re-running this script byte-for-byte reproduces the same
figures. A random seed constant is still defined and documented per the
task's reproducibility requirement, even though no call in this script
consumes it.
"""

import csv
import sys
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import numpy as np

APP = r"D:\New-credential-scrubber\credential-scrubber-app"
DATASET_CSV = APP + r"\ai-evaluation\experiment\analysis\evaluation_dataset.csv"
PAIRED_CSV = APP + r"\ai-evaluation\experiment\analysis\paired_deltas.csv"
FIG_DIR = APP + r"\ai-evaluation\experiment\analysis\figures"

RANDOM_SEED = 42  # documented per reproducibility requirement; unused (no jitter needed - see module docstring)
DPI = 300

DIMS = ["correctness", "completeness", "consistency", "usefulness"]
DIM_LABELS = {"correctness": "Correctness", "completeness": "Completeness",
              "consistency": "Consistency", "usefulness": "Usefulness"}
TASK_ORDER = ["explain_code", "identify_bug", "security_analysis",
              "generate_unit_tests", "suggest_refactoring", "explain_config_relationships"]
LANG_ORDER = ["java", "python", "javascript", "typescript", "go", "csharp", "json", "yaml", "properties"]

COLOR_ORIGINAL = "#4C72B0"   # blue
COLOR_SANITIZED = "#DD8452"  # orange
COLOR_NEUTRAL = "#55637A"    # neutral slate gray, used for delta/failure-mode plots (no positive/negative connotation)
COLOR_ZERO_LINE = "#222222"

plt.rcParams.update({
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "figure.dpi": 100,        # on-screen; PNGs saved explicitly at DPI below
    "savefig.dpi": DPI,
    "font.family": "sans-serif",
})

# ---------------------------------------------------------------------
# Load + validate
# ---------------------------------------------------------------------
with open(DATASET_CSV, newline="", encoding="utf-8") as f:
    dataset_rows = list(csv.DictReader(f))
assert len(dataset_rows) == 96, f"EXPECTED 96 rows in evaluation_dataset.csv, got {len(dataset_rows)}"

n_orig = sum(1 for r in dataset_rows if r["condition"] == "original")
n_san = sum(1 for r in dataset_rows if r["condition"] == "sanitized")
assert n_orig == 48, f"EXPECTED 48 original rows, got {n_orig}"
assert n_san == 48, f"EXPECTED 48 sanitized rows, got {n_san}"

with open(PAIRED_CSV, newline="", encoding="utf-8") as f:
    paired_rows = list(csv.DictReader(f))
assert len(paired_rows) == 48, f"EXPECTED 48 rows in paired_deltas.csv, got {len(paired_rows)}"

# Assert the four always-scored dimensions are never "N/A" in the dataset.
for r in dataset_rows:
    for dim in DIMS:
        if r[dim] == "N/A":
            raise RuntimeError(
                f"DATA INTEGRITY VIOLATION: {dim} is 'N/A' for a response that should "
                f"always be scored ({r['response_file']}). Stopping rather than treating N/A as zero."
            )

# Independently recompute deltas from evaluation_dataset.csv and cross-check
# against paired_deltas.csv exactly (no repair on mismatch - fail loudly).
pair_map = defaultdict(dict)
for r in dataset_rows:
    key = (r["language"], r["file"], r["task"])
    pair_map[key][r["condition"]] = r

recomputed = {}
for key, conds in pair_map.items():
    if "original" not in conds or "sanitized" not in conds:
        raise RuntimeError(f"DATA INTEGRITY VIOLATION: incomplete pair for {key} - missing a condition.")
    o, s = conds["original"], conds["sanitized"]
    recomputed[key] = {dim: int(s[dim]) - int(o[dim]) for dim in DIMS}

mismatches = []
for pr in paired_rows:
    key = (pr["language"], pr["file"], pr["task"])
    if key not in recomputed:
        mismatches.append((key, "MISSING FROM evaluation_dataset.csv-derived pairs"))
        continue
    for dim in DIMS:
        csv_delta = int(pr[f"delta_{dim}"])
        recomputed_delta = recomputed[key][dim]
        if csv_delta != recomputed_delta:
            mismatches.append((key, dim, f"paired_deltas.csv={csv_delta} recomputed={recomputed_delta}"))

if mismatches:
    raise RuntimeError(
        "DATA INTEGRITY VIOLATION: recomputed deltas do not match paired_deltas.csv. "
        f"Stopping without modifying any data. Mismatches: {mismatches}"
    )
print(f"[OK] Recomputed all {len(recomputed)} pairs x {len(DIMS)} dimensions from evaluation_dataset.csv; "
      f"exact match against paired_deltas.csv confirmed (0 mismatches).")

if len(recomputed) != 48:
    raise RuntimeError(f"EXPECTED 48 recomputed pairs, got {len(recomputed)}")

# Failure-mode counts, recomputed from evaluation_dataset.csv, cross-checked
# against the fixed reference counts already established in
# descriptive_results.md / inferential_results.md.
tag_counter = Counter()
tag_cases = defaultdict(list)
for r in dataset_rows:
    fm = r["failure_modes"]
    if fm in ("none", ""):
        continue
    for t in (x.strip() for x in fm.split(";") if x.strip()):
        tag_counter[t] += 1
        tag_cases[t].append(r["response_file"])

EXPECTED_TAG_COUNTS = {
    "missed_sanitization_independent_issue": 14,
    "environmental_deviation": 6,
    "inferred_placeholder_value": 1,
    "placeholder_as_real_value": 1,
}
for tag, expected in EXPECTED_TAG_COUNTS.items():
    actual = tag_counter.get(tag, 0)
    if actual != expected:
        raise RuntimeError(
            f"DATA INTEGRITY VIOLATION: failure-mode tag '{tag}' expected count {expected} "
            f"(per descriptive_results.md/inferential_results.md), recomputed {actual} from "
            f"evaluation_dataset.csv. Stopping without modifying any data."
        )
unexpected_tags = set(tag_counter) - set(EXPECTED_TAG_COUNTS)
if unexpected_tags:
    raise RuntimeError(f"DATA INTEGRITY VIOLATION: unexpected failure-mode tag(s) found: {unexpected_tags}")
print(f"[OK] Failure-mode tag counts recomputed from evaluation_dataset.csv match documented reference counts: "
      f"{dict(tag_counter)}")

print("[OK] All pre-generation validation checks passed.\n")


# ---------------------------------------------------------------------
# Deterministic dot-grid helper (no randomness anywhere)
# ---------------------------------------------------------------------
def draw_dot_grid(ax, x_center, y_center, count, ncols=8, dx=0.05, dy=0.11,
                   color=COLOR_NEUTRAL, size=14, marker="o", alpha=0.85, edgecolor="white", linewidth=0.4):
    """Draws `count` markers as a deterministic grid centered at (x_center, y_center).
    No RNG is used - identical output on every run."""
    if count <= 0:
        return
    xs, ys = [], []
    for i in range(count):
        row = i // ncols
        col = i % ncols
        n_in_row = min(ncols, count - row * ncols)
        row_x_offset = (col - (n_in_row - 1) / 2.0) * dx
        row_y_offset = row * dy
        xs.append(x_center + row_x_offset)
        ys.append(y_center + row_y_offset)
    # center the whole block vertically around y_center
    n_rows = (count - 1) // ncols + 1
    total_h = (n_rows - 1) * dy
    ys = [y - total_h / 2.0 for y in ys]
    ax.scatter(xs, ys, s=size, c=color, marker=marker, alpha=alpha,
               edgecolors=edgecolor, linewidths=linewidth, zorder=3)


def draw_dot_fan(ax, x_center, y_value, count, dx=0.035,
                  color=COLOR_NEUTRAL, size=22, marker="o", alpha=0.85, edgecolor="white", linewidth=0.5):
    """For SMALL counts (<=12 or so): a single horizontal fan of dots at a
    fixed y, deterministic, no overlap-avoidance randomness."""
    if count <= 0:
        return
    offsets = np.linspace(-(count - 1) / 2.0, (count - 1) / 2.0, count) * dx
    xs = [x_center + o for o in offsets]
    ys = [y_value] * count
    ax.scatter(xs, ys, s=size, c=color, marker=marker, alpha=alpha,
               edgecolors=edgecolor, linewidths=linewidth, zorder=3)


# =======================================================================
# FIGURE 1 — Primary score distributions (Original vs Sanitized), 4 dims
# =======================================================================
fig, axes = plt.subplots(2, 2, figsize=(10, 9))
fig.suptitle("Figure 1. Primary rubric score distributions — Original vs. Sanitized (N=48 each)",
             fontsize=13, y=0.98)

for ax, dim in zip(axes.flat, DIMS):
    for cond, x_center, color in [("original", 0, COLOR_ORIGINAL), ("sanitized", 1, COLOR_SANITIZED)]:
        scores = [int(r[dim]) for r in dataset_rows if r["condition"] == cond]
        counts_by_score = Counter(scores)
        for score in range(1, 6):
            c = counts_by_score.get(score, 0)
            draw_dot_grid(ax, x_center, score, c, ncols=8, dx=0.11, dy=0.22, color=color, size=20)
    ax.set_title(DIM_LABELS[dim], fontsize=11)
    ax.set_xlim(-0.6, 1.6)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Original\n(N=48)", "Sanitized\n(N=48)"])
    ax.set_ylim(0.5, 5.5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_ylabel("Rubric score (ordinal, 1–5)")
    ax.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.5, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

legend_handles = [
    mlines.Line2D([], [], color=COLOR_ORIGINAL, marker="o", linestyle="None", markersize=7,
                  markeredgecolor="white", markeredgewidth=0.5, label="Original"),
    mlines.Line2D([], [], color=COLOR_SANITIZED, marker="o", linestyle="None", markersize=7,
                  markeredgecolor="white", markeredgewidth=0.5, label="Sanitized"),
]
fig.legend(handles=legend_handles, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.005))
fig.text(0.5, 0.005,
         "Each dot = one response. Dots are arranged in a fixed deterministic grid at each integer score "
         "(no jitter/randomness); ordinal scale, not a continuous measurement.",
         ha="center", fontsize=8, style="italic")
fig.tight_layout(rect=[0, 0.035, 1, 0.96])
fig.savefig(FIG_DIR + r"\primary_score_distributions.png", dpi=DPI, bbox_inches="tight")
plt.close(fig)
print("[OK] Wrote primary_score_distributions.png")


# =======================================================================
# FIGURE 2 — Paired delta distributions (Sanitized - Original), 4 dims
# =======================================================================
fig, ax = plt.subplots(figsize=(9, 7))
fig.suptitle("Figure 2. Paired score differences (Sanitized − Original), N=48 pairs per dimension",
             fontsize=13, y=0.97)

x_positions = {dim: i for i, dim in enumerate(DIMS)}
Y_MIN, Y_MAX = -4, 4  # symmetric around zero, per instruction

for dim in DIMS:
    deltas = [int(r[f"delta_{dim}"]) for r in paired_rows]
    counts_by_delta = Counter(deltas)
    x_c = x_positions[dim]
    for delta_val in range(Y_MIN, Y_MAX + 1):
        c = counts_by_delta.get(delta_val, 0)
        if c == 0:
            continue
        draw_dot_grid(ax, x_c, delta_val, c, ncols=8, dx=0.11, dy=0.16, color=COLOR_NEUTRAL, size=18)

ax.axhline(0, color=COLOR_ZERO_LINE, linewidth=1.4, zorder=1, label="No difference (0)")
ax.set_xlim(-0.6, len(DIMS) - 0.4)
ax.set_xticks(list(x_positions.values()))
xtick_labels = []
for dim in DIMS:
    deltas = [int(r[f"delta_{dim}"]) for r in paired_rows]
    n_zero = sum(1 for d in deltas if d == 0)
    xtick_labels.append(f"{DIM_LABELS[dim]}\n({n_zero}/48 pairs unchanged)")
ax.set_xticklabels(xtick_labels)
ax.tick_params(axis="x", pad=8)
ax.set_ylim(Y_MIN - 0.6, Y_MAX + 0.6)
ax.set_yticks(range(Y_MIN, Y_MAX + 1))
ax.set_ylabel("Paired difference (Sanitized score − Original score)")
ax.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.5, zorder=0)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.text(0.5, 0.005,
         "Each dot = one paired comparison. All 48 pairs are shown at their observed delta, including the "
         "zero-difference majority (annotated per dimension). No differences are hidden.",
         ha="center", fontsize=8, style="italic")
fig.tight_layout(rect=[0, 0.05, 1, 0.95])
fig.savefig(FIG_DIR + r"\paired_delta_distributions.png", dpi=DPI, bbox_inches="tight")
plt.close(fig)
print("[OK] Wrote paired_delta_distributions.png")


# =======================================================================
# FIGURE 3 — Task-level paired deltas (6 tasks, canonical manifest order)
# =======================================================================
fig, axes = plt.subplots(2, 3, figsize=(14, 8.5), sharey=True)
fig.suptitle("Figure 3. Paired score differences (Sanitized − Original) by task",
             fontsize=13, y=0.985)

DIM_X = {dim: i for i, dim in enumerate(DIMS)}
Y3_MIN, Y3_MAX = -4, 2  # observed range across this dataset; kept identical across all 6 panels

for ax, task in zip(axes.flat, TASK_ORDER):
    task_pairs = [r for r in paired_rows if r["task"] == task]
    n_applicable = len(task_pairs)
    n_na = len(LANG_ORDER) - n_applicable  # files for which this task is not_applicable

    for dim in DIMS:
        deltas = [int(r[f"delta_{dim}"]) for r in task_pairs]
        x_c = DIM_X[dim]
        counts_by_delta = Counter(deltas)
        for delta_val, c in counts_by_delta.items():
            draw_dot_fan(ax, x_c, delta_val, c, dx=0.05, color=COLOR_NEUTRAL, size=26)

    ax.axhline(0, color=COLOR_ZERO_LINE, linewidth=1.1, zorder=1)
    ax.set_xlim(-0.6, len(DIMS) - 0.4)
    ax.set_xticks(list(DIM_X.values()))
    ax.set_xticklabels(["Correct.", "Complete.", "Consist.", "Useful."], fontsize=8.5)
    ax.set_ylim(Y3_MIN - 0.5, Y3_MAX + 0.5)
    ax.set_yticks(range(Y3_MIN, Y3_MAX + 1))
    title = task
    if n_na > 0:
        ax.set_title(f"{task}\n(N={n_applicable} pairs; {n_na} files not applicable)", fontsize=9.5)
    else:
        ax.set_title(f"{task}\n(N={n_applicable} pairs)", fontsize=9.5)
    ax.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.5, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

for ax in axes[:, 0]:
    ax.set_ylabel("Paired difference\n(Sanitized − Original)", fontsize=9)

fig.text(0.5, 0.01,
         "Tasks shown in the order defined by the experiment manifest (not sorted by observed effect). "
         "Each dot = one paired comparison for that dimension. \"Not applicable\" files "
         "(explain_config_relationships is out of scope for the 6 source-code files) are stated explicitly "
         "in each panel title and are excluded from N, never counted as a zero difference.",
         ha="center", fontsize=8, style="italic")
fig.tight_layout(rect=[0, 0.035, 1, 0.955])
fig.savefig(FIG_DIR + r"\task_level_paired_deltas.png", dpi=DPI, bbox_inches="tight")
plt.close(fig)
print("[OK] Wrote task_level_paired_deltas.png")


# =======================================================================
# FIGURE 4 — Failure-mode frequency
# =======================================================================
# Fixed category structure per the task brief. Every named category is
# shown even where the observed count is 0 - nothing is silently dropped.
SANITIZATION_RELATED = [
    ("placeholder_as_real_value", "Placeholder treated as real/working value"),
    ("placeholder_flagged_as_security_issue", "Placeholder flagged as security issue"),
    ("unrunnable_placeholder_reuse", "Unrunnable placeholder reuse"),
    ("false_merge", "False merge"),
    ("false_split", "False split"),
    ("reconstructed_secret", "Reconstructed secret"),
]
SANITIZATION_INDEPENDENT = [
    ("missed_sanitization_independent_issue", "Missed a real,\nsanitization-independent issue"),
]
ENVIRONMENTAL = [
    ("environmental_deviation", "Environment/project-path leakage"),
    ("other_protocol_deviation", "Other protocol deviations"),
]
# Recorded in the dataset but outside the six named sanitization-related
# categories above (rubric checklist item: "response reveals it inferred
# what a placeholder probably stood for" - related to, but distinct from,
# "reconstructed secret"). Shown separately, not folded into either bucket,
# so no category is misrepresented.
OTHER_RECORDED = [
    ("inferred_placeholder_value", "Other recorded tag (not one of the\nsix listed categories): inferred what a\nplaceholder probably stood for"),
]

groups = [
    ("Sanitization-related", SANITIZATION_RELATED, "#4C72B0"),
    ("Sanitization-independent", SANITIZATION_INDEPENDENT, "#8172B2"),
    ("Environmental / protocol", ENVIRONMENTAL, "#55637A"),
    ("Other recorded tag", OTHER_RECORDED, "#8C8C8C"),
]

fig, ax = plt.subplots(figsize=(10, 7.5))
fig.suptitle("Figure 4. Failure-mode frequency across all 96 evaluated responses",
             fontsize=13, y=0.975)

y_labels = []
y_counts = []
y_colors = []
group_boundaries = []  # (start_idx, end_idx, group_name) for background shading/labels
idx = 0
for group_name, items, color in groups:
    start = idx
    for tag, label in items:
        count = tag_counter.get(tag, 0)
        y_labels.append(label)
        y_counts.append(count)
        y_colors.append(color)
        idx += 1
    group_boundaries.append((start, idx - 1, group_name))

y_pos = np.arange(len(y_labels))[::-1]  # top-to-bottom in listed order
bars = ax.barh(y_pos, y_counts, color=y_colors, edgecolor="white", height=0.65, zorder=3)

for yp, c in zip(y_pos, y_counts):
    ax.text(c + 0.25, yp, str(c), va="center", ha="left", fontsize=9.5, color="#222222", zorder=4)

ax.set_yticks(y_pos)
ax.set_yticklabels(y_labels, fontsize=8.8)
ax.set_xlabel("Observed count (of 96 responses)")
ax.set_xlim(0, max(y_counts) + 3)
ax.grid(axis="x", linestyle=":", linewidth=0.6, alpha=0.5, zorder=0)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Group separators + labels on the right margin
rev_index = {orig_i: len(y_labels) - 1 - orig_i for orig_i in range(len(y_labels))}
for start, end, group_name in group_boundaries:
    top_y = y_pos[start]
    bottom_y = y_pos[end]
    if start > 0:
        sep_y = (y_pos[start] + y_pos[start - 1]) / 2.0
        ax.axhline(sep_y, color="#cccccc", linewidth=0.8, zorder=1)

legend_handles = [plt.Rectangle((0, 0), 1, 1, color=color, label=name) for name, _, color in groups]
fig.legend(handles=legend_handles, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.02), fontsize=9)

fig.text(0.5, 0.015,
         "Exact counts recomputed directly from evaluation_dataset.csv's failure_modes field "
         "(cross-checked against descriptive_results.md / inferential_results.md). Categories with an "
         "observed count of 0 are shown explicitly, not omitted. Counts reflect responses (not unique failures); "
         "no response carried more than one tag in this dataset.",
         ha="center", fontsize=7.8, style="italic")
fig.tight_layout(rect=[0, 0.09, 1, 0.955])
fig.savefig(FIG_DIR + r"\failure_mode_frequency.png", dpi=DPI, bbox_inches="tight")
plt.close(fig)
print("[OK] Wrote failure_mode_frequency.png")

print("\nAll 4 figures generated successfully.")
print("matplotlib version:", matplotlib.__version__)
print("numpy version:", np.__version__)
print("python version:", sys.version)
