# AI-Agent Evaluation — Phase 2

**Status: completed.** The frozen experiment defined in `experiment/`
(9 files × 6 tasks × 2 conditions, 96 applicable responses) has been
executed, human-scored against the frozen rubric, and statistically
analyzed.

**What is complete:**
- 96 AI responses collected: 48 Original, 48 Sanitized (`experiment/results/`).
- Human evaluation of all 96 responses against `rubric/rubric.md` is complete, with an independent scoring-integrity audit (`experiment/scoring_integrity_audit.md`).
- Descriptive statistical analysis is complete (`experiment/analysis/descriptive_results.md`).
- Inferential statistical analysis is complete — paired Wilcoxon signed-rank tests, Holm-Bonferroni correction across the four primary dimensions, bootstrap confidence intervals (`experiment/analysis/inferential_results.md`).
- A synthesized results-and-discussion write-up is available (`experiment/analysis/results_and_discussion.md`).
- Four research figures are available (`experiment/analysis/figures/`, documented in that directory's own README).

**How the responses were produced, and what that does and doesn't mean:**
each of the 96 AI responses was collected from an independent Claude Code
subagent session, used here only as this evaluation's controlled proxy
for "an AI coding agent reading the file" (see `experiment/README.md`'s
isolation rules — one fresh session per cell, no cross-condition access,
no experiment metadata shown to the evaluated session). **This is a
property of the evaluation methodology, not a feature or integration of
Credential Scrubber itself** — nothing in this directory changes, calls,
or depends on `engine.py`, and the Credential Scrubber application has no
integration with Claude Code, any other agent, or any live API.

This is the second phase of turning Credential Scrubber from a security
tool into a measurable research project (Phase 1 was the synthetic
detection/sanitization benchmark under `benchmark/`). Phase 1 asked "does
the engine find and correctly mask the secret?" This phase asks a
different, harder question that Phase 1 cannot answer on its own: **if
sanitization works perfectly, does the AI agent reading the sanitized
code still do useful work?**

## Research objective

Determine whether source code can be sanitized - removing or replacing
sensitive values - in a way that:

1. Prevents a sensitive value from ever reaching an AI coding agent's
   context, and
2. Preserves enough semantic information (types, relationships, structure)
   that the agent's output on the sanitized version is still substantively
   as useful as its output on the original.

The goal is not "redact everything" (trivially achieves goal 1 while
destroying goal 2) and not "redact nothing" (the reverse). The interesting
region - and the one this project is actually positioned to say something
new about, per the earlier competitive-landscape audit - is the tradeoff
between them.

## Research question

> Can sensitive source-code values be sanitized before providing source
> code to an AI coding agent while preserving enough semantic information
> for the AI to perform useful software-engineering tasks?

This is deliberately a comparative, not absolute, question. It's answered
by measuring a *delta* between two conditions (original vs. sanitized),
never by a standalone score on either condition alone.

## Relationship to Phase 1 (the existing benchmark)

| | Phase 1 (`benchmark/`) | Phase 2 (`ai-evaluation/`, this directory) |
|---|---|---|
| Asks | Did the engine detect and correctly mask the secret? | Given a *correctly* sanitized file, is it still useful to an AI agent? |
| Subject | `engine.py`'s output | An AI model's output, given `engine.py`'s output as input |
| Ground truth | Machine-checkable (regex/parse/string match) | Human-rated (a rubric, not an oracle) |
| Status | Implemented, automated, 113 cases (no committed run-results file — see `BENCHMARK.md`) | Completed - 96 applicable cells run, human-scored, and analyzed |

Phase 2 assumes Phase 1's detection/sanitization correctness as a
*precondition*, not something it re-tests. A file that leaks a secret
(Phase 1's critical failure) is not a useful case for Phase 2 - Phase 2
is specifically about the cost of sanitization that already worked
correctly, not about sanitization that's still broken.

## Threat model

```
Developer source code
        |
        v
  Credential Scrubber   <-- Phase 1 lives here (detection + sanitization)
        |
        v
  Sanitized source
        |
        v
   AI coding agent       <-- Phase 2 lives here (does the agent still work?)
        |
        v
 AI response / generated code
```

**Sensitive information this project protects** (matches the existing
rule categories in `rules_default.yaml`, not a new list invented for this
phase): passwords, API keys, access/bearer tokens, database credentials
and connection strings, private keys, client/webhook secrets, cloud
provider credentials, and - per the earlier audit's differentiation
direction, not yet implemented in the engine - customer/user identifiers
and internal infrastructure details (internal hostnames, internal URLs).

**What the AI agent still needs to know to be useful**, per task:
- *That a value exists and roughly what it's for* (this is a credential,
  this is a URL, this is an identifier) - the **type**.
- *Whether two values are the same value or different values* - the
  **relationship** (see "Placeholder requirements" below - this is the
  crux of the research question).
- *The surrounding code's structure and control flow*, which sanitization
  should never touch at all.
- *Enough of a value's shape to reason about format-level bugs* (e.g. "is
  this connection string missing a port") without needing the real value.

**What an attacker could learn if sanitization fails**, by failure mode:
- **False negative** (Phase 1 concern) - the real secret reaches the AI
  provider's servers/logs/training pipeline in full. This is the
  original, pre-existing risk this whole project exists to prevent.
- **Partial/incorrect sanitization** (Phase 1 concern, e.g. the audit's
  F2 finding) - a fragment or the whole value survives inside otherwise
  "sanitized" text.
- **Placeholder correlation leakage** (a Phase 2-relevant risk, *not yet
  applicable* since no reversible mapping is implemented in this phase) -
  if a future stable-placeholder system's real-value mapping were ever
  exposed or reconstructible, an attacker with response access could
  correlate placeholders across a session. Out of scope for this phase's
  experiment (no mapping is being built or sent anywhere here), but noted
  because it is the natural next threat once placeholders exist for real.
- **Over-disclosure via "helpful" AI inference** - a subtler risk
  specific to this phase: if a sanitized value's *type label* is too
  specific (e.g. `<STRIPE_SECRET_KEY_FOR_PROD_BILLING_ACCOUNT_4471>`
  instead of `<API_KEY_1>`), the label itself becomes a disclosure. This
  phase's rubric explicitly checks for it (see the rubric's "over-specific
  placeholder" failure mode).

**What sanitization is allowed to transform:** the literal value of
anything matching a detection rule - its characters, replaced by a
placeholder. Nothing about *where* it appears (line, position, quoting) or
*what type* it is should change.

**What must remain unchanged:** everything else - code structure, control
flow, non-sensitive literals, comments, whitespace-significant formatting,
identifiers/variable names that aren't themselves the sensitive value, and
(critically for the research question) the *pattern of repetition* of a
given sensitive value across the file.

## Placeholder requirements

The evaluation is built around **typed, stable, per-value placeholders**,
not the single shared mask (`***REDACTED***`) the engine's default
behavior produces. This is now implemented, as an opt-in mode -
`engine.scan_project(..., placeholder_mode=True)` - rather than the
hand-authored fixtures originally planned for this phase; see
`dataset/README.md` for how the experiment's sanitized condition is
produced. The default (`placeholder_mode=False`, MASK) behavior is
unchanged and remains the engine's default everywhere else.

Requirement, illustrated:

```
Original:
customerId = "PF001"
...
customerId = "PF001"          # same value, later in the same file

Sanitized:
customerId = "<CUSTOMER_ID_1>"
...
customerId = "<CUSTOMER_ID_1>"   # same placeholder - NOT <CUSTOMER_ID_2>
```

If a *different* real value appeared instead (`"PF002"`), it must get a
*different* placeholder (`<CUSTOMER_ID_2>`), never collide with the first.

### Why deterministic relationships matter to AI agents

An agent reasoning about code relies on identity, not just type, to follow
logic. Two concrete failure modes if placeholders aren't stable:

- **False merging** (all instances of a category get the same token,
  e.g. every ID becomes `<ID>`): the agent can no longer tell "this bug
  only reproduces for one specific customer" from "this bug affects all
  customers" - a materially different, and differently prioritized, bug.
- **False splitting** (the same real value gets different placeholders
  in different spots, e.g. because the mapping isn't kept consistent):
  the agent may conclude two DB config blocks point at different
  databases when they actually point at the same one, and reason (or
  generate a fix) accordingly wrong.

Both failure modes are silent - the agent doesn't know it's reasoning
about a proxy value, so it has no way to flag its own confusion. This is
precisely the "misunderstood the sanitized values" failure mode the
rubric asks human raters to watch for.

## Evaluation dimensions

Kept **conceptually and numerically separate** - never combined into one
score. A tool can be strong on one axis and weak on another, and
collapsing them would hide exactly the tradeoff this research question is
about.

### A. Detection correctness
*(Already implemented and measured - see `benchmark/`. Restated here only
to show where it fits relative to B and C.)*
- Precision, Recall, F1, False-positive rate.

### B. Sanitization correctness
*(Already implemented and measured - see `benchmark/`, including the
placeholder-mode-specific metrics below.)*
- Secret leakage (critical - does the original value survive?)
- Replacement correctness (right span, right file)
- Placeholder consistency (same real value -> same placeholder) - a real,
  checked property now that placeholder mode exists (`run_benchmark.py
  --placeholder-mode`); still trivially true under the default MASK mode,
  where every finding shares one token.
- Placeholder distinctness (different real values never collide on one
  placeholder) - likewise now a real, checked property in placeholder
  mode; see `BENCHMARK.md`.
- Repeated-value relationship preservation (the PF001/PF002 property
  above) - measurable directly against the real engine now, via
  `placeholder_mode=True`.

### C. Source/semantic preservation *(new in this phase)*
- **Syntax validity** - does the sanitized file still parse in its own
  language/format? (Reuses the same real-parser-where-possible /
  heuristic-elsewhere approach as `benchmark/syntax_check.py`.)
- **Structural preservation** - is the code's shape (control flow,
  function/class structure, config nesting) unchanged?
- **Identifier/reference preservation** - are variable, key, and function
  names untouched where they aren't themselves the sensitive value?
- **Configuration structure preservation** - for config files
  specifically, are the key hierarchy and format conventions intact?
- **Task usefulness after sanitization** *(the human-rated core of this
  phase)* - for each fixed task (explain/find-a-bug/security-analysis/
  generate-tests/refactor/explain-config-relationships), is the AI
  response on the sanitized version substantively as useful as on the
  original? Rated per the rubric in `rubric/`, always as **sanitized vs.
  original**, never as an absolute score.

## Evaluation methodology

1. Take a small, fixed set of source files already in the Phase 1
   benchmark dataset (see `dataset/README.md` for selection criteria and
   the candidate list).
2. For each file, produce the sanitized companion by running it through
   the actual engine: `engine.scan_project(..., placeholder_mode=True)`
   (or the desktop app, once this mode is exposed there - not yet, per
   this phase's scope). No hand-authoring - the experiment measures the
   real system's output, not a mockup of what it should eventually do.
3. For each of the fixed tasks (`prompts/`), run the *same* prompt
   template against both the original and the sanitized version of the
   file, using the same model, version, and settings.
4. A human rater scores both responses independently against the rubric
   (`rubric/`), without being told (at scoring time) which response came
   from which condition where practical (see "Experimental controls").
5. Record everything in `experiment/results/` - raw responses, ratings,
   and any observed failure mode - before drawing any conclusion. (The
   original `results/` directory documents the schema this follows; the
   actual completed data lives under `experiment/results/` - see
   `results/README.md`.)
6. Compare sanitized-condition ratings against original-condition ratings
   *per task, per file* - never aggregated into one number across tasks,
   since "explain the code" and "generate unit tests" are not
   commensurate.

## Metrics (summary)

| Dimension | Metric | Type |
|---|---|---|
| A. Detection | Precision / Recall / F1 / FPR | Automated (existing) |
| B. Sanitization | Leakage / replacement correctness / placeholder consistency / distinctness | Automated (existing, incl. `run_benchmark.py --placeholder-mode`) |
| C. Semantic preservation | Syntax validity | Automated (reused checker) |
| C. Semantic preservation | Structural / identifier / config-structure preservation | Manual diff review |
| C. Task usefulness | Rubric ratings (1-5 ordinal, per dimension - see `rubric/`) | Human-rated, per response |

No single number summarizes "how good is sanitization" across all three
dimensions - that arbitrary combination is explicitly rejected by this
methodology, per the task brief.

## Experimental controls

For any comparison between an original-condition response and a
sanitized-condition response to be meaningful, the following must be held
fixed - varying only the presence/absence of sanitization:

- **Same model.**
- **Same model version**, where the provider exposes one (avoids a
  silent model swap between runs being mistaken for a sanitization
  effect).
- **Same prompt template** (see `prompts/`) for both conditions.
- **Same source file** (the sanitized version is a transform of the
  exact original, not a different file).
- **Sanitization is the only variable** - no other difference between
  the two inputs.
- **No hidden information given to one condition and not the other** -
  in particular, the prompt must not mention "this code has been
  sanitized" or otherwise cue the model, since that framing could itself
  change the response (see `prompts/README.md`).
- **Same task** description and framing for both conditions.
- **Same rubric** applied by the same rater(s) to both conditions,
  ideally without the rater knowing which condition produced which
  response until after scoring (ID codes rather than "original"/
  "sanitized" labels in the response given to the rater - see
  `results/README.md`).

## Known limitations

*A concise, public-facing summary. For the complete limitations list see
`experiment/analysis/results_and_discussion.md`'s "What the experiment
does NOT establish" section; for limitations specific to the statistical
methods used, see `experiment/analysis/inferential_results.md`'s
"Statistical limitations" section.*

- **YAML block-scalar bodies are not scanned by the engine** (a
  documented, pre-existing gap - see `BENCHMARK.md`). This phase does
  not fix it and does not route block-scalar content through the
  experiment.
- **The benchmark dataset is entirely synthetic.** Results here say
  nothing about real, messier production code - variable naming
  conventions, comment density, and secret placement in the wild are all
  more varied than a small hand-built dataset.
- **The completed AI experiment is small** - 9 files, 6 task types (one
  applicable only to the 3 config-shaped files), one model
  (`claude-sonnet-5`, via Claude Code subagent sessions). This was a
  pilot-scale experiment to establish methodology and produce an initial
  measurement, not a large, purpose-powered study - see
  `experiment/analysis/inferential_results.md`'s own statistical
  limitations for exactly what small-sample caveats apply to its results.
- **Human evaluation introduces subjectivity.** Ratings are ordinal
  opinions from whoever scores them, not an objective ground truth the
  way Phase 1's detection metrics are. Multiple independent raters and an
  agreement measure are a natural next step, not part of this phase.
- **Sanitization can genuinely remove information an AI would find
  useful** - e.g. a real hostname might hint at environment (staging vs.
  prod) in a way `<INTERNAL_HOSTNAME_1>` doesn't. This is not a bug to
  fix; it is the actual tradeoff this whole research question exists to
  quantify.
- **This phase does not prove anything about protection against a real
  AI-agent context leak.** It does not model prompt injection, tool-use
  side channels, model provider data retention policy, or an agent
  choosing to echo a placeholder's original value if it can infer it
  from other context. It measures one narrower thing: response quality
  delta when a value is replaced by a well-formed placeholder versus left
  in the clear.

## What this phase intentionally does not include

- **No integration between the Credential Scrubber application and
  Claude Code, any other agent, or any live API.** The completed
  experiment's AI responses came from independent Claude Code subagent
  sessions used purely as the evaluation's proxy for "an AI coding
  agent" - that is a property of how the evaluation was run, not a
  feature of `engine.py` or the desktop app (see the status section
  above).
- **No automated LLM-as-judge** - all rubric scoring, for all 96
  responses, was done by a human rater reading the raw response.
- **No UI change, no new engine feature, no change to `engine.py`'s
  actual redaction behavior** - this phase evaluates the existing,
  unmodified engine's `placeholder_mode=True` output. Placeholder mode
  is real, tested, and used to produce this experiment's sanitized
  fixtures, but it is reachable today only via direct `engine.py` calls
  and `run_benchmark.py --placeholder-mode` - the desktop app's scan
  route does not expose it, and this phase does not add that wiring.
- **No fix for the YAML block-scalar-body gap** (still open, see
  `BENCHMARK.md`).
- **No claim, anywhere in this phase's output, that sanitization "makes
  AI usage secure"** - only a measured, per-cell comparison of two
  response sets, now that the experiment has been run, scored, and
  analyzed. Formal paired hypothesis testing (Wilcoxon signed-rank,
  Holm-Bonferroni-corrected) was performed and is reported in
  `experiment/analysis/inferential_results.md` - but at this
  experiment's pilot scale (9 files, 48 paired comparisons), not as a
  study explicitly powered in advance for a target effect size, and
  never as evidence that sanitization is universally safe or has no
  effect (see that document's own limitations section).

## Directory contents

```
ai-evaluation/
├── README.md               This file.
├── dataset/
│   └── README.md           How the experiment's 9 files were selected; candidate list.
├── prompts/
│   ├── README.md            Prompt-design principles (determinism, no condition leakage).
│   └── *.md                  One fixed template per task.
├── rubric/
│   └── rubric.md            Human evaluation rubric (1-5 ordinal, six dimensions).
├── results/
│   ├── README.md             Original results schema/scaffold - superseded by experiment/results/ (see that README).
│   └── results_template.csv  Empty template, kept for the schema it documents.
├── pilot/, pilot-002/        Two earlier single-cell pilots (one file x one task each), kept for record; superseded by experiment/.
└── experiment/                The completed, frozen 9-file x 6-task x 2-condition experiment.
    ├── README.md                     Frozen design: population, tasks, isolation rules, completion status.
    ├── manifest.json                 Machine-readable frozen design + completion status.
    ├── validation_report.md          Per-file engine validation the freeze was built on.
    ├── collection_integrity_audit.md Read-only audit of the 96 collected raw responses.
    ├── scoring_integrity_audit.md    Read-only audit of the completed human evaluation.
    ├── sanitized/                    The 9 frozen sanitized fixtures (engine.py, placeholder_mode=True).
    │                                  (Original-condition responses use benchmark/dataset/files/ directly -
    │                                   there is no separate experiment/original/ copy.)
    ├── results/                      Raw AI responses + human evaluation, one subdirectory per candidate file
    │   └── <candidate>/<task>/{original,sanitized}.txt, batch_record.md, human_evaluation.md
    └── analysis/                     Descriptive + inferential statistical analysis and figures.
        ├── evaluation_dataset.csv, paired_deltas.csv       Structured scoring data.
        ├── descriptive_results.md                          Descriptive statistics (no significance tests).
        ├── inferential_results.md, run_inferential_analysis.py   Paired Wilcoxon/Holm/bootstrap analysis + its script.
        ├── results_and_discussion.md                       Synthesized research write-up.
        ├── generate_figures.py                             Figure-generation script.
        └── figures/                                        4 PNG research figures + README.md.
```
