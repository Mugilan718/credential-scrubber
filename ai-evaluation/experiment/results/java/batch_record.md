# Batch 1 record — `java/Config.java`, 5 tasks × 2 conditions

**Status: 10/10 responses collected. Not scored. No LLM judge used.**
Procedural record only — no quality assessment, no comparison, no
conclusion. Scoring is a separate, later step against
`ai-evaluation/rubric/rubric.md`.

## Frozen scope confirmation

Verified against `ai-evaluation/experiment/manifest.json` before starting
(unchanged since the prior freeze/verification step): `java/Config.java`
is applicable for exactly these 5 tasks — `explain_code`, `identify_bug`,
`security_analysis`, `generate_unit_tests`, `suggest_refactoring` —
and `explain_config_relationships` is `not_applicable` for this file
(out of that task's own documented scope: source code, not a config
file). `explain_config_relationships` was **not** run for this file, per
the frozen manifest.

## Model

Claude, model id `claude-sonnet-5` ("Sonnet 5") — the model backing this
Claude Code session. All 10 responses were collected as fresh
`general-purpose` Claude Code subagent invocations (via the Agent tool)
with no `model` override, so each inherited the parent session's model.
As with Pilot 001/002, this tooling does not return an explicit model-id
confirmation string per call — recorded as "inherited from the parent
session," consistent with prior pilot records.

## Sanitized fixture source

`ai-evaluation/pilot/sanitized/java/Config.java` — the existing,
already-engine-generated fixture from Pilot 001. **Not regenerated** for
this batch, per instruction — located from the frozen experiment
configuration (`manifest.json`'s `sanitized_fixture_generation_method`
references this exact file as the Pilot 001 precedent for
`java/Config.java`).

## Execution date

2026-09-20T14:04:59Z (UTC) — all 10 sessions launched as independent,
parallel tool invocations within the same short window.

## Responses

| # | Task | Condition | Subagent id | Tool calls | Response file | Status |
|---|---|---|---|---:|---|---|
| 1 | `explain_code` | original | `a343d910ac319eb46` | 0 | `ai-evaluation/experiment/results/java/explain_code/original.txt` | success |
| 2 | `explain_code` | sanitized | `a92db702e813c064f` | 0 | `ai-evaluation/experiment/results/java/explain_code/sanitized.txt` | success |
| 3 | `identify_bug` | original | `a7cf39e9f7133a6aa` | 0 | `ai-evaluation/experiment/results/java/identify_bug/original.txt` | success |
| 4 | `identify_bug` | sanitized | `ae9ace31764f5a44a` | 0 | `ai-evaluation/experiment/results/java/identify_bug/sanitized.txt` | success |
| 5 | `security_analysis` | original | `a3fa8b09562b552d5` | 0 | `ai-evaluation/experiment/results/java/security_analysis/original.txt` | success |
| 6 | `security_analysis` | sanitized | `af699e8d4b5a42e35` | 0 | `ai-evaluation/experiment/results/java/security_analysis/sanitized.txt` | success |
| 7 | `generate_unit_tests` | original | `a365d337f89ec68b6` | 0 | `ai-evaluation/experiment/results/java/generate_unit_tests/original.txt` | success |
| 8 | `generate_unit_tests` | sanitized | `a0c48265e0d23230f` | 0 | `ai-evaluation/experiment/results/java/generate_unit_tests/sanitized.txt` | success |
| 9 | `suggest_refactoring` | original | `a4ccbe2cb6e6ba94c` | 0 | `ai-evaluation/experiment/results/java/suggest_refactoring/original.txt` | success |
| 10 | `suggest_refactoring` | sanitized | `a7c5966a54258d746` | 0 | `ai-evaluation/experiment/results/java/suggest_refactoring/sanitized.txt` | success |

All 10 rows share `file: java/Config.java`.

## Isolation confirmation

- **10 distinct subagent ids** — no session was reused across rows, no
  session's prompt referenced another row's file, task, or condition.
- **Zero tool calls in every one of the 10 sessions** — each response was
  generated purely from its own prompt text (task template + the one
  file's content, embedded directly), confirming no repository
  exploration, no access to the other condition, and no access to this
  manifest, the rubric, or any other evaluation file.
- **No session was told** this is an experiment, what Credential
  Scrubber is, that the source was sanitized, what the placeholder tokens
  mean, or that an original/sanitized comparison exists — every prompt
  was the task template's own wording plus the file content, nothing
  else.
- Each `original`/`sanitized` pair for the same task used a different
  subagent id, confirming the two conditions were never run in the same
  conversation.

## Settings

Same as Pilot 001/002 (carried forward, not re-decided): temperature and
max-output-tokens are not independently controllable via the available
subagent tooling; the platform default applied identically and by
omission to all 10 sessions. No conversation history in any session; one
response per condition, no repeated sampling.

## Procedural deviations

None. All 10 sessions completed successfully on the first attempt,
returned complete responses matching each task template's requested
format, and reported zero tool calls. No file was regenerated, no prompt
was modified, no session saw content beyond its own single task template
and single source file.

## What this record deliberately does not contain

No quality assessment of any response, no comparison between the
original and sanitized conditions, no rubric scores, and no conclusion
about whether sanitization helped or hurt for any of these 5 tasks.
`human_evaluation.md` for this batch has not been created — scoring is a
separate, later step.
