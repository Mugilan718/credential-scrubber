# Frozen experiment — Credential Scrubber AI evaluation (9 files × 6 tasks × 2 conditions)

**Status: completed.** This directory defines the full experimental
population, task set, and isolation rules for the AI evaluation, and now
also contains the completed run: 96 applicable responses collected (48
Original, 48 Sanitized, across 48 paired file/task comparisons), all
human-scored against the frozen rubric, with completed descriptive and
inferential statistical analysis. No LLM judge was used anywhere in this
experiment - all scoring is by a human rater. See `manifest.json` for the
machine-readable frozen design and completion status, `validation_report.md`
for the per-file engine validation this freeze was built on, `results/`
for the raw responses and human evaluations, and `analysis/` for the
descriptive analysis, inferential analysis, and results-and-discussion
write-up.

**Summary of what was executed:**
- 96 responses collected (48 Original / 48 Sanitized / 48 paired comparisons) - see `collection_integrity_audit.md`.
- Human scoring completed for all 96 responses against `../rubric/rubric.md` - see `scoring_integrity_audit.md`.
- Descriptive analysis completed - `analysis/descriptive_results.md`.
- Inferential analysis completed - `analysis/inferential_results.md`.

## Research objective

> Can sensitive source-code values be sanitized before providing source
> code to an AI coding agent while preserving enough semantic information
> for the AI to perform useful software-engineering tasks?

(Verbatim from `ai-evaluation/README.md`.) This experiment measures a
*delta* between two conditions on the same files and tasks — never a
standalone score on either condition, and never a claim that sanitization
"works" in general from any single result.

## Experiment design

A full factorial design: every one of the 9 frozen files is run against
every one of the 6 frozen tasks, in both conditions —

```
9 files × 6 tasks × 2 conditions = 108 (nominal grid, frozen in manifest.json)
```

One task (`explain_config_relationships`) is out of scope, by its own
documented design, for the 6 source-code files (see "What differs" and
`manifest.json`'s `task_applicability_matrix`), so the number of cells
actually executed is 96, not 108 — both numbers are recorded explicitly
in `manifest.json` rather than silently collapsing one into the other.

## Frozen population (9 files)

Taken as-is from `ai-evaluation/dataset/README.md`'s existing candidate
list — no substitution, no new files created:

| # | File | Language | Role |
|---|---|---|---|
| 1 | `java/Config.java` | Java | Multi-value code file, incl. multiline concatenation (also Pilot 001) |
| 2 | `python/config.py` | Python | Multi-value code file, incl. `os.getenv` and multiline concatenation |
| 3 | `javascript/config.js` | JavaScript | Multi-value code file, incl. multiline concatenation |
| 4 | `typescript/auth.ts` | TypeScript | Typed declarations; exercises the value-pattern (not key-name) detection path |
| 5 | `go/config.go` | Go | Minimal surrounding code |
| 6 | `csharp/Config.cs` | C# | Multiline concatenation via `+` operator |
| 7 | `config/appsettings.json` | JSON | Nested config, grouping relationship (also Pilot 002) |
| 8 | `config/settings.yaml` | YAML | Nested config, includes a value that bypasses the placeholder allow-list |
| 9 | `edge_cases/false_positives.properties` | `.properties` | **Negative control** — zero true positives, by design |

All 9 confirmed present in `benchmark/dataset/files/` and in
`benchmark/dataset/cases.jsonl`'s ground truth — see
`validation_report.md` for per-file detail.

## The six tasks

1. `explain_code` — code comprehension
2. `identify_bug` — bug-finding (a legitimate "no bug found" response is expected and comparable, not a failure)
3. `security_analysis` — the highest-stakes task: does sanitization cause a missed real issue, or a hallucinated one caused by the placeholder itself?
4. `generate_unit_tests` — structural/behavioral test-generation equivalence
5. `suggest_refactoring` — code-quality judgment that should be unaffected by which literal values are visible
6. `explain_config_relationships` — the task most directly aimed at this project's differentiation claim (per `ai-evaluation/README.md`): can an AI still reason about how values *relate* when they're placeholders?

Each template is used exactly as already written in `ai-evaluation/prompts/`
— none were modified to build this freeze.

## Two conditions

- **Original** — the unmodified benchmark fixture file, exactly as it
  exists in `benchmark/dataset/files/`.
- **Sanitized** — the same file run through the current, unmodified
  engine with `placeholder_mode=True`, using an isolated single-file scan
  per file (see `manifest.json`'s `sanitized_fixture_generation_method`).
  All 9 sanitized fixtures have since been generated and are frozen under
  `sanitized/` (this document's own validation, in `validation_report.md`,
  covers that generation is deterministic, leak-free, and syntactically
  valid).

## Isolation rules

- **One fresh, independent subagent session per (file, task, condition)
  cell.** No session's prompt may reference, or be derived from, any
  other session.
- **No cross-condition access.** A session evaluating the sanitized
  condition never sees the original file's content, and vice versa.
- **No repository exploration.** Each session receives the complete file
  content embedded directly in its prompt, so there is no need — and, per
  Pilot 001/002's precedent, no expectation — for it to read files, search
  the repository, or use any tool. Zero tool calls per session is the
  target and the observed baseline from both prior pilots.
- **No experiment metadata supplied to the evaluated agent.** The
  evaluated session is never told this is an experiment, never told what
  Credential Scrubber is, never told a value was sanitized/removed, and
  never shown this manifest, the rubric, or any other evaluation file —
  only the task template's own wording plus the one file's content.
- **No LLM judge, anywhere.** Every score is produced by a human rater
  applying `rubric/rubric.md` — no model is ever asked to evaluate,
  compare, or rank a response.
- **One response per condition** — no repeated sampling in this design.

## Why original and sanitized must be run independently

If the same conversation produced both responses, the model would already
know the "before" content while writing the "after" response (or vice
versa), collapsing exactly the variable this experiment exists to
isolate — whether the *presence or absence of the real values* changes
task usefulness. A model that has already seen the real value can trivially
"perform well" on the sanitized version by drawing on context it isn't
supposed to have; a model that has already seen the sanitized version
first could anchor its original-condition response on the placeholders
it saw a moment ago. Two fresh, independent sessions (confirmed via
distinct session identifiers and zero cross-referencing content, exactly
as Pilot 001 and Pilot 002 already demonstrated is achievable with the
available tooling) are the only way to keep sanitization presence/absence
as the *sole* variable.

## What is held constant

Same prompt template (byte-identical except the embedded file content),
same file (two representations of it), same task, same model
(`claude-sonnet-5`, inherited identically by both sessions), same
(uncontrollable-but-identical-by-omission) settings, same evaluation
procedure and rubric.

## What differs

The **only** intended variable is whether the file content shown to the
model is the original or the sanitized representation. One structural
exception is explicit and documented, not incidental: `explain_config_relationships`
is not run against the 6 source-code files at all, in *either* condition,
because the task template itself declares that scope restriction — this
is a per-task inclusion/exclusion decision made once, identically, before
any response is collected, not a per-condition difference.

## What was measured

- **Human-rated task usefulness** — `rubric/rubric.md`'s six dimensions,
  scored per response by a human rater, following
  `ai-evaluation/results/results_template.csv`'s schema (already aligned
  to the rubric — see the prior evaluation-design audit; no schema
  change made here). The actual completed data lives under `results/`
  (raw responses, `batch_record.md`, `human_evaluation.md` per candidate
  file) and `analysis/evaluation_dataset.csv` (the same scores in
  structured, one-row-per-response form).
- **Automated sanitization/detection metrics** — already implemented and
  measured independently of this experiment, via `run_benchmark.py` /
  `run_benchmark.py --placeholder-mode` (leakage, consistency,
  distinctness, syntax validity, determinism) — see `BENCHMARK.md`. This
  experiment's `validation_report.md` re-confirms these properties
  specifically for the 9 frozen files, but does not replace or duplicate
  the full 113-case benchmark.

These two measurement types are kept explicitly separate throughout this
experiment's documentation (manifest, validation report, and any future
per-cell result), per `ai-evaluation/README.md`'s own A/B/C dimension
split — human-rated usefulness is never combined with, or used to infer,
automated sanitization correctness, or vice versa.

## Human rubric dimensions

Exactly `rubric/rubric.md`'s six, unmodified: **Correctness, Completeness,
Consistency, Usefulness, Misunderstood a sanitized value?, Relationships
between values preserved?** No new dimension was added for this
experiment.

## Known limitations (carried into the frozen design, not fixed)

- **Category-imprecision on 3 of 9 files** (`java/Config.java`,
  `python/config.py`, `go/config.go`): certain single-line
  source-code-identifier secrets (`apiKey`, `api_key`) resolve to the
  generic `GENERIC_SECRET` category rather than `API_KEY`, a pre-existing
  engine behavior (regex-backtracking artifact in the single-line
  `code_variable_pattern` detection path — see `validation_report.md` for
  the precise mechanism, confirmed not to affect the multiline or
  config-key detection paths). Not fixed here, per this task's explicit
  "do not change detection rules" instruction — preserved and documented.
- **`CustomerId` detection gap** on `config/appsettings.json`: no
  customer/user-identifier detection rule exists in the engine; this
  value is unchanged in both conditions for that file (a pre-existing,
  documented gap, not a new issue).
- **Heuristic-only syntax checking** for Java/JS/TS/Go/C# (no
  stdlib-level parser available to this project — `BENCHMARK.md`
  Limitations).
- **Residual synthetic signals.** Every file in `benchmark/dataset/files/`
  carries some synthetic tell (a disclosure comment on 8 of 9 files, or —
  for `appsettings.json`, the sole exception — the value `"AppName":
  "BenchmarkDemo"` and `fake-`-prefixed secrets). No file in this
  population reads as an entirely unlabeled, ordinary developer file.
- **Tooling constraints carried over from Pilot 001/002**: temperature
  and max-output-tokens are not independently controllable via the
  available subagent tooling; the "AI agent" evaluated is a Claude Code
  subagent, not a bare provider API call. Both apply identically across
  all 96 applicable cells.
- **9 files is not exhaustive** — a deliberately small, hand-selected
  population (per `ai-evaluation/README.md`'s own scope: "a pilot to
  shake out methodology problems, not a statistically powered study"),
  covering language/format diversity, not every secret shape or coding
  style in the wild.

## This is a comparative evaluation, not proof of universal effectiveness

This experiment produced a *per-file, per-task* comparison of human-rated
response quality between two conditions on 9 specific, synthetic,
hand-selected files (see `analysis/results_and_discussion.md` for the
full interpretation). It is explicitly **not**:

- A statistically powered study (9 files is a deliberate pilot-scale
  population, not a representative sample of real-world code).
- Proof that Credential Scrubber's sanitization "works" or "preserves
  usefulness" for any file, language, or task outside this exact set.
- A claim that AI usefulness has been proven to survive sanitization in
  general — only a measured, per-cell comparison of two response sets,
  now that the experiment has actually been run and scored.
- A ranking of files, a pre-scored expectation of which condition will do
  better, or a selection filtered by any preliminary AI output — no
  cell's inclusion or exclusion in this freeze was based on any AI
  response, preliminary or otherwise; the population and task
  applicability were fixed from the existing, already-documented
  candidate list and each task's own documented scope, before any
  response in this experiment (beyond the two already-existing pilots)
  was collected.
