# Inferential statistical analysis — Credential Scrubber AI experiment

**Status: descriptive statistics were already reported in
`descriptive_results.md`; this document adds formal paired hypothesis
tests, effect sizes, and confidence intervals on top of that same data.**
No human score, raw AI response, rubric, manifest, prompt, or fixture was
changed to produce this analysis. All computations are reproducible from
`ai-evaluation/experiment/analysis/run_inferential_analysis.py`, which
reads only the already-validated
`ai-evaluation/experiment/analysis/paired_deltas.csv` (48 pairs) and
`ai-evaluation/experiment/analysis/evaluation_dataset.csv` (96 rows, used
only to flag which pairs contain an environmental-deviation response for
§10's sensitivity analysis).

Language used throughout follows the task's explicit discipline:
"statistically distinguishable from zero," "observed paired difference,"
"consistent with," "exploratory," "control-condition variability" — never
causal claims, never a combined AI-performance score, never a ranking of
tasks or languages, never "winner"/"loser" framing.

---

## 1. Analysis scope

- **Primary confirmatory analysis (§3–§6):** the four always-scored
  dimensions — Correctness, Completeness, Consistency, Usefulness —
  each analyzed as **N=48 paired differences** (sanitized − original),
  never as 96 independent observations. This is the full set of primary
  tests; Holm-Bonferroni correction is applied across it.
- **Exploratory analyses (§7–§10):** task-level, language/file-level,
  the Properties negative control, and an environmental-deviation
  sensitivity analysis. These are explicitly *not* part of the
  corrected confirmatory family; no p-value from these sections should
  be read as confirmatory evidence, and no subgroup is ranked.
- **Interpretive discussion (§11):** separates score changes plausibly
  caused by sanitization's intentional information removal from changes
  that look more like an actual response/sanitizer defect or ordinary
  variability — using the qualitative evidence already recorded in each
  `human_evaluation.md`, not inferred from the numbers alone.
- Dimension 5 (`misunderstood_value`) and Dimension 6
  (`relationships_preserved`) are **not** part of this paired
  Original-vs-Sanitized analysis: Dimension 5 is N/A for every original
  response (no valid pair exists), and Dimension 6 is N/A for 90 of 96
  responses. Both were already analyzed on their own terms in
  `descriptive_results.md` §6–§7 and are not repeated here.

## 2. Statistical hypotheses

For each primary dimension *d* ∈ {Correctness, Completeness, Consistency,
Usefulness}:

- **H0(d):** the population median of the paired difference
  (sanitized − original) is 0.
- **H1(d):** the population median of the paired difference is not 0
  (two-sided).
- **Test:** Wilcoxon signed-rank test, `zero_method="wilcox"` (pairs with
  a difference of exactly 0 are dropped before ranking — the classic
  Wilcoxon treatment; documented explicitly per dimension below since it
  changes the effective N for the test itself, though not for the
  reported N of pairs).
- **α = 0.05**, two-sided, with Holm-Bonferroni step-down correction
  applied across the dimensions that produced a valid p-value.

## 3. Primary paired tests

| Dimension | N pairs | Non-zero pairs | Wilcoxon statistic | Raw p-value | Direction of observed median |
|---|---:|---:|---:|---:|---|
| Correctness | 48 | 1 | 0.0 | 0.3173 | median = 0 (1 pair moved, +1; see note) |
| Completeness | 48 | 6 | 0.0 | 0.0264 | median = 0 (6 pairs moved, all −1 to −3; see note) |
| Consistency | 48 | 0 | — | — | no observed difference in any of the 48 pairs |
| Usefulness | 48 | 7 | 0.0 | 0.0158 | median = 0 (7 pairs moved, all −1 to −3; see note) |

**Reading the "median = 0" rows correctly:** with 41–47 of 48 pairs
showing a difference of exactly 0, the **median** of all 48 paired
differences is 0 for every dimension, including Completeness and
Usefulness. The Wilcoxon signed-rank test is **not** a test of whether
the median differs from 0 in the naive point-estimate sense — it tests
whether the *distribution* of signed ranks of the non-zero differences
is symmetric around 0, i.e., whether there is directional asymmetry
among the differences that did occur. For Completeness and Usefulness,
every single one of the non-zero differences pointed in the same
direction (negative — sanitized scored lower than its paired original in
every case where a difference occurred at all, zero cases the other
way), which is what produces a small p-value despite the flat median.
This distinction is easy to misread and is stated here explicitly to
avoid it.

**Consistency** — reported exactly as specified, not manufactured: all
48 paired differences equal 0. `scipy.stats.wilcoxon` with
`zero_method="wilcox"` has no non-zero differences to rank and cannot
produce a statistic or p-value. **The Wilcoxon signed-rank test is not
applicable / degenerate for Consistency. No p-value is reported.**

**Correctness** — technically non-degenerate (1 non-zero pair exists,
so scipy does return a statistic and p-value), but flagged here as very
low-powered: a two-sided test built on a single non-zero difference
out of 48 pairs has essentially no ability to distinguish a real,
reproducible effect from a one-off event, and its p-value (0.317, not
distinguishable from zero at α=0.05) should be read with that caveat
rather than as evidence of "no effect" in any strong sense — there is
simply almost no signal to test.

## 4. Effect sizes

Matched-pairs rank-biserial correlation (Kerby 2014 "simple difference"
formula), computed from the signed ranks of |non-zero differences|:
r_rb = (W+ − W−) / (W+ + W−), range [−1, +1]. Reported as magnitude and
direction only, per instruction — not labeled "important"/"unimportant."

| Dimension | Effect size (r_rb) | Direction | What it reflects here |
|---|---:|---|---|
| Correctness | +1.00 | positive | The single non-zero pair moved in the positive (sanitized-higher) direction; with only one non-zero pair, r_rb is mechanically ±1 regardless of magnitude — it reflects perfect directional consistency among *one* data point, not a strong general effect. |
| Completeness | −1.00 | negative | All 6 non-zero pairs moved in the negative (sanitized-lower) direction — perfect directional consistency among those 6 pairs. |
| Consistency | not applicable | — | No non-zero pairs exist; rank-biserial correlation is undefined (no ranks to compute). |
| Usefulness | −1.00 | negative | All 7 non-zero pairs moved in the negative (sanitized-lower) direction — perfect directional consistency among those 7 pairs. |

**Important reading note:** because this effect size is computed only
from the non-zero differences, a value of exactly ±1.0 here means "every
pair that changed, changed in the same direction" — it does **not** mean
"every pair changed," and it does not by itself convey how *often* a
change occurred (41–47 of 48 pairs showed no change at all for these
three dimensions). The rate of change (6/48, 7/48, 1/48) and the
direction-consistency (r_rb) are two separate pieces of information;
both are needed together, and neither should be quoted alone.

## 5. Confidence intervals

**Method:** bootstrap for the median paired difference. BCa
(bias-corrected and accelerated) was attempted first via
`scipy.stats.bootstrap(method="BCa")`; for every one of the four primary
dimensions, BCa returned `NaN` bounds (`DegenerateDataWarning`/
`RuntimeWarning: invalid value encountered in scalar divide` — the
underlying jackknife acceleration estimate is undefined here because the
statistic, the median, is a step function that is locally constant
across the overwhelming majority of resamples, which breaks the
smoothness assumption BCa's acceleration correction relies on). Per
instruction, the script fell back to a **percentile bootstrap**, using
the same fixed seed, and this fallback is stated explicitly rather than
silently substituted.

- **Bootstrap method:** percentile bootstrap (BCa attempted and found
  unavailable for this statistic/data combination; documented per
  dimension in `inferential_results.csv`'s `ci_method` column).
- **Resamples:** 10,000 per dimension.
- **Random seed:** 42 (fixed; `numpy.random.default_rng(42)`).
- **Confidence level:** 95% (α=0.05, two-sided percentiles: 2.5th /
  97.5th).

| Dimension | 95% CI (median paired difference) | Note |
|---|---|---|
| Correctness | [0.0, 0.0] | With only 1 of 48 differences non-zero, the resampled median is 0 in the overwhelming majority of the 10,000 bootstrap resamples — the CI collapses to a point at 0. |
| Completeness | [0.0, 0.0] | With only 6 of 48 differences non-zero, the same mechanism applies. |
| Consistency | [0.0, 0.0] | Degenerate: all 48 values are identical (0), so every possible resample has median exactly 0 — the CI is a point by construction, not by a fallback method. |
| Usefulness | [0.0, 0.0] | With only 7 of 48 differences non-zero, the same mechanism applies. |

**This is a real, correctly-computed result, not an error.** A
median-based CI on a sample where the value 0 constitutes a strict
majority (85%+ of pairs, for every dimension) will typically be a point
mass at 0, even when the Wilcoxon test (which is sensitive to the
signed-rank distribution, not the median) reports a small p-value. The
two statistics are answering different questions: the CI describes
uncertainty in the *typical* pair's difference (which is unambiguously
0 for the large majority), while the Wilcoxon test asks whether the
*pattern* of non-zero differences is more one-directional than chance
would predict. Reporting only one of the two would be misleading; both
are given together here for that reason. **No causal interpretation is
implied by either.**

## 6. Holm-Bonferroni correction

Applied across the primary dimensions that produced a valid p-value.
**Consistency is excluded from the correction family** — it has no
p-value to correct (§3), and including a manufactured value (e.g. p=1)
would not represent an actual hypothesis test. The family therefore has
m=3 tests (Correctness, Completeness, Usefulness), ranked by raw p-value
ascending, each multiplied by its Holm step-down weight
(m − rank + 1), enforcing monotonicity:

| Rank | Dimension | Raw p-value | Holm weight | Holm-adjusted p-value | Distinguishable from zero at α=0.05? |
|---:|---|---:|---:|---:|---|
| 1 | Usefulness | 0.01576 | ×3 | 0.04729 | **Yes** |
| 2 | Completeness | 0.02643 | ×2 | 0.05287 | No (just above 0.05) |
| 3 | Correctness | 0.31731 | ×1 | 0.31731 | No |
| — | Consistency | not applicable | — | not applicable | not applicable (no test performed) |

**After Holm-Bonferroni correction across the primary family, only
Usefulness remains statistically distinguishable from zero at α=0.05.**
Completeness's adjusted p-value (0.0529) sits just above the 0.05
threshold — this is reported exactly as computed, not rounded down or
described as "essentially significant"; it is a paired difference whose
raw evidence is comparable in direction and magnitude to Usefulness's
but does not clear the corrected threshold. Correctness does not
approach the threshold either before or after correction. Consistency
was not tested and makes no contribution to, or claim from, this family.

**This does not establish that sanitization causes lower Usefulness
scores.** It establishes that, within this paired dataset, the observed
pattern of Usefulness differences is unlikely to have arisen from a
symmetric (no-directional-preference) process, under the assumptions of
the Wilcoxon test, after adjusting for testing four dimensions.
Attribution to sanitization specifically — as opposed to task-specific
model behavior, ordinary session variability, or a mix — requires the
qualitative and control-condition evidence in §9–§11.

---

## 7. Task-level exploratory analysis

**Exploratory only — not part of the corrected confirmatory family. No
task is ranked, and no subgroup p-value below is treated as
confirmatory evidence**, both because these are secondary analyses run
without their own multiple-comparison correction and because most
subgroup sample sizes (N=9, or N=3 for `explain_config_relationships`)
are too small for a two-sided Wilcoxon test to have meaningful power —
several of the p-values below are exactly 1.0, 0.5, or 0.25, which are
artifacts of very small non-zero counts (a Wilcoxon test on 1–4 non-zero
paired differences has very few possible rank permutations and thus a
coarse, discrete p-value distribution) rather than evidence of "no
effect."

| Task | N pairs | Dimension | Non-zero | Median Δ | Mean Δ | Exploratory Wilcoxon p |
|---|---:|---|---:|---:|---:|---:|
| `explain_code` | 9 | all four | 0 | 0 | 0.000 | not computed (no non-zero differences) |
| `identify_bug` | 9 | all four | 0 | 0 | 0.000 | not computed (no non-zero differences) |
| `security_analysis` | 9 | Completeness | 1 | 0 | −0.111 | 1.000 |
| `security_analysis` | 9 | Usefulness | 1 | 0 | −0.111 | 1.000 |
| `generate_unit_tests` | 9 | Completeness | 2 | 0 | −0.667 | 0.500 |
| `generate_unit_tests` | 9 | Usefulness | 2 | 0 | −0.667 | 0.500 |
| `suggest_refactoring` | 9 | Correctness | 1 | 0 | +0.111 | 1.000 |
| `suggest_refactoring` | 9 | Completeness | 3 | 0 | −0.556 | 0.250 |
| `suggest_refactoring` | 9 | Usefulness | 4 | 0 | −0.556 | 0.125 |
| `explain_config_relationships` | 3 | all four | 0 | 0 | 0.000 | not computed (N too small, no non-zero differences) |

Consistency showed 0 non-zero differences in every task (omitted from
the table for brevity — always N/A/degenerate, same as the primary
result).

**`generate_unit_tests`, `security_analysis`, `suggest_refactoring`,
`explain_config_relationships`** — the four tasks flagged for attention:

- **`generate_unit_tests`:** the largest per-pair magnitude in the whole
  dataset (−3 on both Completeness and Usefulness, in 2 of 9 pairs —
  `javascript` and `yaml`). Exploratory p=0.500 reflects that a
  two-sided sign test on 2 non-zero, same-direction differences out of 9
  pairs is the smallest possible non-trivial sample for this test and
  cannot be distinguished from chance at any conventional threshold —
  this is a **descriptive, not inferential**, red flag: worth continued
  attention because of magnitude and the qualitative mechanism recorded
  in `descriptive_results.md` §4, not because of this p-value.
- **`security_analysis`:** only 1 of 9 pairs changed (`python`,
  Completeness and Usefulness both −1). Exploratory p=1.000 (the
  weakest possible evidence against H0 for a Wilcoxon test).
- **`suggest_refactoring`:** the most pairs affected of any task (3/9
  Completeness, 4/9 Usefulness, plus the dataset's one Correctness
  increase). Exploratory p=0.125–0.250, still not below any conventional
  threshold, and again too few non-zero pairs for the test to carry real
  power. This task's pattern is discussed further against the Properties
  negative control in §9 — the same shape of change occurred there with
  no sanitization at all.
- **`explain_config_relationships`:** 0 non-zero differences across all
  3 applicable pairs on all four dimensions — the cleanest, most uniform
  result of any task, though N=3 is the smallest subgroup in the
  dataset.

## 8. Language/file-type exploratory analysis

**Exploratory only.** No language is ranked, and no claim is made that
any language is "more" or "less" affected — the table below is a plain
restatement of paired-difference counts per language, offered only to
show where the (already small) set of non-zero pairs falls.

| Language/file | N pairs | Completeness: non-zero (mean Δ) | Usefulness: non-zero (mean Δ) |
|---|---:|---|---|
| `java` | 5 | 0 (0.000) | 0 (0.000) |
| `python` | 5 | 1 of 5 (−0.200) | 1 of 5 (−0.200) |
| `javascript` | 5 | 1 of 5 (−0.600) | 1 of 5 (−0.600) |
| `typescript` | 5 | 0 (0.000) | 1 of 5 (−0.200) |
| `go` | 5 | 1 of 5 (−0.200) | 1 of 5 (−0.200) |
| `csharp` | 5 | 1 of 5 (−0.400) | 1 of 5 (−0.400) |
| `json` | 6 | 0 (0.000) | 0 (0.000) |
| `yaml` | 6 | 1 of 6 (−0.500) | 1 of 6 (−0.500) |
| `properties` | 6 | 1 of 6 (−0.333) | 1 of 6 (−0.167) |

Correctness and Consistency are omitted from this table — every language
shows 0 non-zero pairs on Consistency, and only `json` shows a single
non-zero Correctness pair (already discussed in §3/§9). Formal Wilcoxon
tests were not run per language: with N=5 or N=6 pairs and at most 1
non-zero difference in almost every case, a per-language test would have
even less power than the per-task tests in §7 and would not add
information beyond the counts already shown here. Each language's single
non-zero pair (where one exists) corresponds to exactly one of the
task-level cases already discussed in §7 — no additional, purely
language-driven pattern is observed beyond what the task breakdown
already shows.

## 9. Properties negative-control analysis

`edge_cases/false_positives.properties` is the experiment's one file
where the sanitized fixture is **byte-identical** to the original (zero
ground-truth detections). All 6 of its task pairs therefore received
literally identical prompt content in both conditions — this makes it a
direct control for model/session variability, independent of any
sanitization effect, because no sanitization occurred here at all.

| Task | Δ Correctness | Δ Completeness | Δ Consistency | Δ Usefulness |
|---|---:|---:|---:|---:|
| `explain_code` | 0 | 0 | 0 | 0 |
| `identify_bug` | 0 | 0 | 0 | 0 |
| `security_analysis` | 0 | 0 | 0 | 0 |
| `generate_unit_tests` | 0 | 0 | 0 | 0 |
| `suggest_refactoring` | 0 | **−2** | 0 | **−1** |
| `explain_config_relationships` | 0 | 0 | 0 | 0 |

- **N properties pairs = 6.**
- **Changed pairs = 1 of 6** (`suggest_refactoring`); magnitude −2
  (Completeness) and −1 (Usefulness).
- **5 of 6 pairs show zero difference on every dimension**, as expected
  when the two conditions' input is identical.

**Interpretation, stated at the scope this single observation
supports:** this is not a formal estimate of "how much AI variance
exists in general" — it is the variability observed **under this
experiment's one control condition**, from a single pair. It demonstrates
that a paired difference of this magnitude and direction (−2/−1, the
same shape as several of the `suggest_refactoring` changes reported in
§7) **can occur with zero possible sanitization effect**, which is
sufficient to show that ordinary session variability is a real,
non-negligible competing explanation for at least part of the
`suggest_refactoring` pattern elsewhere in the dataset. It does not show
what fraction of the non-control `suggest_refactoring` changes (in `go`,
`csharp`, `typescript`) are variability versus a genuine effect of
sanitization — distinguishing those would require repeated sampling
under both conditions, which this experiment (one response per
condition per file/task) was not designed to do.

## 10. Environmental-deviation sensitivity analysis

**Clearly labeled as a sensitivity check, not a replacement for the
primary analysis in §3–§6.** Per instruction, the 6 documented
environmental-deviation responses (see `descriptive_results.md` §9) were
**not** removed from the primary analysis — §3–§6 above include every
one of the 48 pairs. This section additionally reports what changes if
the pairs containing a deviation-affected response are excluded, as an
explicit check on whether the primary conclusions depend on them.

The 6 deviation-tagged responses fall within **5 distinct pairs** (one
pair, `properties`/`generate_unit_tests`, has a deviation tag on *both*
its original and sanitized response):

- `python` / `explain_code`
- `typescript` / `security_analysis`
- `go` / `explain_code`
- `yaml` / `explain_code`
- `properties` / `generate_unit_tests`

Excluding these 5 pairs leaves **N=43 pairs**.

| Dimension | N (sensitivity) | Non-zero | Raw p | Holm-adj p | Effect size (r_rb) | Distinguishable at α=0.05 after Holm? |
|---|---:|---:|---:|---:|---:|---|
| Correctness | 43 | 1 | 0.3173 | 0.3173 | +1.00 | No |
| Completeness | 43 | 6 | 0.0264 | 0.0529 | −1.00 | No |
| Consistency | 43 | 0 | not applicable | not applicable | not applicable | not applicable |
| Usefulness | 43 | 7 | 0.0158 | 0.0473 | −1.00 | **Yes** |

**Comparison to the primary (N=48) analysis: every raw p-value, Holm-
adjusted p-value, effect size, and significance conclusion is identical
to §3–§6.** This is expected and mechanically explained, not a
coincidence to read into further: none of the 6 environmental-deviation
responses belonged to a pair with a non-zero delta on any of the four
primary dimensions (all 6 deviation-affected responses scored 5/5/5/5 —
see `descriptive_results.md` §9) — removing them removes only pairs that
were already contributing a 0 to the Wilcoxon calculation (which drops
zeros regardless), so the non-zero data driving every test is completely
untouched. Mean deltas shift very slightly (the denominator changes from
48 to 43) but medians, ranks, p-values, and Holm results do not change
at all. **The primary conclusions do not depend on the environmental
deviations.** As throughout this analysis, these deviations are read as
tooling/session-metadata artifacts, not as evidence of sanitizer
leakage.

---

## 11. Information-loss mechanism vs. sanitizer-failure interpretation

Not every score decrease in this dataset represents the same kind of
event. Cross-referencing the paired-difference cases above against the
qualitative evidence recorded in each `human_evaluation.md` (not
inferred from the numeric deltas alone) separates them into three kinds:

### (a) Plausibly explained by sanitization's *intended* information
removal (an accepted cost of the approach, not a defect)

- **`javascript` and `yaml` `generate_unit_tests` (−3/−3):** the
  sanitized-condition response is recorded as declining to write any
  test code, reasoning from the visible placeholder syntax toward a
  broader "this whole file is an external fixture" conclusion — a
  plausible behavioral consequence of replacing a realistic-looking
  secret with a generic semantic placeholder, distinct from any error in
  handling the placeholder itself.
- **`yaml` `security_analysis`/`identify_bug` (no scored delta, but a
  documented qualitative effect):** `session_key`'s real value is the
  non-secret-looking word `dummy`; the engine still sanitizes it to
  `<GENERIC_SECRET_1>`, a placeholder indistinguishable from a genuine
  secret. The original-condition response could see the value was
  trivial and made a calibrated Medium-severity judgment; the sanitized
  response reasonably treated the placeholder at face value and judged
  it High severity. This did not change any of the four primary
  dimension scores (both responses were independently judged thorough),
  but it is a clean, directly observed example of sanitization
  **removing the information a severity judgment depends on** — exactly
  the mechanism the task brief asks to be distinguished from a defect.
- **`json` `suggest_refactoring` (the dataset's one Correctness
  increase):** the original-condition response made a minor factual
  error reproducing a secret's literal prefix in an illustrative
  example; the sanitized-condition response could not make the
  analogous error because it had no literal value to reproduce.
  Information removal here *prevented* an error rather than causing a
  decrease — included here as the same mechanism working in the
  opposite direction.

### (b) Not clearly attributable to sanitization's information removal —
more consistent with ordinary response variability

- **`go` and `csharp` `suggest_refactoring` (−1/−1 and −2/−2):** both
  sanitized-condition responses left a real security fix (secret
  redaction; removal of console-logging) unimplemented in delivered
  code, despite demonstrably having all the information needed to
  implement it (each response's own `security_analysis` sibling
  correctly identified the same issue). This is not an information-loss
  effect — nothing about the fix depends on knowing the actual secret
  value. The `properties`/`suggest_refactoring` control pair (§9) shows
  an equivalently-shaped decrease with **zero information difference**
  between conditions, which is direct evidence that this specific
  pattern can arise from ordinary variability alone. These two cases are
  therefore best read as **ambiguous between "ordinary variability" and
  "an effect of sanitization"** — the data available does not
  distinguish them, and neither is asserted here.
- **`python` and `json` `security_analysis` (−1/−1 each):** both
  decreases trace to specific missed observations that the evaluations
  confirm were independently findable directly in the *sanitized* file
  (not dependent on the redacted values) — i.e., information that
  remained available but was not used. This is response-thoroughness
  variation, not information loss.
- **`typescript` `suggest_refactoring` (Usefulness −1 only):** the
  sanitized response's delivered refactor left placeholder literals
  hardcoded in the "after" code rather than sourcing them from
  environment variables. Unlike (a), the placeholder's presence may have
  made it easier to paste as-is rather than externalize it — a plausible
  but unconfirmed information-adjacent behavioral effect, distinct from
  a placeholder-understanding defect (the response never misidentifies
  or misuses the placeholder's type). Presented here as ambiguous, not
  resolved.

### (c) Actual response-side placeholder-handling issues (closest to a
"sanitizer defect" in the AI-response sense, though neither is a scoring
or engine defect)

- **`java` `generate_unit_tests`/sanitized:** `placeholder_as_real_value`
  — a placeholder was used as an ordinary test-fixture literal with no
  acknowledgment it was substituted; the evaluation records this as mild
  and notes the resulting test is still factually correct and would
  pass.
- **`java` `explain_code`/sanitized:** `inferred_placeholder_value` — the
  response speculated (backwards) about the substitution mechanism; the
  evaluation records this as hedged and inconsequential to the response's
  main content.

Neither (c) case involved a false merge, false split, reconstructed
secret, placeholder flagged as a security issue, or unrunnable
placeholder reuse — none of those occurred anywhere in the 96 responses
(§8 of `descriptive_results.md`), and both (c) cases are the only two
sanitized-condition responses in the whole dataset that scored below 5
on Dimension 5 (§6 of `descriptive_results.md`).

**No statistical procedure in this document performed this
classification** — it is a qualitative cross-reference against each
response's recorded evidence text, reported here because the task brief
explicitly asks that it not be conflated with "every decrease counted as
sanitization damage."

## 12. Statistical limitations

*Scope note: this section covers limitations of the statistical methods
used in this document only (test power, sample sizes feeding each test,
bootstrap/CI behavior). It is deliberately narrower than the complete
experiment-level limitations list in `results_and_discussion.md`'s
"What the experiment does NOT establish" (§11 there) - e.g. the
synthetic-benchmark, single-model, and no-production-repository
limitations are experiment design choices, not statistical-method
limitations, and are documented there instead of being duplicated here.*

- **Small non-zero counts drive every primary result.** Completeness and
  Usefulness rest on 6 and 7 non-zero pairs respectively out of 48;
  Correctness rests on exactly 1. Wilcoxon p-values and rank-biserial
  effect sizes computed from this few non-zero observations are
  correctly calculated but inherently fragile — a small number of
  additional or differently-signed observations could move the
  conclusion substantially. This is stated, not smoothed over, in every
  relevant section above.
- **The point-mass-at-zero median and its degenerate bootstrap CI are a
  real feature of this data, not a limitation of the method** — but they
  mean the CI in §5 answers a different question than the Wilcoxon test
  in §3, and reporting either alone would be incomplete (see §5's
  explanation).
- **Task- and language-level exploratory analyses have very low power**
  (N=9 or fewer pairs, frequently 1–4 non-zero differences) and were
  explicitly not corrected for multiple comparisons, consistent with the
  instruction to reserve Holm-Bonferroni for the four primary
  dimensions only. Their p-values (where computed at all) should not be
  read as confirmatory.
- **This experiment provides one response per condition per (file,
  task) cell** — there is no repeated sampling under either condition,
  so within-condition variance (how much a single condition's response
  would vary on its own across repeated runs) cannot be separately
  estimated from this data. The Properties control (§9) provides exactly
  one data point of what a zero-information-difference paired comparison
  looks like; it is suggestive, not a variance estimate.
- **Single human rater, single scoring pass** (carried over from
  `descriptive_results.md`'s limitations) — no inter-rater reliability
  measure exists for any of the 96 underlying scores this analysis is
  built on.
- **BCa bootstrap was not achievable for any of the four primary
  dimensions** given this data's structure (a step-function statistic
  over a majority-constant sample); the percentile-bootstrap fallback is
  a documented, standard alternative, but it is a less refined interval
  than BCa would have provided had it been computable.
- **Statistical distinguishability from zero is not evidence of cause.**
  Nothing in this document establishes that sanitization *causes* the
  Usefulness pattern reported in §6 — only that the pattern, as observed
  in this dataset, is unlikely under a symmetric-random-direction null
  model, after correcting for testing four dimensions. §11 and §9's
  control evidence are offered as the closest available step toward
  mechanism, and even they leave several cases explicitly unresolved.

## 13. Results suitable for research discussion

For direct reuse in a subsequent write-up, stated in the neutral register
used throughout this document:

- Across 48 paired (original, sanitized) response comparisons, paired
  differences on Correctness and Consistency were negligible-to-absent
  (Consistency: exactly zero in all 48 pairs; Correctness: one pair out
  of 48 changed). Completeness and Usefulness each showed a paired
  difference in a minority of comparisons (6/48 and 7/48 respectively),
  and in every one of those cases the change was in the same direction
  (sanitized scored lower than its paired original).
- A two-sided Wilcoxon signed-rank test, applied to each of the four
  primary dimensions across all 48 pairs and corrected for multiple
  comparisons via Holm-Bonferroni, found the Usefulness paired
  difference statistically distinguishable from zero at α=0.05
  (Holm-adjusted p=0.047); Completeness approached but did not cross this
  threshold (Holm-adjusted p=0.053); Correctness did not approach it;
  Consistency could not be tested (no observed differences).
- Matched-pairs rank-biserial correlations for Completeness and
  Usefulness were both −1.00, reflecting that every non-zero paired
  difference for these two dimensions pointed in the same (sanitized-
  lower) direction — not that every pair changed, nor the size of a
  "general" effect.
- A sensitivity analysis excluding all 5 pairs touched by a documented
  environmental deviation (N=43) reproduced every p-value, effect size,
  and Holm-adjusted conclusion from the full N=48 analysis exactly,
  because none of the excluded pairs contributed a non-zero difference.
- A within-experiment control condition (`properties`, byte-identical
  input in both conditions) showed a paired-difference of the same shape
  and comparable magnitude to part of the observed `suggest_refactoring`
  pattern (−2 Completeness / −1 Usefulness) with no sanitization having
  occurred, indicating that ordinary session-to-session response
  variability is a plausible contributor to at least part of the
  observed pattern and cannot be ruled out by this dataset alone.
- Qualitative cross-referencing separated the observed decreases into
  those plausibly explained by sanitization's intended information
  removal (e.g., loss of a value's realistic appearance affecting task
  engagement or severity calibration), those better explained by
  ordinary response variability (supported directly by the control
  condition), and a small number (2 of 96 responses) of genuine
  placeholder-handling imprecision in the AI's responses, both rated
  mild by the human evaluator and neither involving a false merge, false
  split, reconstructed secret, or unrunnable code.
