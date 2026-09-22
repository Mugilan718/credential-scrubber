# Batch 8 record — `config/settings.yaml`, 6 tasks × 2 conditions

**Status: 12/12 responses collected. Not scored. No LLM judge used.**
Procedural record only — no quality assessment, no comparison, no
conclusion. Scoring is a separate, later step against
`ai-evaluation/rubric/rubric.md`.

## Applicability determination (from the frozen manifest, checked before launching any subagent)

`ai-evaluation/experiment/manifest.json` was re-read and confirmed
unchanged since it was frozen. Its `task_applicability_matrix` marks all
six tasks `"applicable"` for `config/settings.yaml`:

- `explain_code`: applicable
- `identify_bug`: applicable
- `security_analysis`: applicable
- `generate_unit_tests`: applicable
- `suggest_refactoring`: applicable
- `explain_config_relationships`: applicable

No conflict this time between the batch instructions' stated expectation
(12 responses) and the manifest's actual determination — both agree.
Proceeded directly with all 12 cells.

## Applicable task IDs

`explain_code`, `identify_bug`, `security_analysis`,
`generate_unit_tests`, `suggest_refactoring`,
`explain_config_relationships` — all 6.

## Expected response count

12 (6 tasks × 2 conditions).

## Model

Claude, model id `claude-sonnet-5` ("Sonnet 5"). All 12 responses were
collected as fresh `general-purpose` Claude Code subagent invocations
(via the Agent tool) with no `model` override, so each inherited the
parent session's model — recorded as "inherited from the parent
session," consistent with all prior pilots/batches.

## Sanitized fixture source

`ai-evaluation/experiment/sanitized/config/settings.yaml` — the frozen
fixture generated and validated in the earlier preparation step. **Not
regenerated, not modified** for this batch — `engine.scan_project()` was
not called at any point during this batch.

## Execution date

2026-09-21T15:44:00Z (UTC) — all 12 sessions launched as independent,
parallel tool invocations within the same short window.

## Responses

| # | Task | Condition | Subagent id | Tool calls | Response file | Status |
|---|---|---|---|---:|---|---|
| 1 | `explain_code` | original | `a3d475cf38ea8ca3a` | 0 | `ai-evaluation/experiment/results/config-yaml/explain_code/original.txt` | success (see protocol deviation below) |
| 2 | `explain_code` | sanitized | `ab0195d948ef799b7` | 0 | `ai-evaluation/experiment/results/config-yaml/explain_code/sanitized.txt` | success |
| 3 | `identify_bug` | original | `a097926f5a0aa97f9` | 0 | `ai-evaluation/experiment/results/config-yaml/identify_bug/original.txt` | success |
| 4 | `identify_bug` | sanitized | `ab9fb42a198793537` | 0 | `ai-evaluation/experiment/results/config-yaml/identify_bug/sanitized.txt` | success |
| 5 | `security_analysis` | original | `ace4701338303cdf8` | 0 | `ai-evaluation/experiment/results/config-yaml/security_analysis/original.txt` | success |
| 6 | `security_analysis` | sanitized | `a4d8aaeedf764953c` | 0 | `ai-evaluation/experiment/results/config-yaml/security_analysis/sanitized.txt` | success |
| 7 | `generate_unit_tests` | original | `a689822f8eca3c96e` | 0 | `ai-evaluation/experiment/results/config-yaml/generate_unit_tests/original.txt` | success |
| 8 | `generate_unit_tests` | sanitized | `a269706511f2406cf` | 0 | `ai-evaluation/experiment/results/config-yaml/generate_unit_tests/sanitized.txt` | success |
| 9 | `suggest_refactoring` | original | `ac4c65287d5e9bfc2` | 0 | `ai-evaluation/experiment/results/config-yaml/suggest_refactoring/original.txt` | success |
| 10 | `suggest_refactoring` | sanitized | `a5194cbf1263cab3c` | 0 | `ai-evaluation/experiment/results/config-yaml/suggest_refactoring/sanitized.txt` | success |
| 11 | `explain_config_relationships` | original | `af1838a61faa5c357` | 0 | `ai-evaluation/experiment/results/config-yaml/explain_config_relationships/original.txt` | success |
| 12 | `explain_config_relationships` | sanitized | `a67a87436ecdcc3d8` | 0 | `ai-evaluation/experiment/results/config-yaml/explain_config_relationships/sanitized.txt` | success |

All 12 rows share `file: config/settings.yaml`.

## Isolation confirmation

- **12 distinct subagent ids**, zero tool calls in every session.
- Each `original`/`sanitized` pair used a different subagent id.

## Protocol deviation — flagged, response preserved unchanged, high confidence

**Response #1 (`explain_code`, original condition) contains the
sentence:** *"...this is very likely a fixture used to test tooling such
as a credential/secret scanner (matching the working directory name
'New-credential-scrubber')..."*

This is the same exact, distinctive, high-confidence pattern already
documented in Batch 2's and Batch 5's `batch_record.md` — an exact match
to this repository's actual project directory name, appearing in a
session whose prompt contained only the task template and raw file
content (no project name, no path), and which reported `tool_uses: 0`.
Per the environmental-control requirement, this is treated as a
high-confidence environmental deviation (an exact/distinctive
project/repository name appearing without being supplied), not merely
"ordinary reasoning based on the visible YAML."

**Per instruction: the response was not edited, not regenerated, and
this deviation did not prevent the response from being collected under
the frozen protocol** — `explain_code/original.txt` is saved complete
and unedited, including this sentence. No cell was re-run.

**Scope:** exactly 1 of 12 responses; the other 11, including this same
task's *sanitized* condition, contain no reference to the project name,
"credential-scrubber," the experiment, or the other condition.

**Generic reasoning correctly not counted as a deviation:** several
responses (e.g. `explain_code`/sanitized noting the values are "clearly
stand-ins (redacted or template tokens)"; `security_analysis` responses
noting "All values in this file are placeholders... consistent with the
'synthetic benchmark fixture' comment") drew conclusions directly
supported by the visible YAML content (the header comment, the
`<...>` bracket syntax) — these are exactly the kind of generic,
content-grounded observations the environmental-control requirement says
not to treat as deviations.

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
separate, later step.
