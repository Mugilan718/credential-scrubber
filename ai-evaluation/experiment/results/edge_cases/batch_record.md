# Batch 9 (FINAL) record — `edge_cases/false_positives.properties`, 6 tasks × 2 conditions

**Status: 12/12 responses collected. Not scored. No LLM judge used.**
Procedural record only — no quality assessment, no comparison, no
conclusion. Scoring is a separate, later step against
`ai-evaluation/rubric/rubric.md`. This is the final collection batch —
the frozen experiment now has 96/96 raw responses collected.

## Applicability determination (from the frozen manifest, checked before launching any subagent)

`ai-evaluation/experiment/manifest.json` was re-read and confirmed
unchanged since it was frozen. Its `task_applicability_matrix` marks all
six tasks `"applicable"` for `edge_cases/false_positives.properties`
(the `explain_config_relationships` entry specifically notes: *"applicable
- in scope (.properties); expected to yield a low-relationship-density
response since the file is flat with no nested groups, which is itself a
valid negative-control observation for this task"*). No conflict between
the batch instructions' stated expectation (12 responses) and the
manifest's actual determination. Proceeded directly with all 12 cells.

## Applicable task IDs

`explain_code`, `identify_bug`, `security_analysis`,
`generate_unit_tests`, `suggest_refactoring`,
`explain_config_relationships` — all 6.

## Expected response count

12 (6 tasks × 2 conditions).

## Negative-control note

`benchmark/dataset/files/edge_cases/false_positives.properties` has zero
ground-truth true positives (`benchmark/dataset/cases.jsonl` confirms
`expected_detection: false` for every line). Its frozen sanitized copy
(`ai-evaluation/experiment/sanitized/edge_cases/false_positives.properties`)
is therefore byte-identical to the original — re-confirmed by direct
read immediately before this batch. Both conditions' prompts contain
identical file content by design; this is the expected, correct behavior
for this file, not an error. No additional interpretation, explanation,
or "this is a negative control" framing was added to either prompt —
each session received only the task template and the raw file content,
same as every other batch.

## Model

Claude, model id `claude-sonnet-5` ("Sonnet 5"). All 12 responses were
collected as fresh `general-purpose` Claude Code subagent invocations
(via the Agent tool) with no `model` override, so each inherited the
parent session's model — recorded as "inherited from the parent
session," consistent with all prior pilots/batches.

## Sanitized fixture source

`ai-evaluation/experiment/sanitized/edge_cases/false_positives.properties`
— the frozen fixture from the earlier preparation step. **Not
regenerated, not modified** for this batch — `engine.scan_project()` was
not called at any point during this batch.

## Execution date

2026-09-21T15:48:27Z (UTC) — all 12 sessions launched as independent,
parallel tool invocations within the same short window.

## Responses

| # | Task | Condition | Subagent id | Tool calls | Response file | Status |
|---|---|---|---|---:|---|---|
| 1 | `explain_code` | original | `ad011d583ce85e952` | 0 | `ai-evaluation/experiment/results/edge_cases/explain_code/original.txt` | success |
| 2 | `explain_code` | sanitized | `a1a1ced9e9b51eb3b` | 0 | `ai-evaluation/experiment/results/edge_cases/explain_code/sanitized.txt` | success |
| 3 | `identify_bug` | original | `affa62145c3f80afe` | 0 | `ai-evaluation/experiment/results/edge_cases/identify_bug/original.txt` | success |
| 4 | `identify_bug` | sanitized | `a0fdab3c4980cba34` | 0 | `ai-evaluation/experiment/results/edge_cases/identify_bug/sanitized.txt` | success |
| 5 | `security_analysis` | original | `a571b60c426ba81f6` | 0 | `ai-evaluation/experiment/results/edge_cases/security_analysis/original.txt` | success |
| 6 | `security_analysis` | sanitized | `a40fdc172e21640da` | 0 | `ai-evaluation/experiment/results/edge_cases/security_analysis/sanitized.txt` | success |
| 7 | `generate_unit_tests` | original | `a121fbc81f7147022` | 0 | `ai-evaluation/experiment/results/edge_cases/generate_unit_tests/original.txt` | success (see protocol deviation below) |
| 8 | `generate_unit_tests` | sanitized | `ab24bc54972aec770` | 0 | `ai-evaluation/experiment/results/edge_cases/generate_unit_tests/sanitized.txt` | success (see protocol deviation below) |
| 9 | `suggest_refactoring` | original | `a5cf704920841d2bc` | 0 | `ai-evaluation/experiment/results/edge_cases/suggest_refactoring/original.txt` | success |
| 10 | `suggest_refactoring` | sanitized | `a26f06a11ea38f2a8` | 0 | `ai-evaluation/experiment/results/edge_cases/suggest_refactoring/sanitized.txt` | success |
| 11 | `explain_config_relationships` | original | `a58b043478092e3ec` | 0 | `ai-evaluation/experiment/results/edge_cases/explain_config_relationships/original.txt` | success |
| 12 | `explain_config_relationships` | sanitized | `a1c87f3573081c338` | 0 | `ai-evaluation/experiment/results/edge_cases/explain_config_relationships/sanitized.txt` | success |

All 12 rows share `file: edge_cases/false_positives.properties`.

## Isolation confirmation

- **12 distinct subagent ids**, zero tool calls in every session.
- Each `original`/`sanitized` pair used a different subagent id.

## Protocol deviations — flagged, responses preserved unchanged, high confidence, two instances (both in the same task)

**Response #7 (`generate_unit_tests`, original condition)** contains:
*"the file's own comment ('None of these should ever be flagged...')
and its context (directory `New-credential-scrubber`) strongly suggest
this is a fixture for testing a separate credential-scrubbing tool..."*
— an exact match to the actual project directory name.

**Response #8 (`generate_unit_tests`, sanitized condition)** contains
**two** instances, and is the most severe leak observed across this
entire experiment: *"...evidently a credential/secret scrubber, given the
'New-credential-scrubber' project context..."* **and**, later, *"point me
at the scrubber/scanner source (or the directory it lives in under
`D:\New-credential-scrubber`)"* — this second instance reveals the
**full absolute filesystem path**, not merely the project name, going
beyond every prior deviation documented in this experiment (Batches 2,
5, 8 each showed only the bare project-name string).

Both sessions' prompts contained only the task template and raw file
content — no project name, no path, no drive letter — and both reported
`tool_uses: 0`, so neither read any file or explored the repository to
learn this. Per the environmental-control requirement, both are treated
as high-confidence environmental deviations (exact/distinctive
project/repository name and, in response #8's case, a full path,
appearing without being supplied).

**Per instruction: neither response was edited, neither was
regenerated, and this deviation did not prevent either response from
being collected under the frozen protocol** — both
`generate_unit_tests/original.txt` and `generate_unit_tests/sanitized.txt`
are saved complete and unedited, including these sentences. No cell was
re-run.

**Scope:** exactly 2 of 12 responses (both within the same task,
`generate_unit_tests`); the other 10, including 5 of the 6 tasks'
*sanitized* conditions, contain no reference to the project name, the
absolute path, "credential-scrubber," the experiment, or the other
condition.

**Note on this batch's structure:** because this file's sanitized and
original conditions are byte-identical (negative control, 0 detected
values), the two `generate_unit_tests` sessions received literally
identical prompt content — the fact that the deviation appeared in
*both* here (unlike prior batches, where it appeared in only one of a
pair) is consistent with, not contradictory to, a purely
environment-driven (not content-driven) leakage source: with identical
inputs, the two independent sessions had an equal, independent chance of
producing this pattern, and in this case both did.

**Generic reasoning correctly not counted as a deviation:** several
other responses (e.g., multiple noting the file "contains ordinary,
non-sensitive configuration" or that specific keys "merely contain a
sensitive-sounding substring without being a credential") drew
conclusions directly supported by the file's own header comment and
visible content — consistent with the "generic reasoning... is not
automatically a deviation" guidance, not counted.

## Settings

Same as all prior pilots/batches (carried forward, not re-decided):
temperature and max-output-tokens not independently controllable;
platform default applied identically and by omission to all 12
sessions. No conversation history; one response per condition, no
repeated sampling.

## What this record deliberately does not contain

No quality assessment of any response, no comparison between the
original and sanitized conditions, no rubric scores, and no conclusion
about whether sanitization helped or hurt for any of these 6 tasks.
`human_evaluation.md` for this batch has not been created — scoring is a
separate, later step. No summary statistics across the full 96-response
experiment are computed here either.
