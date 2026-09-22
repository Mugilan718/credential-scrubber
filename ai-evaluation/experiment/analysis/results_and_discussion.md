# Results and Discussion — Credential Scrubber AI Evaluation Experiment

This document interprets the completed experiment. It introduces no new
statistics, no recalculated numbers, and no additional tests. Every
figure below is taken directly from `descriptive_results.md`,
`inferential_results.md`, `evaluation_dataset.csv`,
`paired_deltas.csv`, `scoring_integrity_audit.md`, and
`collection_integrity_audit.md`, which remain the authoritative sources.

---

## 1. Research question

The experiment was designed to address one question:

> **Can sensitive source-code values be sanitized before providing
> source code to an AI coding agent while preserving enough semantic
> information for the AI to perform useful software-engineering
> tasks?**

This document does not restate the question in a stronger or weaker
form. It is not a question about whether sanitization is "safe," about
overall AI capability, or about whether one condition "wins" — it is
specifically about whether enough task-relevant semantic information
survives sanitization for six defined software-engineering task types.

## 2. Experimental dataset

- **9 candidate files**, spanning 6 source-code languages (Java, Python,
  JavaScript, TypeScript, Go, C#) and 3 configuration/data formats
  (JSON, YAML, Java `.properties`), one of which
  (`edge_cases/false_positives.properties`) is a negative control with
  zero ground-truth sensitive values.
- **6 task types**: `explain_code`, `identify_bug`, `security_analysis`,
  `generate_unit_tests`, `suggest_refactoring`, and
  `explain_config_relationships`.
- **96 evaluated AI responses**: 48 under the `original` (unsanitized)
  condition and 48 under the `sanitized` condition, each produced by an
  independent Claude Code subagent session with no memory of any other
  session, no repository exploration (`tool_uses: 0` in every collected
  session), and no mention of the experiment, sanitization, or the other
  condition in its prompt.
- **48 paired comparisons.** Not every (file, task) combination was
  applicable: `explain_config_relationships` is meaningful only for the
  3 configuration-shaped files (per the frozen
  `manifest.json` `task_applicability_matrix`) and is `not_applicable`
  for the 6 source-code files. This yields 6 files × 5 tasks + 3 files ×
  6 tasks = 30 + 18 = 48 applicable (file, task) cells, each scored once
  per condition, producing 96 responses and 48 paired comparisons — not
  the nominal 9 × 6 = 54 (108 responses) that a full grid would imply.
- **Scoring:** every response was scored by hand against the frozen
  `ai-evaluation/rubric/rubric.md`, one response at a time, without an
  LLM judge, on six dimensions (Correctness, Completeness, Consistency,
  Usefulness, Misunderstood-a-sanitized-value, Relationships-preserved),
  plus a separate, non-scored failure-mode checklist.
- **Independent validation:** a read-only collection-integrity audit
  (`collection_integrity_audit.md`) verified all 96 responses, their
  metadata, and every frozen input file by hash before scoring began; a
  separate scoring-integrity audit (`scoring_integrity_audit.md`)
  verified rubric compliance, failure-mode consistency, and raw-file
  integrity after scoring, and resolved one methodology inconsistency
  (Dimension 6's applicability rule) transparently, with the resolution
  documented in that same file.
- **Descriptive analysis** (`descriptive_results.md`) computed per-
  condition and paired-difference statistics for all four primary
  dimensions, by task, and by language/file type, without any inferential
  test.
- **Inferential analysis** (`inferential_results.md`) added paired
  Wilcoxon signed-rank tests, rank-biserial effect sizes, bootstrap
  confidence intervals, and Holm-Bonferroni correction across the four
  primary dimensions, plus clearly-labeled exploratory subgroup analyses
  and a sensitivity analysis.

## 3. Primary quantitative findings

The four primary dimensions were each tested as N=48 paired differences
(sanitized − original), with Holm-Bonferroni correction applied across
the dimensions that produced a valid p-value.

| Dimension | N pairs | Non-zero pairs | Raw p-value | Holm-adjusted p-value | Distinguishable from zero at α=0.05? |
|---|---:|---:|---:|---:|---|
| Correctness | 48 | 1 | 0.3173 | 0.3173 | No |
| Completeness | 48 | 6 | 0.0264 | 0.0529 | No |
| Consistency | 48 | 0 | — | — | Not applicable (no test performed) |
| Usefulness | 48 | 7 | 0.0158 | 0.0473 | **Yes** |

Stated plainly:

- **Correctness was not statistically distinguishable from zero after
  Holm correction** (adjusted p = 0.3173).
- **Completeness was not statistically distinguishable from zero after
  Holm correction**, although its adjusted p-value (0.0529) was close to
  the chosen 0.05 threshold.
- **Consistency had zero paired changes across all 48 pairs**, so no
  inferential test was applicable; no p-value is reported for it, and
  none was manufactured.
- **Usefulness was statistically distinguishable from zero after Holm
  correction** (adjusted p = 0.0473).

## 4. The meaning of the Usefulness result

The experiment observed a **statistically distinguishable decrease in
Usefulness scores under the sanitized condition, after correcting for
multiple comparisons**. This is a paired, distributional observation
about this dataset — it is not the claim that "sanitization reduces AI
usefulness" in a general sense, and that claim is not made here.

Several features of the same result argue for caution before drawing a
general conclusion from it:

- Only **7 of 48 Usefulness pairs changed at all** — 41 of 48 pairs
  (85.4%) showed no difference between conditions.
- **Every one of those 7 changes was a decrease**; none was an increase.
  This directional uniformity, not a large average magnitude, is what
  the Wilcoxon test and the rank-biserial effect size (−1.00) are
  detecting — the effect size reflects that the non-zero differences
  were unanimous in direction, not that a large fraction of responses
  changed or that any single response changed by a large amount.
- The largest task-level concentrations were in **`generate_unit_tests`**
  (2 of 9 pairs, both −3, the largest magnitude drops in the dataset —
  `javascript` and `yaml`) and **`suggest_refactoring`** (4 of 9 pairs,
  −1 to −2 — `go`, `csharp`, `typescript`, `properties`).
- The **Properties byte-identical control** (§8 below) demonstrated that
  a paired difference of comparable shape and magnitude
  (−2 Completeness / −1 Usefulness, in `suggest_refactoring`) can occur
  **without any sanitization having taken place at all**, since that
  file's original and sanitized inputs are identical. This is direct
  evidence that ordinary session-to-session response variability is a
  real, competing explanation for at least part of the observed
  Usefulness pattern.

The overall Usefulness result should therefore be interpreted **together
with** this control-condition variability, not in isolation. This
document does not attempt to statistically subtract the control's
variability from the treatment comparison — the experiment was not
designed with the repeated sampling that a proper variance decomposition
would require (see §11, §12). The result stands as: a distributional
signal that is statistically distinguishable from zero in this dataset,
occurring in a small minority of pairs, concentrated in two tasks, and
co-occurring with direct evidence that unrelated variability can produce
similarly-shaped changes.

## 5. Completeness result

- **6 of 48 pairs decreased**; no pair increased.
- Holm-adjusted p-value = **0.0529**.
- This value is **just above** the pre-registered α = 0.05 threshold used
  throughout this analysis.
- Accordingly, this result is **not** described as statistically
  significant, and is not described as "almost significant" — the 0.05
  threshold is a convention adopted for this analysis, not a boundary
  with independent scientific meaning, and a result on either side of it
  by a small margin should be read as comparably uncertain rather than
  categorically different.
- The pattern (direction, task concentration in `generate_unit_tests`
  and `suggest_refactoring`, magnitude) closely parallels the Usefulness
  result, which is expected since Completeness and Usefulness moved
  together in every affected pair in this dataset. Given how close the
  adjusted p-value sits to the threshold and how similar its underlying
  pattern is to the dimension that did cross it, **this result may
  warrant further investigation in a larger or repeated experiment**,
  where a larger number of non-zero pairs could better distinguish a
  reproducible pattern from sampling variation.

## 6. Correctness and Consistency

**Correctness:**

- Only **one** paired difference was observed across all 48 pairs
  (`json` / `suggest_refactoring`).
- That single change was an **increase** in the sanitized condition
  (original = 4, sanitized = 5).
- The change did not originate from the sanitized-condition response
  reasoning more correctly in a general sense. It originated from an
  **error in the original-condition response**: its illustrative "actual
  secret value" example dropped the `fake-` prefix present in the real
  source literal, a minor but real factual inaccuracy. The sanitized
  response could not make the analogous error because it had no literal
  secret value available to reproduce.
- In other words: **sanitization removed information that had enabled
  an erroneous illustrative claim** in the original condition. This is a
  case where information removal prevented an error rather than caused
  one — worth recording precisely because it illustrates that
  information removal can affect a response in either direction,
  depending on what the removed information would otherwise have been
  used for.

**Consistency:**

- **48 of 48 pairs were unchanged.** No paired difference was observed on
  this dimension anywhere in the dataset, in either direction.

**Relevance to semantic preservation:** Correctness and Consistency are
the two dimensions most directly tied to whether a response's *internal*
reasoning holds together and whether its factual claims about the code
are true. Their near-total stability across 48 paired comparisons — with
the single Correctness exception explained above, and traced to a
mechanism other than "sanitization degraded the response's reasoning" —
is evidence that, at least for the responses in this dataset, sanitized
inputs did not measurably increase the rate of factual errors or
internal self-contradiction relative to unsanitized inputs. This is
consistent with (not proof of) the hypothesis that the core semantic
structure needed to reason correctly and coherently about these files
survived sanitization in the cases tested.

## 7. Qualitative findings

The paired-difference numbers above do not by themselves indicate *why*
a score changed. Cross-referencing the affected pairs against the
qualitative evidence recorded in each `human_evaluation.md` separates
the observed changes into three categories.

### Intended information-loss effects

Cases where the qualitative evidence points to sanitization's deliberate
removal of information as the plausible mechanism:

- **JavaScript and YAML `generate_unit_tests`** (−3 Completeness / −3
  Usefulness each): the sanitized-condition response declined to write
  any test code, reasoning from the visible placeholder syntax toward a
  broader "this whole file is an external fixture, not worth testing"
  conclusion — where the paired original-condition response, facing
  materially the same testable structure, delivered working tests. This
  is recorded as a plausible behavioral consequence of replacing a
  realistic-looking value with a generic semantic placeholder.
- **YAML `session_key` severity judgment** (no scored dimension change,
  but a directly documented qualitative effect): the real value behind
  `session_key` is the non-secret-looking word `dummy`; the sanitized
  fixture replaces it with `<GENERIC_SECRET_1>`, a placeholder
  indistinguishable in appearance from a genuine secret. The
  original-condition response could see the value was trivial and
  assigned a calibrated Medium-severity finding; the sanitized-condition
  response reasonably treated the placeholder at face value and assigned
  High severity. This is a direct example of sanitization removing the
  specific information a severity judgment depends on, without either
  response being in error given what it could see.
- **The `json`/`suggest_refactoring` Correctness increase** (§6): the
  same underlying mechanism — information removal — operating in the
  direction of preventing an error rather than causing one.

### Potential model/session variability

Cases where the qualitative evidence does not clearly implicate
information loss, and where a within-experiment control shows the same
shape of change can occur independent of sanitization:

- **Go, C#, and TypeScript `suggest_refactoring`**: each sanitized-
  condition response's delivered refactor left a related fix (secret
  redaction in Go; console-logging removal in C#; environment-variable
  externalization in TypeScript) unimplemented in code, despite the same
  response's own `security_analysis` sibling (Go, C#) correctly
  identifying the same issue — i.e., the information needed was
  demonstrably available. Nothing about these gaps depends on the actual
  secret value.
- **Python and JSON `security_analysis`** (−1 Completeness / −1
  Usefulness each): both decreases trace to specific observations that
  the evaluations confirm were independently findable directly in the
  *sanitized* file itself (unrelated to the redacted values) — response-
  thoroughness variation rather than information loss.
- **The Properties negative control** (§8): the clearest evidence in
  this category, since it isolates response variability from
  sanitization entirely.

### Placeholder interpretation issues

Two mild cases were recorded, both in the `java` file, both affecting
only Dimension 5 (Misunderstood a sanitized value?), neither affecting
any of the four primary dimensions:

- `java` `explain_code`/sanitized: the response speculated, backwards,
  about the substitution mechanism (describing placeholders as slots to
  be filled *in* rather than values that had been redacted *out*);
  explicitly hedged as a question, with no effect on the response's main
  content.
- `java` `generate_unit_tests`/sanitized: a placeholder was used as an
  ordinary test-fixture literal with no acknowledgment elsewhere in the
  response that it was a substituted value; the resulting test is
  factually correct and would run.

Both are recorded as mild by the human evaluator, and neither is
exaggerated here. Across all 96 responses:

- **0** false merges (two different real values treated as the same).
- **0** false splits (one real value treated as two different ones).
- **0** reconstructed secrets (a response stating or revealing what a
  redacted value actually was).
- **0** instances of unrunnable placeholder reuse (placeholder text
  reused in generated code in a way that would not run or compile).
- **0** instances of a placeholder being flagged as itself a security
  issue distinct from the underlying pattern.

## 8. Negative control: Properties

`edge_cases/false_positives.properties` is the experiment's one file
with **zero ground-truth sensitive values** — every line is intentionally
designed to resemble a secret without being one. Because the sanitization
engine correctly detects nothing to redact in this file, its frozen
sanitized fixture is **byte-identical** to the original. Both conditions'
sessions for this file therefore received exactly the same prompt
content.

- **5 of 6 Properties task pairs showed no difference** on any of the
  four primary dimensions — the expected result when input content is
  identical.
- **1 of 6 pairs** (`suggest_refactoring`) showed a **−2 Completeness /
  −1 Usefulness** difference, despite the two conditions' input being
  identical.

Because sanitization did not occur for this file, this single changed
pair demonstrates that the model/session setup used in this experiment
**can produce a response difference between two independently-run
sessions even when there is no input difference to explain it**. This is
not presented as a formal estimate of general AI response variance — it
is one **observed control-condition variability signal**, from one pair,
under this experiment's specific setup. It is used in this document only
to caution against attributing every observed sanitized-vs-original
difference to sanitization itself, not to quantify how much of any
specific difference is variability versus effect.

## 9. Environmental contamination

Six responses in the dataset carry a documented environmental-deviation
tag:

- `python` `explain_code`/original
- `typescript` `security_analysis`/original
- `go` `explain_code`/original
- `yaml` `explain_code`/original
- `properties` `generate_unit_tests`/original
- `properties` `generate_unit_tests`/sanitized

In each case, the affected response's text contains a reference to the
evaluation session's own working-directory name or filesystem path (in
one instance, the full absolute path). Every affected session reported
`tool_uses: 0`, meaning the information could not have come from
exploring the repository; each batch's `batch_record.md` attributes this
to ambient Claude Code subagent-runtime session-metadata exposure — a
property of the evaluation tooling itself. **These are not instances of
sanitized-credential leakage**: in every case the leaked text is the
evaluation session's own directory/path, never a scrubbed value from any
candidate file's content, and never derived from the sanitized fixture.
All 6 responses had this content explicitly excluded from scoring credit
on every dimension during human evaluation, before any statistic in this
analysis was computed.

Per the experiment's methodology, these six responses were **not**
retrospectively removed from the primary analysis (§3–§6 above include
every one of the 48 pairs). A separately-labeled sensitivity analysis
was instead performed, excluding the 5 distinct pairs touched by these 6
responses (one pair, `properties`/`generate_unit_tests`, has the tag on
both its original and sanitized response) — leaving N=43 pairs. **This
sensitivity analysis produced inferential conclusions identical to the
primary N=48 analysis** — the same raw p-values, the same Holm-adjusted
p-values, the same effect sizes, the same significance outcomes —
because none of the 5 excluded pairs contained a non-zero score
difference on any of the four primary dimensions to begin with; removing
them removes only pairs that were already contributing zero to the
paired-difference calculation.

## 10. What the experiment supports

Stated at the level of precision the data allows:

- Semantic structure in the tested files was **generally retained
  sufficiently** for the AI to perform the six tested task types, in the
  large majority of the 48 paired comparisons (41–48 of 48 pairs showed
  no change, depending on dimension).
- **Correctness and Consistency were highly stable** between conditions,
  with the single Correctness change traced to a mechanism (information
  removal preventing an original-condition error) that does not indicate
  a sanitized-condition deficiency.
- **No catastrophic placeholder-related failures were observed**: zero
  false merges, false splits, reconstructed secrets, unrunnable
  placeholder reuse, or placeholder-flagged-as-security-issue cases
  across all 96 responses; the two recorded placeholder-interpretation
  issues were both rated mild and did not affect any primary dimension.
- **Some Usefulness and Completeness reductions did occur** in the
  sanitized condition, concentrated in a minority of pairs and in
  specific tasks (`generate_unit_tests`, `suggest_refactoring`).
- **Some of these reductions are plausibly connected to intentional
  information loss** (loss of a value's realistic appearance affecting
  task engagement or severity calibration — §7).
- **Some similarly-shaped reductions are also observable under the
  byte-identical Properties control**, where no information was removed
  at all (§8).
- **The evidence therefore does not support attributing every observed
  reduction to sanitization.** Some fraction of the observed pattern is
  plausibly attributable to ordinary response variability, and this
  experiment's design does not allow that fraction to be separated from
  a genuine sanitization effect with confidence.

This document does not claim the sanitizer is proven safe, and does not
claim it has no effect. Both of those would overstate what a single
paired comparison, run once per cell, with a small number of non-zero
observations, can establish.

## 11. What the experiment does NOT establish

*Scope note: this is the complete experiment-level limitations list
(design, data, and scope). For limitations specific to the statistical
methods used in the paired analysis (test power, sample sizes,
bootstrap/CI behavior), see `inferential_results.md`'s "Statistical
limitations" (§12 there), which is intentionally narrower and does not
repeat the items below. For the short, public-facing version of this
list, see `ai-evaluation/README.md`'s "Known limitations".*

- **Only 9 files** were evaluated — a small, hand-curated set, not a
  representative sample of any broader codebase population.
- **All candidate content was synthetic benchmark content**, explicitly
  labeled as fake in each file's own header comment; no real secrets or
  production code were used.
- **One AI model/agent setup** was evaluated (Claude Code subagents
  inheriting the parent session's model, `claude-sonnet-5`) — results
  may not generalize to other models or agent architectures.
- **One response was collected per condition per (file, task) cell** —
  there was no repeated sampling within either condition, so
  within-condition variance cannot be separately estimated from this
  experiment alone.
- **A limited number of non-zero paired changes** underlie every primary
  result (1, 6, 0, and 7 out of 48 for Correctness, Completeness,
  Consistency, and Usefulness respectively) — small counts that make
  every reported statistic sensitive to individual observations.
- **Human scoring introduces evaluator judgment.** All 96 scores come
  from a single rater applying the rubric once per response; there is no
  inter-rater reliability measure.
- **No repeated runs per cell** means the experiment cannot distinguish
  a reproducible sanitization effect from a one-off session outcome with
  the same confidence a repeated-measures design would provide.
- **No production repository was evaluated** — only isolated,
  single-file fixtures.
- **No long-horizon coding-agent workflow was tested** — each task was a
  single-turn request/response, not a multi-step agentic session.
- **No tool-use, edit, compile, or test-execution loop was exercised** —
  responses were evaluated as static text output, not by actually
  running any generated code or refactor against a real build/test
  pipeline.
- **No real credentials were involved anywhere** in this experiment.
- **Language/format coverage was limited to 9 combinations** and does
  not represent broad coverage of real-world languages, frameworks, or
  credential patterns.
- **A previously-documented placeholder category-imprecision limitation
  remains** in the underlying engine (certain single-line code-variable
  patterns resolve to a generic `GENERIC_SECRET` category rather than a
  more specific one, due to regex-backtracking order) — this experiment
  did not test whether that imprecision itself affects AI task
  performance.
- **Control-condition variability is only observed, not comprehensively
  estimated.** The Properties control provides one data point showing
  that variability of a certain shape and magnitude can occur; it does
  not quantify variability across the rest of the dataset's files or
  tasks.
- **These inferential results should not be generalized beyond this
  specific experiment** — its files, its task prompts, its one model
  configuration, and its one round of scoring.

## 12. Future experiment design

The following are proposed as scientifically useful next steps. None of
them was implemented as part of this experiment or this document.

1. **Multiple independent AI runs per Original/Sanitized pair**, to
   directly estimate within-condition variance and allow a formal
   separation of treatment effect from session variability — something
   this single-run-per-cell design cannot do.
2. **More real-world repository files**, beyond hand-curated synthetic
   fixtures, to test generalization to naturally-occurring code.
3. **A larger benchmark** (more files, more task instances per
   file/task combination) to increase the number of non-zero paired
   observations available to each statistical test.
4. **Multiple AI models/agents**, to test whether observed patterns are
   specific to one model family or hold more broadly.
5. **Agentic tasks involving editing, compilation, tests, debugging, and
   refactoring** — moving beyond single-turn text responses to a full
   tool-use loop where generated code is actually executed and verified.
6. **Controlled experiments that remove only one semantic property at a
   time** (e.g., value realism, but not category; or category, but not
   length/format), to isolate which specific kind of information removal
   drives which kind of task-performance change.
7. **A three-way comparison** of generic masking, deterministic semantic
   placeholders (the approach tested here), and unmodified original
   source, to characterize the tradeoff space rather than a single
   two-condition comparison.
8. **Better control-condition replication** — deliberately including
   more byte-identical or near-identical negative-control cases across
   more languages/tasks, to build a broader, more direct picture of
   control-condition variability than the single Properties file
   currently provides.

## 13. Final discussion

This experiment examined whether replacing sensitive values in source
code with deterministic, typed placeholders preserves enough semantic
information for an AI coding agent to perform six defined
software-engineering tasks. Across 48 paired comparisons, Correctness
and Consistency showed strong stability between the original and
sanitized conditions, and no catastrophic placeholder-handling failure —
no false merge, false split, reconstructed secret, unrunnable
placeholder reuse, or placeholder misidentified as a security issue —
was observed in any of the 96 evaluated responses. At the same time, the
experiment observed some reductions in Completeness and Usefulness under
the sanitized condition, concentrated in a minority of paired
comparisons and in specific tasks. The Usefulness difference reached the
predefined statistical threshold after Holm-Bonferroni correction for
multiple comparisons; the Completeness difference did not, though it
followed a similar pattern and sits close to that threshold. Critically,
the experiment's own byte-identical negative control demonstrated that a
change of comparable shape and magnitude can occur between two
independently-run sessions with **no sanitization involved at all**,
which means response variability inherent to the model/session setup is
a plausible contributor to at least part of the observed pattern and
cannot be ruled out with the data collected here.

Taken together, this experiment provides evidence that, in this tested
setting, semantic sanitization can preserve substantial task-relevant
information for the AI coding agent across a range of task types and
languages, while also identifying specific circumstances —
particularly test generation and refactoring tasks — where information
removal, model/session variability, or some combination of the two may
reduce task usefulness. This is evidence from one controlled pilot
experiment on a small, synthetic benchmark, evaluated with a single
model configuration and a single scoring pass. It does not constitute a
general or universal claim about sanitization's effect on AI-assisted
software engineering, and it should be read, and extended, as such.
