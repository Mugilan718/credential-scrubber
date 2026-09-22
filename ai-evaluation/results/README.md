# Results — schema and process (superseded scaffold)

**This directory's own `results_template.csv` is still just an empty
header row - it was never filled in.** That is expected, not stale: this
directory describes the schema and recording process this project
designed *before* the first real experiment ran. The actual experiment
was executed under a full, frozen 9-file x 6-task x 2-condition design
instead of the single small run this scaffold anticipated, and its real
results live at `../experiment/results/` (raw responses, per-file
`batch_record.md` and `human_evaluation.md`) and
`../experiment/analysis/evaluation_dataset.csv` (the same 96 scored
responses in structured, one-row-per-response form) - see
`../experiment/README.md` for the completed experiment's status and
`../README.md` for the overall phase summary.

**Do not read this directory as containing active experiment results.**
It is kept for the column-schema and blind-rating-process documentation
below, which the actual experiment's scoring followed in substance (see
`../experiment/results/*/human_evaluation.md`, which record the same six
rubric dimensions plus failure-mode tags described here), even though
the real data was ultimately organized as one `human_evaluation.md` per
candidate file rather than as a single filled-in `results_template.csv`.

## Original plan for this directory (not what actually happened)

This is the layout this scaffold originally anticipated - a `runs/<run_id>/`
folder per experiment run, filled in here:

```
results/
├── README.md                 This file.
├── results_template.csv      Empty schema (committed as-is in this phase).
├── runs/<run_id>/             One folder per experiment run (created at run time).
│   ├── raw_responses/          One .txt file per (file, task, condition) call.
│   └── results.csv             That run's filled-in copy of the template.
```

**This `runs/` layout was never created.** When the real experiment was
built out, it used the frozen design under `../experiment/` instead
(`experiment/results/<candidate>/<task>/{original,sanitized}.txt` plus a
`human_evaluation.md` per candidate file, rather than a single
`results.csv` per run) - see the note at the top of this document.

Raw model responses are **not** inlined into the CSV. They're long,
multi-line, and can contain characters that make CSV fragile; each
response is saved as its own text file under `raw_responses/`, and the
CSV row references it by filename via `response_file`. This also makes it
trivial to hand a rater the raw response file directly without also
handing them the CSV's other columns (see "Blind rating" below).

## Column schema (`results_template.csv`)

| Column | Meaning |
|---|---|
| `run_id` | Identifier for the experiment run this row belongs to (e.g. a date-based id). |
| `date` | ISO date the call was made. |
| `case_file` | Path (relative to `benchmark/dataset/files/`) of the source file used. |
| `task` | One of the six task names in `prompts/` (filename without extension). |
| `prompt_version` | Filename + a version marker for the exact template text used - if a template is edited later, bump this so old and new results are never silently compared. |
| `condition` | `original` or `sanitized`. **Populated by the experiment coordinator, not shown to the rater at scoring time** - see "Blind rating". |
| `response_id` | An opaque code (e.g. `R014`) shown to the rater *instead of* the condition - this is what "blind" means here in practice. |
| `model` | Model name. |
| `model_version` | Exact version/snapshot identifier, where the provider exposes one. |
| `temperature` | Sampling temperature used (should be `0` per `prompts/README.md`'s recommended settings, recorded explicitly rather than assumed). |
| `response_file` | Filename of the saved raw response under `raw_responses/`. |
| `rater_id` | Who scored this response (a name or initials is fine for a small pilot). |
| `correctness` | 1-5, per `rubric/rubric.md`. |
| `completeness` | 1-5. |
| `consistency` | 1-5. |
| `usefulness` | 1-5. |
| `misunderstood_value` | 1-5 or `N/A`. |
| `relationships_preserved` | 1-5 or `N/A`. |
| `failure_modes` | Semicolon-separated tags from the rubric's checklist (e.g. `treated_placeholder_as_real;false_merge`), empty if none apply. |
| `notes` | Freeform. Not optional - see the rubric's own note on why. |

## Blind rating

Where practical, the rater scores a response identified only by
`response_id`, without being told whether it's the original- or
sanitized-condition response, until after both are scored. The mapping
from `response_id` to `condition` is kept by whoever coordinates the run
(e.g. in a small separate key file, or simply filled into the `condition`
column only after scoring is complete) so scoring isn't influenced by
knowing which one is "supposed" to look worse.

This isn't always fully achievable - a sanitized response will often be
identifiable by its content (visible `<PLACEHOLDER>` tokens), and that's
fine; it does not need to be hidden from the rater as a fact. What must
be avoided is the rater going in already primed to expect one condition
to score lower.

## What this directory actually commits

Only `README.md` and `results_template.csv` (header row only, still
empty). No `runs/` directory, no raw responses, no filled-in rows were
ever added here - the real experiment's raw responses and scored results
were committed under `../experiment/results/` and
`../experiment/analysis/` instead (see the note at the top of this
document).
