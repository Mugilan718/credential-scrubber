# Batch 5 record — `go/config.go`, 5 tasks × 2 conditions

**Status: 10/10 responses collected. Not scored. No LLM judge used.**
Procedural record only — no quality assessment, no comparison, no
conclusion. Scoring is a separate, later step against
`ai-evaluation/rubric/rubric.md`.

## Frozen scope confirmation

`go/config.go` is applicable for exactly these 5 tasks — `explain_code`,
`identify_bug`, `security_analysis`, `generate_unit_tests`,
`suggest_refactoring` — and `explain_config_relationships` is
`not_applicable` per the frozen manifest (source code, not a config
file). `explain_config_relationships` was **not** run.

## Model

Claude, model id `claude-sonnet-5` ("Sonnet 5"). All 10 responses were
collected as fresh `general-purpose` Claude Code subagent invocations
(via the Agent tool) with no `model` override, so each inherited the
parent session's model — recorded as "inherited from the parent
session," consistent with all prior pilots/batches.

## Sanitized fixture source

`ai-evaluation/experiment/sanitized/go/config.go` — the frozen fixture
generated and validated in the earlier preparation step. **Not
regenerated** for this batch — `engine.scan_project()` was not called at
any point during this batch.

## Execution date

2026-09-21T15:30:15Z (UTC) — all 10 sessions launched as independent,
parallel tool invocations within the same short window.

## Responses

| # | Task | Condition | Subagent id | Tool calls | Response file | Status |
|---|---|---|---|---:|---|---|
| 1 | `explain_code` | original | `a4f8c7717f223b384` | 0 | `ai-evaluation/experiment/results/go/explain_code/original.txt` | success (see protocol deviation below) |
| 2 | `explain_code` | sanitized | `a65f873ed0c6d3618` | 0 | `ai-evaluation/experiment/results/go/explain_code/sanitized.txt` | success |
| 3 | `identify_bug` | original | `a763850cd463b6c0c` | 0 | `ai-evaluation/experiment/results/go/identify_bug/original.txt` | success |
| 4 | `identify_bug` | sanitized | `aeaef13861f5cc6b6` | 0 | `ai-evaluation/experiment/results/go/identify_bug/sanitized.txt` | success |
| 5 | `security_analysis` | original | `ada462fa9ba7cef1f` | 0 | `ai-evaluation/experiment/results/go/security_analysis/original.txt` | success |
| 6 | `security_analysis` | sanitized | `a91bb02989913c1ec` | 0 | `ai-evaluation/experiment/results/go/security_analysis/sanitized.txt` | success |
| 7 | `generate_unit_tests` | original | `a23f5026a721b11fd` | 0 | `ai-evaluation/experiment/results/go/generate_unit_tests/original.txt` | success |
| 8 | `generate_unit_tests` | sanitized | `a23f48bef1d691087` | 0 | `ai-evaluation/experiment/results/go/generate_unit_tests/sanitized.txt` | success |
| 9 | `suggest_refactoring` | original | `a6e689223e38d7ee1` | 0 | `ai-evaluation/experiment/results/go/suggest_refactoring/original.txt` | success |
| 10 | `suggest_refactoring` | sanitized | `ae273a9bf879a036f` | 0 | `ai-evaluation/experiment/results/go/suggest_refactoring/sanitized.txt` | success |

All 10 rows share `file: go/config.go`.

## Isolation confirmation

- **10 distinct subagent ids**, zero tool calls in every session.
- Each `original`/`sanitized` pair used a different subagent id.

## Protocol deviation — flagged, response preserved unchanged, high confidence

**Response #1 (`explain_code`, original condition) contains the
sentence:** *"This is clearly a test fixture designed for something like
a credential-scanning or secret-detection tool (matching the
'New-credential-scrubber' project this lives in)..."*

This is an exact, verbatim match to this repository's actual project
directory name, `New-credential-scrubber`. The prompt given to this
session contained only the task template and raw file content — no
project name, no path, no mention of "credential-scrubber" in any form —
and the session reported `tool_uses: 0`, so it did not read any file or
explore the repository to learn this.

**Confidence assessment:** unlike Batch 4's "website" observation (a
generic word also explicable as ordinary security-review phrasing), this
is the same high-confidence pattern already documented in Batch 2's
`batch_record.md` — an exact, distinctive, hyphenated project name that
is not plausible as coincidental or generic phrasing. Recorded here with
high confidence that this reflects the same ambient
working-directory/session-metadata exposure already identified as a
structural property of the Claude Code subagent tooling, not something
caused by this batch's prompts (which were, as always, self-contained
task template + file content only).

**Per instruction: the response was not edited, not regenerated, and
this deviation did not prevent the response from being collected under
the frozen protocol** — `explain_code/original.txt` is saved complete
and unedited, including this sentence. No cell was re-run.

**Scope:** exactly 1 of 10 responses; the other 9, including this same
task's *sanitized* condition, contain no reference to the project name,
"credential-scrubber," the experiment, or the other condition.

## Settings

Same as all prior pilots/batches (carried forward, not re-decided):
temperature and max-output-tokens not independently controllable;
platform default applied identically and by omission to all 10
sessions. No conversation history; one response per condition, no
repeated sampling.

## What this record deliberately does not contain

No quality assessment of any response, no comparison between the
original and sanitized conditions, no rubric scores, and no conclusion
about whether sanitization helped or hurt for any of these 5 tasks.
`human_evaluation.md` for this batch has not been created — scoring is a
separate, later step.
