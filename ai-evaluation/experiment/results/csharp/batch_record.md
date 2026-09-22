# Batch 6 record — `csharp/Config.cs`, 5 tasks × 2 conditions

**Status: 10/10 responses collected. Not scored. No LLM judge used.**
Procedural record only — no quality assessment, no comparison, no
conclusion. Scoring is a separate, later step against
`ai-evaluation/rubric/rubric.md`.

## Frozen scope confirmation

`csharp/Config.cs` is applicable for exactly these 5 tasks —
`explain_code`, `identify_bug`, `security_analysis`,
`generate_unit_tests`, `suggest_refactoring` — and
`explain_config_relationships` is `not_applicable` per the frozen
manifest (source code, not a config file). `explain_config_relationships`
was **not** run.

## Model

Claude, model id `claude-sonnet-5` ("Sonnet 5"). All 10 responses were
collected as fresh `general-purpose` Claude Code subagent invocations
(via the Agent tool) with no `model` override, so each inherited the
parent session's model — recorded as "inherited from the parent
session," consistent with all prior pilots/batches.

## Sanitized fixture source

`ai-evaluation/experiment/sanitized/csharp/Config.cs` — the frozen
fixture generated and validated in the earlier preparation step. **Not
regenerated** for this batch — `engine.scan_project()` was not called at
any point during this batch.

## Execution date

2026-09-21T15:34:01Z (UTC) — all 10 sessions launched as independent,
parallel tool invocations within the same short window.

## Responses

| # | Task | Condition | Subagent id | Tool calls | Response file | Status |
|---|---|---|---|---:|---|---|
| 1 | `explain_code` | original | `a61b300124cd80083` | 0 | `ai-evaluation/experiment/results/csharp/explain_code/original.txt` | success |
| 2 | `explain_code` | sanitized | `a7e03c9389951b040` | 0 | `ai-evaluation/experiment/results/csharp/explain_code/sanitized.txt` | success |
| 3 | `identify_bug` | original | `a9b880a4435b7d714` | 0 | `ai-evaluation/experiment/results/csharp/identify_bug/original.txt` | success |
| 4 | `identify_bug` | sanitized | `afdb602780b4e30f8` | 0 | `ai-evaluation/experiment/results/csharp/identify_bug/sanitized.txt` | success |
| 5 | `security_analysis` | original | `ad6df8b50aaa70d76` | 0 | `ai-evaluation/experiment/results/csharp/security_analysis/original.txt` | success |
| 6 | `security_analysis` | sanitized | `af7d3fba4a2ed87ab` | 0 | `ai-evaluation/experiment/results/csharp/security_analysis/sanitized.txt` | success |
| 7 | `generate_unit_tests` | original | `a3da1762792cf7e9b` | 0 | `ai-evaluation/experiment/results/csharp/generate_unit_tests/original.txt` | success |
| 8 | `generate_unit_tests` | sanitized | `a0bcdeecac68ad61d` | 0 | `ai-evaluation/experiment/results/csharp/generate_unit_tests/sanitized.txt` | success |
| 9 | `suggest_refactoring` | original | `aa6b9cda7dcf64d03` | 0 | `ai-evaluation/experiment/results/csharp/suggest_refactoring/original.txt` | success |
| 10 | `suggest_refactoring` | sanitized | `a655fe1ec8b392a7f` | 0 | `ai-evaluation/experiment/results/csharp/suggest_refactoring/sanitized.txt` | success |

All 10 rows share `file: csharp/Config.cs`.

## Isolation confirmation

- **10 distinct subagent ids**, zero tool calls in every session.
- Each `original`/`sanitized` pair used a different subagent id.
- No session's prompt mentioned the experiment, Credential Scrubber,
  sanitization, placeholders, or the other condition.

## Protocol deviations

**None detected.** No response in this batch mentions
`New-credential-scrubber`, "Credential Scrubber," "website," any
repository/project name, working-directory/path information, the
experiment, or the other condition.

One response (`security_analysis`/sanitized) made a generic, unprompted
observation that the `+ "" + ""` concatenation pattern "is a common
artifact of automated secret-scrubbing/obfuscation tooling and can
indicate that a real secret was mechanically split/replaced" — this
correctly infers the mechanism from the visible placeholder syntax
(`<API_KEY_1>`, `<ACCESS_TOKEN_1>`) without naming any specific product,
tool, or repository. Consistent with the same expected,
already-documented pattern from Pilot 001/002 and prior batches
(spontaneous recognition of placeholder syntax is anticipated, not
suppressed, and does not by itself name anything that wasn't visible in
the prompt). Not counted as a deviation.

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
