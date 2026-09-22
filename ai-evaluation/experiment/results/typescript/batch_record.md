# Batch 4 record — `typescript/auth.ts`, 5 tasks × 2 conditions

**Status: 10/10 responses collected. Not scored. No LLM judge used.**
Procedural record only — no quality assessment, no comparison, no
conclusion. Scoring is a separate, later step against
`ai-evaluation/rubric/rubric.md`.

## Frozen scope confirmation

`typescript/auth.ts` is applicable for exactly these 5 tasks —
`explain_code`, `identify_bug`, `security_analysis`,
`generate_unit_tests`, `suggest_refactoring` — and
`explain_config_relationships` is `not_applicable` for this file per the
frozen manifest (source code, not a config file).
`explain_config_relationships` was **not** run.

## Model

Claude, model id `claude-sonnet-5` ("Sonnet 5"). All 10 responses were
collected as fresh `general-purpose` Claude Code subagent invocations
(via the Agent tool) with no `model` override, so each inherited the
parent session's model — recorded as "inherited from the parent
session," consistent with all prior pilots/batches.

## Sanitized fixture source

`ai-evaluation/experiment/sanitized/typescript/auth.ts` — the frozen
fixture generated and validated in the earlier preparation step. **Not
regenerated** for this batch — `engine.scan_project()` was not called at
any point during this batch.

## Execution date

2026-09-21T15:26:30Z (UTC) — all 10 sessions launched as independent,
parallel tool invocations within the same short window.

## Environmental-control compliance

No attempt was made to expose, rename, or manipulate the working
directory for this batch, per the instruction. See "Protocol deviations"
below for one response that may reflect ambient environment leakage
despite this.

## Responses

| # | Task | Condition | Subagent id | Tool calls | Response file | Status |
|---|---|---|---|---:|---|---|
| 1 | `explain_code` | original | `ad3f19fdfd38f95ba` | 0 | `ai-evaluation/experiment/results/typescript/explain_code/original.txt` | success |
| 2 | `explain_code` | sanitized | `aabf8101b8aa13d42` | 0 | `ai-evaluation/experiment/results/typescript/explain_code/sanitized.txt` | success |
| 3 | `identify_bug` | original | `af5be3ea24f4118cc` | 0 | `ai-evaluation/experiment/results/typescript/identify_bug/original.txt` | success |
| 4 | `identify_bug` | sanitized | `ae65f6a8f6f28762e` | 0 | `ai-evaluation/experiment/results/typescript/identify_bug/sanitized.txt` | success |
| 5 | `security_analysis` | original | `a4d9a25c459ac790d` | 0 | `ai-evaluation/experiment/results/typescript/security_analysis/original.txt` | success (see protocol deviation below) |
| 6 | `security_analysis` | sanitized | `a62a9bd9b3a50b8dd` | 0 | `ai-evaluation/experiment/results/typescript/security_analysis/sanitized.txt` | success |
| 7 | `generate_unit_tests` | original | `a20c5692f8b14651d` | 0 | `ai-evaluation/experiment/results/typescript/generate_unit_tests/original.txt` | success |
| 8 | `generate_unit_tests` | sanitized | `a64a1354ceff3ef16` | 0 | `ai-evaluation/experiment/results/typescript/generate_unit_tests/sanitized.txt` | success |
| 9 | `suggest_refactoring` | original | `a791a5f41979faf35` | 0 | `ai-evaluation/experiment/results/typescript/suggest_refactoring/original.txt` | success |
| 10 | `suggest_refactoring` | sanitized | `a6340ea2f619c8ee0` | 0 | `ai-evaluation/experiment/results/typescript/suggest_refactoring/sanitized.txt` | success |

All 10 rows share `file: typescript/auth.ts`.

## Isolation confirmation

- **10 distinct subagent ids**, zero tool calls in every session.
- **No session's prompt mentioned** the experiment, Credential Scrubber,
  sanitization, placeholders, or the other condition.
- Each `original`/`sanitized` pair used a different subagent id.

## Protocol deviation — flagged, response preserved unchanged

**Response #5 (`security_analysis`, original condition) contains the
phrase:** *"if this file is part of a `website` project and ever gets
imported into client-side/browser-bundled code, the 'secret' ships to
every visitor..."*

This session's Claude Code working directory is
`D:\New-credential-scrubber\website` — the word "website" matches the
actual working directory's final path component exactly. This is the
same category of concern as the deviation documented in Batch 2's
`batch_record.md` (where a session named the parent directory
`New-credential-scrubber`): the prompt given to this session contained
only the task template and raw file content, with no mention of
"website," any project name, or any path — and, as with all 10 sessions
in this batch, it reported `tool_uses: 0`, so it did not read any file
or explore the repository to learn this.

**This is reported with appropriate uncertainty, not asserted as
certain:** unlike Batch 2's case (where the exact, full,
hyphen-for-hyphen project name `New-credential-scrubber` appeared,
leaving little room for alternative explanation), "website" is also a
generic, plausible word a security reviewer would naturally reach for
when describing client-side/browser exposure risk, independent of any
awareness of this specific repository. It is not possible to determine
with confidence whether this is (a) another instance of the same
ambient-working-directory-leakage pattern documented in Batch 2, or (b)
coincidental generic phrasing. Flagged here rather than silently passed
over, consistent with the instruction to document any such occurrence
regardless of certainty.

**Per instruction: the response was not edited, not regenerated, and
this deviation did not prevent the response from being collected under
the frozen protocol** — `security_analysis/original.txt` is saved
complete and unedited, including this sentence.

**Scope:** exactly 1 of 10 responses shows this pattern; the other 9,
including this same task's *sanitized* condition, contain no reference
to "website," "credential-scrubber," the experiment, or any other
apparent environment leak.

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
