# Batch 2 record — `python/config.py`, 5 tasks × 2 conditions

**Status: 10/10 responses collected. Not scored. No LLM judge used.**
Procedural record only — no quality assessment, no comparison, no
conclusion. Scoring is a separate, later step against
`ai-evaluation/rubric/rubric.md`.

## Frozen scope confirmation

Verified against `ai-evaluation/experiment/manifest.json` before
starting (unchanged since the prior freeze/verification step):
`python/config.py` is applicable for exactly these 5 tasks —
`explain_code`, `identify_bug`, `security_analysis`,
`generate_unit_tests`, `suggest_refactoring` — and
`explain_config_relationships` is `not_applicable` for this file (out of
that task's own documented scope: source code, not a config file).
`explain_config_relationships` was **not** run for this file, per the
frozen manifest.

## Model

Claude, model id `claude-sonnet-5` ("Sonnet 5") — the model backing this
Claude Code session. All 10 responses were collected as fresh
`general-purpose` Claude Code subagent invocations (via the Agent tool)
with no `model` override, so each inherited the parent session's model.
As with Pilot 001/002 and Batch 1, this tooling does not return an
explicit model-id confirmation string per call — recorded as "inherited
from the parent session."

## Sanitized fixture source

`ai-evaluation/experiment/sanitized/python/config.py` — the frozen
fixture generated and validated in the prior preparation step (isolated
single-file `engine.scan_project(..., placeholder_mode=True)` scan).
**Not regenerated** for this batch — `engine.scan_project()` was not
called at any point during this batch.

## Execution date

2026-09-21T14:08:49Z (UTC) — all 10 sessions launched as independent,
parallel tool invocations within the same short window.

## Responses

| # | Task | Condition | Subagent id | Tool calls | Response file | Status |
|---|---|---|---|---:|---|---|
| 1 | `explain_code` | original | `a120c9d280d0c3e6e` | 0 | `ai-evaluation/experiment/results/python/explain_code/original.txt` | success (see protocol deviation below) |
| 2 | `explain_code` | sanitized | `a60bf819e8a650d65` | 0 | `ai-evaluation/experiment/results/python/explain_code/sanitized.txt` | success |
| 3 | `identify_bug` | original | `abb1bff679afab918` | 0 | `ai-evaluation/experiment/results/python/identify_bug/original.txt` | success |
| 4 | `identify_bug` | sanitized | `ada9457810878f04c` | 0 | `ai-evaluation/experiment/results/python/identify_bug/sanitized.txt` | success |
| 5 | `security_analysis` | original | `aad1dfff0d59ad7d5` | 0 | `ai-evaluation/experiment/results/python/security_analysis/original.txt` | success |
| 6 | `security_analysis` | sanitized | `a554ed468d3269d9a` | 0 | `ai-evaluation/experiment/results/python/security_analysis/sanitized.txt` | success |
| 7 | `generate_unit_tests` | original | `a4ccb398e0c38be64` | 0 | `ai-evaluation/experiment/results/python/generate_unit_tests/original.txt` | success |
| 8 | `generate_unit_tests` | sanitized | `af74689f0941a9586` | 0 | `ai-evaluation/experiment/results/python/generate_unit_tests/sanitized.txt` | success |
| 9 | `suggest_refactoring` | original | `a60e0d6930b3e3187` | 0 | `ai-evaluation/experiment/results/python/suggest_refactoring/original.txt` | success |
| 10 | `suggest_refactoring` | sanitized | `ad656343553845358` | 0 | `ai-evaluation/experiment/results/python/suggest_refactoring/sanitized.txt` | success |

All 10 rows share `file: python/config.py`.

## Isolation confirmation

- **10 distinct subagent ids** — no session was reused across rows, no
  session's prompt referenced another row's file, task, or condition.
- **Zero tool calls in every one of the 10 sessions** — each response was
  generated purely from its own prompt text (task template + the one
  file's content, embedded directly).
- **No session's prompt mentioned** this is an experiment, Credential
  Scrubber, that the source was sanitized, what placeholders were
  generated or mean, or that an original/sanitized comparison exists —
  every prompt was the task template's own wording plus the file
  content, nothing else.
- Each `original`/`sanitized` pair for the same task used a different
  subagent id, confirming the two conditions were never run in the same
  conversation.

## Protocol deviation — flagged, not corrected mid-run

**Response #1 (`explain_code`, original condition) spontaneously
referenced the project's identity.** Its answer includes the sentence:
*"...this pattern (env var with hardcoded fallback, bare string literal,
multi-line concatenated string) is likely designed to exercise a
credential-scanning or secret-detection tool (consistent with the
working directory name `New-credential-scrubber`)..."*

This was **not** caused by anything in the prompt — the prompt given to
that session contained only the task template and the raw file content,
identical in structure to the other 9 prompts, none of which produced
this. The most likely explanation is that the Claude Code subagent
environment automatically exposes baseline session metadata (including
the working directory path) to every subagent regardless of prompt
content, independent of tool use (this session, like all 10, reported
`tool_uses: 0` — it did not read any file or explore the repository to
learn this; the working directory name appears to be ambient context the
subagent runtime provides). Because this repository's working directory
literally contains the string "credential-scrubber", the subagent was
able to name the project without violating the "no repository
exploration" isolation rule in the mechanical sense (no tool call
occurred), but it did violate the *intent* of "do not mention Credential
Scrubber" / "do not mention the experiment."

**This was not detected until after all 10 (parallel) sessions had
already completed**, so it could not be caught and corrected mid-run
without violating "do not improvise" — reporting it now, unmodified,
rather than editing the response or re-running that one cell, per the
explicit instruction to stop and report rather than change methodology.
The response itself (`explain_code/original.txt`) has been saved
completely and unedited, including this sentence — no content was
removed or altered.

**Scope of the deviation:** exactly 1 of 10 responses. The other 9
(including `explain_code`'s own *sanitized* condition) contain no
reference to Credential Scrubber, the experiment, or the working
directory. This is a structural limitation of the subagent tooling
(also already noted in Pilot 001/002's execution records as "the AI
agent evaluated is a Claude Code subagent, not a bare provider API
call"), not a prompt-design mistake — no wording in any of the 10
prompts differed in a way that would explain why only this one session
produced this observation.

## Settings

Same as Pilot 001/002/Batch 1 (carried forward, not re-decided):
temperature and max-output-tokens are not independently controllable via
the available subagent tooling; the platform default applied identically
and by omission to all 10 sessions. No conversation history in any
session; one response per condition, no repeated sampling.

## Other procedural notes

Unlike Batch 1, each of these 10 subagent results was wrapped by the
harness in a "[Subagent hand-back]" provenance notice framing the
content as untrusted model output. This wrapper (and the trailing
`agentId:`/`usage` metadata line) was stripped before saving — only the
actual response text between those markers was written to each
`.txt` file, matching Batch 1's save format exactly.

## What this record deliberately does not contain

No quality assessment of any response, no comparison between the
original and sanitized conditions, no rubric scores, and no conclusion
about whether sanitization helped or hurt for any of these 5 tasks.
`human_evaluation.md` for this batch has not been created — scoring is a
separate, later step.
