# Batch 3 record — `javascript/config.js`, 5 tasks × 2 conditions

**Status: 10/10 responses collected. Not scored. No LLM judge used.**
Procedural record only — no quality assessment, no comparison, no
conclusion. Scoring is a separate, later step against
`ai-evaluation/rubric/rubric.md`.

## Frozen scope confirmation

Verified against `ai-evaluation/experiment/manifest.json` before
starting (unchanged since the prior freeze/verification step):
`javascript/config.js` is applicable for exactly these 5 tasks —
`explain_code`, `identify_bug`, `security_analysis`,
`generate_unit_tests`, `suggest_refactoring` — and
`explain_config_relationships` is `not_applicable` for this file (out of
that task's own documented scope: source code, not a config file).
`explain_config_relationships` was **not** run for this file.

## Model

Claude, model id `claude-sonnet-5` ("Sonnet 5") — the model backing this
Claude Code session. All 10 responses were collected as fresh
`general-purpose` Claude Code subagent invocations (via the Agent tool)
with no `model` override, so each inherited the parent session's model.
As with prior pilots/batches, this tooling does not return an explicit
model-id confirmation string per call — recorded as "inherited from the
parent session."

## Sanitized fixture source

`ai-evaluation/experiment/sanitized/javascript/config.js` — the frozen
fixture generated and validated in the prior preparation step. **Not
regenerated** for this batch — `engine.scan_project()` was not called at
any point during this batch.

## Execution date

2026-09-21T15:22:39Z (UTC) — all 10 sessions launched as independent,
parallel tool invocations within the same short window.

## Responses

| # | Task | Condition | Subagent id | Tool calls | Response file | Status |
|---|---|---|---|---:|---|---|
| 1 | `explain_code` | original | `a228a559994b24f8f` | 0 | `ai-evaluation/experiment/results/javascript/explain_code/original.txt` | success |
| 2 | `explain_code` | sanitized | `abf6367224d246c54` | 0 | `ai-evaluation/experiment/results/javascript/explain_code/sanitized.txt` | success |
| 3 | `identify_bug` | original | `a6f1dcbdadcdf5a9b` | 0 | `ai-evaluation/experiment/results/javascript/identify_bug/original.txt` | success |
| 4 | `identify_bug` | sanitized | `a5d750a57a86a7c16` | 0 | `ai-evaluation/experiment/results/javascript/identify_bug/sanitized.txt` | success |
| 5 | `security_analysis` | original | `ae8630f228b2a1414` | 0 | `ai-evaluation/experiment/results/javascript/security_analysis/original.txt` | success |
| 6 | `security_analysis` | sanitized | `a7c917e62f2cce576` | 0 | `ai-evaluation/experiment/results/javascript/security_analysis/sanitized.txt` | success |
| 7 | `generate_unit_tests` | original | `a29bd4fb970bea69f` | 0 | `ai-evaluation/experiment/results/javascript/generate_unit_tests/original.txt` | success |
| 8 | `generate_unit_tests` | sanitized | `ac0a1dc98190ab0a2` | 0 | `ai-evaluation/experiment/results/javascript/generate_unit_tests/sanitized.txt` | success |
| 9 | `suggest_refactoring` | original | `a446934f638807ba6` | 0 | `ai-evaluation/experiment/results/javascript/suggest_refactoring/original.txt` | success |
| 10 | `suggest_refactoring` | sanitized | `af8de7fefcc136e19` | 0 | `ai-evaluation/experiment/results/javascript/suggest_refactoring/sanitized.txt` | success |

All 10 rows share `file: javascript/config.js`.

## Isolation confirmation

- **10 distinct subagent ids** — no session was reused across rows, no
  session's prompt referenced another row's file, task, or condition.
- **Zero tool calls in every one of the 10 sessions.**
- **No session's prompt mentioned** this is an experiment, Credential
  Scrubber, that the source was sanitized, what placeholders were
  generated or mean, or that an original/sanitized comparison exists.
- Each `original`/`sanitized` pair for the same task used a different
  subagent id.

## Protocol deviations

**None detected in this batch.** Per the working directory / environment
control note for this batch, no attempt was made to expose, rename, or
otherwise manipulate the working directory. None of the 10 responses
mention "Credential Scrubber," the working directory name, the
experiment, or the other condition. (For contrast, see Batch 2's
`batch_record.md`, which documents one such deviation in a different
response.)

Two responses (`explain_code`/sanitized and `generate_unit_tests`/
sanitized) spontaneously used their own neutral, unprompted language to
describe the sanitized values as being generated/redacted from a
template ("this file was itself auto-generated/redacted from a
template", "a fixture for testing something *external* (e.g., a
credential/secret scanner)") — this is the model's own inference from
the visible `<...>` syntax and the file's pre-existing header comment,
not something I told it, and does not name any specific product or use
the word "Credential Scrubber." Consistent with the same pattern already
observed and expected per Pilot 001/002's execution records (spontaneous
recognition of placeholder syntax is anticipated, not suppressed). Not
counted as a protocol deviation.

## Settings

Same as all prior pilots/batches (carried forward, not re-decided):
temperature and max-output-tokens are not independently controllable via
the available subagent tooling; the platform default applied identically
and by omission to all 10 sessions. No conversation history in any
session; one response per condition, no repeated sampling.

## What this record deliberately does not contain

No quality assessment of any response, no comparison between the
original and sanitized conditions, no rubric scores, and no conclusion
about whether sanitization helped or hurt for any of these 5 tasks.
`human_evaluation.md` for this batch has not been created — scoring is a
separate, later step.
