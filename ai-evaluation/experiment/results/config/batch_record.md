# Batch 7 record — `config/appsettings.json`, 6 tasks × 2 conditions

**Status: 12/12 responses collected. Not scored. No LLM judge used.**
Procedural record only — no quality assessment, no comparison, no
conclusion. Scoring is a separate, later step against
`ai-evaluation/rubric/rubric.md`.

## Methodological problem encountered before execution — stopped and reported, resolved by user decision

This batch's instructions stated: *"the frozen experiment manifest
defines `explain_config_relationships` as not applicable to
source-code/config cells"* (implying `not_applicable` for
`config/appsettings.json`).

**This contradicted the actual frozen `ai-evaluation/experiment/manifest.json`**,
whose `task_applicability_matrix.explain_config_relationships` entry
explicitly marks `config/appsettings.json` as `"applicable"` (along with
`config/settings.yaml` and `edge_cases/false_positives.properties`) —
`not_applicable` is reserved only for the 6 *source-code* files
(java/python/javascript/typescript/go/csharp), each annotated "out of
the template's documented scope (source code, not a config file)." The
manifest was re-read before execution and confirmed unchanged since it
was frozen.

Per the standing "stop and report a methodological problem instead of
improvising" instruction, I did not proceed on either interpretation
unilaterally. I asked the user how to resolve the discrepancy; they
selected **"Follow the actual frozen manifest.json."** Accordingly, this
batch ran **all 6 applicable tasks** for `config/appsettings.json`
(including `explain_config_relationships`), producing **12 responses**
instead of the 10 the batch instructions' task list implied. This
matches `manifest.json`'s own applicability determination exactly, and
matches what Pilot 002 already did for this same file/task pair.

**Experiment progress note:** this batch therefore contributes 12
responses toward the 96-applicable-cell total, not 10. Prior batches'
progress counters (60/96 before this batch) assumed 10 per file for the
6 source-code files, which is correct for those files (`explain_config_relationships`
is genuinely `not_applicable` for all of them) — `config/appsettings.json`
is the first of the 3 config-shaped files in the population and is where
the count-per-file legitimately rises to 12. This does not change the
frozen 96-cell total itself, only how many of those 96 responses come
from this one file.

## Frozen scope confirmation (for the record)

`config/appsettings.json` is applicable for all 6 tasks per the actual
manifest: `explain_code`, `identify_bug`, `security_analysis`,
`generate_unit_tests`, `suggest_refactoring`, **and**
`explain_config_relationships`.

## Model

Claude, model id `claude-sonnet-5` ("Sonnet 5"). All 12 responses were
collected as fresh `general-purpose` Claude Code subagent invocations
(via the Agent tool) with no `model` override, so each inherited the
parent session's model — recorded as "inherited from the parent
session," consistent with all prior pilots/batches.

## Sanitized fixture source

`ai-evaluation/experiment/sanitized/config/appsettings.json` — the
frozen fixture generated and validated in the earlier preparation step
(identical to Pilot 002's sanitized fixture for this same file). **Not
regenerated, not modified** for this batch — `engine.scan_project()` was
not called at any point during this batch.

## Execution date

2026-09-21T15:38:58Z (UTC) — all 12 sessions launched as independent,
parallel tool invocations within the same short window.

## Responses

| # | Task | Condition | Subagent id | Tool calls | Response file | Status |
|---|---|---|---|---:|---|---|
| 1 | `explain_code` | original | `aa1d70218df444437` | 0 | `ai-evaluation/experiment/results/config/explain_code/original.txt` | success |
| 2 | `explain_code` | sanitized | `acf75d4aa04ccfbfe` | 0 | `ai-evaluation/experiment/results/config/explain_code/sanitized.txt` | success |
| 3 | `identify_bug` | original | `a35095096674b543f` | 0 | `ai-evaluation/experiment/results/config/identify_bug/original.txt` | success |
| 4 | `identify_bug` | sanitized | `a0c43ef1c9a700ab6` | 0 | `ai-evaluation/experiment/results/config/identify_bug/sanitized.txt` | success |
| 5 | `security_analysis` | original | `a9dc450bcc6a42ec0` | 0 | `ai-evaluation/experiment/results/config/security_analysis/original.txt` | success |
| 6 | `security_analysis` | sanitized | `a1071ae4eca8d0e2c` | 0 | `ai-evaluation/experiment/results/config/security_analysis/sanitized.txt` | success |
| 7 | `generate_unit_tests` | original | `a9342a33e52f6b685` | 0 | `ai-evaluation/experiment/results/config/generate_unit_tests/original.txt` | success |
| 8 | `generate_unit_tests` | sanitized | `a3912346a4c5175f7` | 0 | `ai-evaluation/experiment/results/config/generate_unit_tests/sanitized.txt` | success |
| 9 | `suggest_refactoring` | original | `a6536ad83a7a85ae8` | 0 | `ai-evaluation/experiment/results/config/suggest_refactoring/original.txt` | success |
| 10 | `suggest_refactoring` | sanitized | `a884777606c95a1df` | 0 | `ai-evaluation/experiment/results/config/suggest_refactoring/sanitized.txt` | success |
| 11 | `explain_config_relationships` | original | `accd2ec2a5710426b` | 0 | `ai-evaluation/experiment/results/config/explain_config_relationships/original.txt` | success |
| 12 | `explain_config_relationships` | sanitized | `a5af754f6ce3b9b60` | 0 | `ai-evaluation/experiment/results/config/explain_config_relationships/sanitized.txt` | success |

All 12 rows share `file: config/appsettings.json`.

## Isolation confirmation

- **12 distinct subagent ids**, zero tool calls in every session.
- Each `original`/`sanitized` pair used a different subagent id.
- No session's prompt mentioned the experiment, Credential Scrubber,
  sanitization, placeholders, or the other condition.

## Protocol deviations

**None detected.** No response mentions `New-credential-scrubber`,
"Credential Scrubber," "website," any repository/project name,
working-directory/path information, or the other condition.

The sanitized-condition `explain_code` response independently noted the
`<PLACEHOLDER>`-style bracket notation and inferred these "are already
redacted/templated placeholders, which supports the 'template'
interpretation" — a generic, correct, unprompted observation from the
visible JSON syntax alone, not a reference to anything outside the
supplied prompt/source. Consistent with the "generic observations...
unless they reveal information unavailable from the supplied
prompt/source" guidance — not counted as a deviation.

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
