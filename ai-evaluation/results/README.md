# Results — schema and process

**No results exist yet.** `results_template.csv` contains only a header
row. This document describes the schema and the recording process for
when the first experiment is actually run - not part of this preparation
phase.

## Files this directory will hold once an experiment runs

```
results/
├── README.md                 This file.
├── results_template.csv      Empty schema (committed as-is in this phase).
├── runs/<run_id>/             One folder per experiment run (created at run time).
│   ├── raw_responses/          One .txt file per (file, task, condition) call.
│   └── results.csv             That run's filled-in copy of the template.
```

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

## What this phase commits

Only `README.md` and `results_template.csv` (header row only). No
`runs/` directory, no raw responses, no filled-in rows - those are all
created when an experiment is actually executed, which is explicitly not
part of this preparation phase.
