# Analysis dataset — Credential Scrubber AI evaluation experiment

This directory holds the **structured, machine-readable dataset**
extracted from the 9 human-evaluation reports, prepared as the first
step of the statistical-analysis phase. `evaluation_dataset.csv` itself
contains no calculated statistics — it is a faithful, row-per-response
transcription of scores that were already assigned by hand during human
evaluation. The statistical-analysis phase that this dataset was built
for has since been completed in full - see "Reproducing the analysis"
below for what exists and how to regenerate it.

## Source files

Human evaluations (the sole source of every score in this dataset):

- `ai-evaluation/experiment/results/java/human_evaluation.md`
- `ai-evaluation/experiment/results/python/human_evaluation.md`
- `ai-evaluation/experiment/results/javascript/human_evaluation.md`
- `ai-evaluation/experiment/results/typescript/human_evaluation.md`
- `ai-evaluation/experiment/results/go/human_evaluation.md`
- `ai-evaluation/experiment/results/csharp/human_evaluation.md`
- `ai-evaluation/experiment/results/config/human_evaluation.md`
- `ai-evaluation/experiment/results/config-yaml/human_evaluation.md`
- `ai-evaluation/experiment/results/edge_cases/human_evaluation.md`

Also consulted for context and methodology (not as a score source):

- `ai-evaluation/rubric/rubric.md` — the six scoring dimensions and their
  1–5 definitions.
- `ai-evaluation/experiment/manifest.json` — the frozen
  `task_applicability_matrix` that determines which of the 108 nominal
  (file × task × condition) cells are applicable.
- `ai-evaluation/experiment/scoring_integrity_audit.md` — the completed
  audit of the human-evaluation phase, including its
  "Dimension 6 Methodology Resolution" section, whose rule this dataset
  applies uniformly (see below).

## Dataset

`evaluation_dataset.csv` — **96 rows, one per evaluated AI response** (8
files × 5 tasks × 2 conditions = 80, plus 3 files × 1 additional task ×
2 conditions = 6, totalling the 96 applicable cells out of 108 nominal
cells; the 12 non-applicable cells — `explain_config_relationships` for
the 6 source-code files — are correctly absent, not represented as
empty/N/A rows).

### Schema

| Column | Meaning |
|---|---|
| `language` | One of `java`, `python`, `javascript`, `typescript`, `go`, `csharp`, `json`, `yaml`, `properties` — the candidate file's language/format. |
| `file` | Repo-relative path of the candidate source file under `benchmark/dataset/files/`. |
| `task` | One of the 6 task IDs: `explain_code`, `identify_bug`, `security_analysis`, `generate_unit_tests`, `suggest_refactoring`, `explain_config_relationships`. |
| `condition` | `original` or `sanitized`. |
| `response_file` | Repo-relative path to the raw AI response `.txt` this row scores. |
| `correctness` | Rubric dimension 1, integer 1–5. Always scored (never N/A). |
| `completeness` | Rubric dimension 2, integer 1–5. Always scored. |
| `consistency` | Rubric dimension 3, integer 1–5. Always scored. |
| `usefulness` | Rubric dimension 4, integer 1–5. Always scored. |
| `misunderstood_value` | Rubric dimension 5. `N/A` for every `original`-condition row (48 rows); integer 4 or 5 for every `sanitized`-condition row (48 rows) — including the negative-control `properties` batch, where it is scored 5 (not N/A) per the rubric's own "not remarked on at all where that's appropriate" clause. |
| `relationships_preserved` | Rubric dimension 6. `N/A` for 90 rows; integer 5 for the 6 rows where the task is `explain_config_relationships` (see rule below). |
| `failure_modes` | Short machine-readable tag(s) from the rubric's failure-mode checklist, `;`-joined if more than one, or `none`. Tags used: `inferred_placeholder_value`, `placeholder_as_real_value`, `missed_sanitization_independent_issue`, `environmental_deviation`. (No response in this dataset triggered `placeholder_flagged_as_security_issue`, `false_merge`, `false_split`, or `unrunnable_placeholder_reuse`.) |
| `notes` | A compressed, one-line paraphrase of the evaluator's evidence/rationale for that response — the full prose evidence remains the source of record in the corresponding `human_evaluation.md`; this column exists for at-a-glance scanning of the structured dataset, not as a replacement for it. |
| `deviation` | `none`, or a short description of the documented environmental/protocol deviation affecting that specific response and its confidence level, matching `scoring_integrity_audit.md`'s deviation inventory. |

## Dimension 6 applicability rule (as applied in this dataset)

Per `scoring_integrity_audit.md`'s "Dimension 6 Methodology Resolution":

> Score "Relationships between values preserved?" ONLY when the specific
> task meaningfully requires the AI to reason about identity,
> association, grouping, or relationships between multiple sensitive
> values. Otherwise mark Dimension 6 as N/A. A file merely containing
> multiple sensitive values is not, by itself, sufficient to make
> Dimension 6 applicable.

Under this rule, exactly 6 of the 96 rows carry a non-N/A
`relationships_preserved` value: the `explain_config_relationships` task
for `json`/`appsettings.json`, `yaml`/`settings.yaml`, and
`properties`/`false_positives.properties`, in both conditions. All 90
other rows — including all 10 `java` rows, which had been scored 5/5 on
this dimension for 4 of 5 tasks in the pre-audit version of
`java/human_evaluation.md` — are `N/A`, taken directly from the
post-normalization state of the source files (the normalization itself
happened earlier, as its own tracked step; this dataset simply
transcribes the current, already-normalized scores).

## Row-count validation

Independently verified by script (`csv.DictReader` + cross-checked
against a fresh regex parse of all 9 source Markdown files — see
"Validation performed" below) immediately after the CSV was written:

- **96 rows total.**
- **48 `original` / 48 `sanitized`.**
- **Per-file counts:** `java`, `python`, `javascript`, `typescript`,
  `go`, `csharp` — 10 each; `json`, `yaml`, `properties` — 12 each.
- **Per-task counts:** `explain_code`, `identify_bug`,
  `security_analysis`, `generate_unit_tests`, `suggest_refactoring` — 18
  each (one per file × 2 conditions, across all 9 files);
  `explain_config_relationships` — 6 (3 files × 2 conditions).
- **Dimension 6:** exactly 6 non-N/A rows (all `explain_config_relationships`,
  scored 5), 90 N/A rows.
- **Dimension 5:** exactly 48 N/A rows, and every one of them is an
  `original`-condition row (no `sanitized` row is N/A; no `original` row
  is non-N/A).
- **No invalid scores:** every value in the four always-scored numeric
  columns, and in the two conditionally-scored columns, is one of
  `1`/`2`/`3`/`4`/`5`/`N/A` — no out-of-range, blank, or non-numeric
  value found.
- **No missing required fields:** every one of the 14 columns is
  populated in every row.
- **No duplicate rows:** all 96 `response_file` values are unique.
- **All 96 `response_file` paths verified to exist on disk.**

## Confirmation: scores copied without reinterpretation

Every numeric and N/A value in `evaluation_dataset.csv` was copied
verbatim from its source `human_evaluation.md` — no score was
recalculated, re-judged, rounded, or adjusted while building this
dataset. This was independently verified (not merely asserted) by a
script that re-parses all 9 source Markdown files from scratch — Java's
vertical `| Dimension | Score |` table format and the other 8 files'
horizontal `| Score | 1 | 2 | 3 | 4 | 5 | 6 |` format both required their
own parser — and diffs every one of the resulting 96 (correctness,
completeness, consistency, usefulness, misunderstood_value,
relationships_preserved) tuples against the corresponding CSV row.
**Result: 0 mismatches across all 96 rows.** The `notes` and
`failure_modes` columns are compressed paraphrases for scanability, not
independently-parsed fields — the full-text evidence in each
`human_evaluation.md` remains authoritative for qualitative detail.

## Confirmation: no statistics calculated (in this dataset-creation step)

This dataset-creation step itself computed **no** averages, medians,
deltas (original vs. sanitized), confidence intervals, significance
tests, or any other aggregate/derived value. `evaluation_dataset.csv`
contains only per-response, individually-assigned scores and short
qualitative paraphrases — nothing computed across rows. No chart, plot,
or summary table was produced as part of building this specific file.
The statistical-analysis phase that follows this dataset is now
complete - see below.

## Reproducing the analysis

Everything below reads only the committed CSVs in this directory
(`evaluation_dataset.csv`, `paired_deltas.csv`) or, for `paired_deltas.csv`
itself, the human-evaluation Markdown files listed above. None of the
commands below modify any input file.

### Paired delta dataset (`paired_deltas.csv`)

`paired_deltas.csv` (48 rows, one per applicable Original/Sanitized pair)
was derived from `evaluation_dataset.csv` and independently verified
against it at creation time (see "Confirmation: scores copied without
reinterpretation" above). It is also **independently re-derived and
cross-checked** every time `generate_figures.py` runs (see below) - so
regenerating the figures doubles as a standing integrity check on this
file. There is no separate standalone script to regenerate
`paired_deltas.csv` on its own; it was produced as part of the same
one-off pass documented above; use `run_inferential_analysis.py` or
`generate_figures.py`'s own recomputation-and-cross-check logic (see
each script's module docstring) if you need to re-verify it.

### Descriptive analysis (`descriptive_results.md`)

**No committed script reproduces `descriptive_results.md`.** It was
produced by a one-off analysis pass over `evaluation_dataset.csv` and
`paired_deltas.csv` (means, medians, standard deviations, and paired
deltas, broken down overall/by task/by language - no significance
testing), and the script used for that pass was not committed to this
repository. This is stated plainly rather than implying a script exists.
`descriptive_results.md`'s own numbers were, however, cross-checked
against the CSVs before publication (see that document's own
methodology notes). A researcher wanting to reproduce or extend the
descriptive statistics would need to write a new script against
`evaluation_dataset.csv`/`paired_deltas.csv` - `run_inferential_analysis.py`
(below) is a good reference for the loading/validation pattern to reuse.

### Inferential analysis (`inferential_results.md`, `inferential_results.csv`)

Reproducible from a committed script. Requires
`ai-evaluation/requirements-research.txt` (scipy, numpy):

```
pip install -r ai-evaluation/requirements-research.txt
python ai-evaluation/experiment/analysis/run_inferential_analysis.py
```

Run from the repository root; the script resolves its own input/output
paths internally (see its module docstring for the exact validation and
statistical methodology, including the fixed random seed used for
bootstrap confidence intervals). This regenerates
`inferential_results.csv` in place; `inferential_results.md`'s prose is
not auto-generated and was written to match that CSV's values, which
were verified to match at the time of writing.

### Figures (`figures/`)

```
pip install -r ai-evaluation/requirements-research.txt
python ai-evaluation/experiment/analysis/generate_figures.py
```

Regenerates all four PNGs under `figures/` in place. See
`figures/README.md` for what each figure shows and its own
reproducibility details (Python/matplotlib/numpy versions, determinism
guarantee).
