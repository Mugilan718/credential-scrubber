# Descriptive statistical analysis — Credential Scrubber AI experiment

**Status: descriptive only.** No hypothesis tests, p-values, confidence
intervals, effect-size significance claims, or multiple-comparison
corrections were performed. No overall "AI performance score" or
ranking of tasks/languages/conditions was created. All numbers below are
computed directly from `ai-evaluation/experiment/analysis/evaluation_dataset.csv`
(96 rows) and `ai-evaluation/experiment/analysis/paired_deltas.csv` (48
rows), both of which were produced without altering any score.

Throughout, "sanitized − original" is reported as a **paired
difference**, not a judgment. Where a pattern is discussed, the report
explicitly separates four possible explanations per the task brief:
(1) effects plausibly caused by sanitization itself, (2) ordinary
AI response variability, (3) environmental/protocol contamination
unrelated to sanitization, and (4) information intentionally removed by
sanitization (a known, accepted cost of the approach, not a defect).

---

## 1. Dataset overview

- 96 scored responses: 48 `original`, 48 `sanitized`.
- 48 paired (file × task) comparisons, each with one `original` and one
  `sanitized` response, spanning 9 candidate files (6 source-code
  languages × 5 tasks = 30 pairs; 3 config-shaped files × 6 tasks = 18
  pairs — but `explain_config_relationships` is `not_applicable` for the
  6 source-code files, so those 6 files contribute 5 pairs each = 30,
  and the 3 config-shaped files contribute 6 pairs each = 18; 30+18=48).
- Dimension 5 (`misunderstood_value`) is scored only for the 48
  `sanitized` responses (N/A for all 48 `original` responses, per rubric
  design — original responses have no placeholder to misunderstand).
- Dimension 6 (`relationships_preserved`) is scored for only 6 of the 96
  responses — the `explain_config_relationships` task on
  `json`/`yaml`/`properties`, both conditions — per the Dimension 6
  Methodology Resolution in `scoring_integrity_audit.md`. The other 90
  responses are N/A on this dimension and are excluded from its
  denominator throughout.
- 6 of the 96 responses carry a documented environmental-deviation
  failure-mode tag (isolated ambient working-directory/session-metadata
  leakage; see §9). All 6 were already excluded from scoring credit
  during human evaluation — their numeric scores in this dataset reflect
  only their legitimate task content.

## 2. Overall Original vs. Sanitized statistics

N = 48 per condition for each of the four always-scored dimensions.

| Dimension | Condition | N | Mean | Median | Std. dev. | Min | Max |
|---|---|---:|---:|---:|---:|---:|---:|
| Correctness | original | 48 | 4.979 | 5 | 0.144 | 4 | 5 |
| Correctness | sanitized | 48 | 5.000 | 5 | 0.000 | 5 | 5 |
| Completeness | original | 48 | 5.000 | 5 | 0.000 | 5 | 5 |
| Completeness | sanitized | 48 | 4.750 | 5 | 0.729 | 2 | 5 |
| Consistency | original | 48 | 5.000 | 5 | 0.000 | 5 | 5 |
| Consistency | sanitized | 48 | 5.000 | 5 | 0.000 | 5 | 5 |
| Usefulness | original | 48 | 5.000 | 5 | 0.000 | 5 | 5 |
| Usefulness | sanitized | 48 | 4.750 | 5 | 0.700 | 2 | 5 |

Observed pattern: Correctness and Consistency show essentially no
observed spread in either condition (one single original-condition
Correctness score of 4; otherwise every value is 5). Completeness and
Usefulness show all of the observed spread, and all of it is on the
sanitized side — every one of the 48 original-condition responses scored
a flat 5 on both dimensions, with no exceptions.

**Dimension 6** (6 applicable responses only — see §7 for full detail):
N=6, mean=5.000, median=5, std. dev.=0.000, min=5, max=5. Split by
condition: original N=3 (mean 5.0), sanitized N=3 (mean 5.0). No
variation observed at all on this dimension, in either condition — but
N=6 is far too small to draw any general conclusion from this alone.

## 3. Paired delta analysis (sanitized − original), N = 48 pairs

| Dimension | N | Improved | Unchanged | Decreased | Mean Δ | Median Δ | Std. dev. Δ | Min Δ | Max Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Correctness | 48 | 1 | 47 | 0 | 0.021 | 0 | 0.144 | 0 | +1 |
| Completeness | 48 | 0 | 42 | 6 | −0.250 | 0 | 0.729 | −3 | 0 |
| Consistency | 48 | 48 unchanged | — | — | 0.000 | 0 | 0.000 | 0 | 0 |
| Usefulness | 48 | 0 | 41 | 7 | −0.250 | 0 | 0.700 | −3 | 0 |

Delta distributions (count of pairs at each delta value; only non-zero
buckets shown for brevity, all others = 0):

- **Correctness:** 0 → 47, +1 → 1.
- **Completeness:** 0 → 42, −1 → 2, −2 → 2, −3 → 2.
- **Consistency:** 0 → 48 (no pair showed any change).
- **Usefulness:** 0 → 41, −1 → 4, −2 → 1, −3 → 2.

Observed pattern, stated plainly and without attributing cause yet:
across 48 paired comparisons, Correctness and Consistency were
essentially unchanged by condition (Consistency never changed in a
single pair; Correctness changed in exactly one pair, upward).
Completeness and Usefulness each decreased in the sanitized condition
relative to their paired original in 6–7 of 48 pairs (12.5%–14.6%), never
increased, and were unchanged in the remaining 41–42 pairs (85.4%–87.5%
of all pairs). The single Correctness increase (`json` /
`suggest_refactoring`) is traced in the qualitative evidence to the
*original*-condition response containing a minor factual-reproduction
slip (an illustrative "actual value" example that dropped a `fake-`
prefix present in the real source literal) — the sanitized response
scored higher there specifically because it never attempted to
reconstruct a literal secret value in the first place, not because
sanitization made its reasoning more correct in a general sense.

## 4. Task-level analysis

`N/A` task/file combinations per the frozen manifest: `explain_config_relationships`
is `not_applicable` for all 6 source-code files (`java`, `python`,
`javascript`, `typescript`, `go`, `csharp`) and was never run or scored
for them — those files contribute 0 pairs to this task, not N/A rows.

| Task | N pairs | Correctness Δ (mean / dist of non-zero) | Completeness Δ (mean / dist) | Consistency Δ | Usefulness Δ (mean / dist) |
|---|---:|---|---|---|---|
| `explain_code` | 9 | 0.000 (none) | 0.000 (none) | 0.000 | 0.000 (none) |
| `identify_bug` | 9 | 0.000 (none) | 0.000 (none) | 0.000 | 0.000 (none) |
| `security_analysis` | 9 | 0.000 (none) | −0.111 (−1 ×1) | 0.000 | −0.111 (−1 ×1) |
| `generate_unit_tests` | 9 | 0.000 (none) | −0.667 (−3 ×2) | 0.000 | −0.667 (−3 ×2) |
| `suggest_refactoring` | 9 | +0.111 (+1 ×1) | −0.556 (−1 ×1, −2 ×2) | 0.000 | −0.556 (−1 ×3, −2 ×1) |
| `explain_config_relationships` | 3 | 0.000 (none) | 0.000 (none) | 0.000 | 0.000 (none) |

### `generate_unit_tests` (flagged for attention)

The 2 Completeness/Usefulness decreases (both −3, the largest single-pair
drop observed anywhere in this dataset) are `javascript` and
`config-yaml`/`settings.yaml`. In both, the qualitative evaluation
records the sanitized-condition response declining to write **any** test
code, where the paired original-condition response delivered real,
working tests against materially the same testable surface (a concrete
function in JavaScript; a legitimate schema/structural-validation
opportunity in YAML). Both evaluations explicitly note the omitted
content was independently, structurally derivable from the sanitized
file alone (not dependent on the redacted secret values) — this is the
pattern most plausibly attributable to a *sanitization-related* effect
in this dataset: the presence of placeholder syntax appears, in these
two cases, to have contributed to the model judging the *whole file* not
worth testing, rather than only declining to test the specific redacted
values. This is a plausible-cause observation from 2 of 48 pairs, not a
general finding — the other 7 `generate_unit_tests` pairs (including
`go`, `csharp`, `typescript`, `java`, `python`, `json`, `properties`)
showed zero divergence, several with the sanitized condition matching or
slightly exceeding the original in thoroughness.

### `security_analysis` (flagged for attention)

Only 1 of 9 pairs decreased (`python`, both Completeness and Usefulness,
−1 each). The evaluation attributes this to two specific,
independently-verifiable omissions in the sanitized response (secrets
mixed with non-secret config; the `production`-environment risk context)
— both were judged findable directly in the sanitized file, i.e. **not**
dependent on the redacted values, making this a case of ordinary
response-thoroughness variation rather than an inherent sanitization
limitation. The other 8 `security_analysis` pairs showed no decrease;
several sanitized responses in this task were recorded as *more*
thorough than their paired original (new findings not present in the
original), which does not appear in these aggregate numbers because
Completeness/Usefulness were not raised above the ceiling of 5.

### `suggest_refactoring` (flagged for attention)

This task shows the most decreases (3 of 9 for Completeness, 4 of 9 for
Usefulness) and the only observed increase (Correctness, `json`, see
§3). The 3 Completeness/Usefulness decreases are `go` (−1/−1), `csharp`
(−2/−2), and `properties` (−2/−1); a 4th Usefulness-only decrease is
`typescript` (−1). In `go` and `csharp`, the qualitative evaluations
record the sanitized-condition refactor as leaving a real, functioning
security fix (secret redaction in Go; removal of console-logging in C#)
unimplemented in the delivered code, despite the paired original
condition's refactor implementing it and despite the same response's own
`security_analysis` sibling having identified the issue. This is
directly observable in the delivered code, independent of comparison,
but **whether it is caused by sanitization** cannot be established from
this data alone — see §9, where the `properties`/`suggest_refactoring`
pair (byte-identical input in both conditions) shows an equivalent
Completeness/Usefulness drop with **no sanitization having occurred at
all**, which is evidence that at least part of this task's pattern may
reflect ordinary session-to-session variability rather than an effect of
redaction.

### `explain_config_relationships` (flagged for attention)

All 3 applicable pairs (`json`, `yaml`, `properties`) show zero delta on
every dimension, including Dimension 6 (§7). The qualitative evaluations
record no false merge or false split in any of the 6 responses in this
task. This is the task Dimension 6 exists to test, and — descriptively,
within the limits of N=3 pairs / N=6 responses — it shows the cleanest,
most uniform result of any task in the dataset.

## 5. Language/file-type analysis

No ranking is implied by table order (alphabetical). N pairs = 5 for the
6 source-code languages (no `explain_config_relationships`), 6 for the 3
config-shaped files.

| Language/file | N pairs | Correctness Δ mean (dist) | Completeness Δ mean (dist) | Consistency Δ mean | Usefulness Δ mean (dist) |
|---|---:|---|---|---|---|
| `java` | 5 | 0.000 (none) | 0.000 (none) | 0.000 | 0.000 (none) |
| `python` | 5 | 0.000 (none) | −0.200 (−1 ×1) | 0.000 | −0.200 (−1 ×1) |
| `javascript` | 5 | 0.000 (none) | −0.600 (−3 ×1) | 0.000 | −0.600 (−3 ×1) |
| `typescript` | 5 | 0.000 (none) | 0.000 (none) | 0.000 | −0.200 (−1 ×1) |
| `go` | 5 | 0.000 (none) | −0.200 (−1 ×1) | 0.000 | −0.200 (−1 ×1) |
| `csharp` | 5 | 0.000 (none) | −0.400 (−2 ×1) | 0.000 | −0.400 (−2 ×1) |
| `json` | 6 | +0.167 (+1 ×1) | 0.000 (none) | 0.000 | 0.000 (none) |
| `yaml` | 6 | 0.000 (none) | −0.500 (−3 ×1) | 0.000 | −0.500 (−3 ×1) |
| `properties` | 6 | 0.000 (none) | −0.333 (−2 ×1) | 0.000 | −0.167 (−1 ×1) |

Observed pattern: every language/file shows at most **one** pair with a
non-zero Completeness/Usefulness delta out of its 5 or 6 pairs — there is
no language where a majority, or even a large minority, of pairs
decreased. `java` and `typescript` (Completeness) show zero decreases at
all. The single non-zero pair per language, where one exists, traces
back to exactly one of the task-level cases already discussed in §4 (no
new per-language pattern emerges beyond what the task-level breakdown
already explains) — e.g. `javascript`'s one decrease is its
`generate_unit_tests` pair; `csharp`'s is its `suggest_refactoring` pair;
`yaml`'s is its `generate_unit_tests` pair. This is consistent with the
decreases being driven by specific task/response circumstances rather
than a general per-language effect.

## 6. Dimension 5 analysis (`misunderstood_value`, sanitized responses only)

N = 48 (all sanitized responses; original responses are N/A on this
dimension and excluded).

- Mean = 4.958, median = 5.
- Score distribution: **5 → 46 responses (95.83%)**, **4 → 2 responses (4.17%)**.
  No sanitized response scored 3, 2, or 1 on this dimension anywhere in
  the dataset.

The 2 non-perfect cases (both score 4, both `java`):

| Language | Task | Response file | Failure-mode tag | What the evaluation records |
|---|---|---|---|---|
| java | `explain_code` | `ai-evaluation/experiment/results/java/explain_code/sanitized.txt` | `inferred_placeholder_value` | The response hypothesizes placeholders are "template slots meant to be substituted... **before** the file is fed to whatever tool is being benchmarked" — backwards on substitution direction (real values were replaced *out*, not placeholders substituted *in*). Explicitly hedged as a question to the author; does not affect the response's main conclusions. |
| java | `generate_unit_tests` | `ai-evaluation/experiment/results/java/generate_unit_tests/sanitized.txt` | `placeholder_as_real_value` | An `assertEquals` uses the placeholder text as the expected test value with no acknowledgment elsewhere in the response that it is a substituted/sanitized value. The evaluation notes this is a "borderline/mild instance" — the resulting test is factually correct and would actually pass against the sanitized file, so it is not a functional error. |

**Concrete-case inspection for the specific failure categories requested**
(not inferred from the numeric score alone — each was checked against
the qualitative evidence text in the corresponding `human_evaluation.md`):

- **Placeholder treated as a real/working value:** 1 case (java
  `generate_unit_tests`/sanitized, above) — explicitly qualified by the
  evaluator as mild/borderline, since the assertion is still factually
  correct against the actual sanitized file content.
- **Placeholder misunderstood more broadly (inferred what it "really"
  stood for):** 1 case (java `explain_code`/sanitized, above).
- **Placeholder flagged as itself a security issue:** 0 cases found in
  any of the 96 responses.
- **False merge (two different real values treated as the same):** 0
  cases found.
- **False split (the same real value treated as two different ones):** 0
  cases found.
- **Reconstructed secret (response claims/reveals the actual redacted
  value):** 0 cases found; the closest related category is "inferred
  what a placeholder probably stood for," which occurred once (above)
  and did not involve stating or reconstructing an actual value.
- **Unrunnable placeholder reuse (placeholder text reused in generated
  code in a way that wouldn't run/compile):** 0 cases found. Multiple
  responses were specifically checked for this and confirmed not to
  exhibit it (e.g., placeholder text quoted in "before" code blocks
  as an accurate representation of existing source, never as literal
  values relied upon to function).

## 7. Dimension 6 analysis (6 applicable responses only)

Applicable only to `explain_config_relationships` on `json`, `yaml`, and
`properties`, both conditions. **The 90 N/A responses are excluded from
this section's denominator entirely**, consistent with the task
instructions.

| Language/file | Condition | Score | Failure modes |
|---|---|---:|---|
| json | original | 5 | none |
| json | sanitized | 5 | none |
| yaml | original | 5 | none |
| yaml | sanitized | 5 | none |
| properties | original | 5 | none |
| properties | sanitized | 5 | none |

All 6 applicable responses scored 5/5. No relationship-preservation
failure occurred in any of the 6 — no false merge (two different values
wrongly treated as the same entity) and no false split (one value wrongly
treated as two) is recorded in any of the corresponding evaluation
sections. **N=6 is a very small sample** — this dimension was exercised
by only one task on 3 of the 9 candidate files, so this result describes
those 6 specific responses and should not be generalized to Dimension 6
performance under different files, tasks, or value-relationship
structures without further data.

## 8. Failure-mode analysis

Every value observed in the `failure_modes` column, parsed and counted
(a response can carry more than one tag; none did in this dataset).
Categories the task brief asks to distinguish, reported even where the
count is 0:

### Sanitization-related

| Failure mode | Count | Response IDs |
|---|---:|---|
| Placeholder treated as a real/working value | 1 | java `generate_unit_tests`/sanitized |
| Placeholder flagged as itself a security issue | 0 | — |
| Unrunnable placeholder reuse | 0 | — |
| False merge | 0 | — |
| False split | 0 | — |
| Reconstructed secret | 0 | — |
| *(Closest recorded relative: "inferred what a placeholder probably stood for")* | 1 | java `explain_code`/sanitized |

### Sanitization-independent

| Failure mode | Count | Response IDs |
|---|---:|---|
| Missed a real, sanitization-independent issue (found in original, absent from paired sanitized response) | 14 | java `security_analysis`/sanitized; python `identify_bug`/sanitized; python `security_analysis`/sanitized; javascript `identify_bug`/sanitized; javascript `security_analysis`/sanitized; typescript `identify_bug`/sanitized; typescript `suggest_refactoring`/sanitized; go `security_analysis`/sanitized; go `suggest_refactoring`/sanitized; csharp `identify_bug`/sanitized; csharp `suggest_refactoring`/sanitized; json `identify_bug`/sanitized; json `security_analysis`/sanitized; properties `identify_bug`/sanitized |

This is, by count, the single most common tagged pattern in the dataset
(14 of 96 responses, all in the sanitized condition, 29.2% of all 48
sanitized responses). Per the rubric's own design, this checklist item is
explicitly comparative and was applied **only** where the corresponding
`human_evaluation.md` confirmed the omitted observation was genuinely
derivable from the sanitized file's structure/names alone — not merely
"missing relative to the paired response." In most of these 14 cases the
evaluation explicitly notes the sanitized response's own Completeness/
Usefulness scores were **not** lowered, because the paired sanitized
response was independently judged thorough on its own terms and/or the
omission was offset by a different, novel observation the sanitized
response made that the original did not. Only 2 of these 14 cases
(python and json `security_analysis`/sanitized) contributed to an
actual Completeness/Usefulness score reduction (see §4); the remaining
12 were recorded as qualitative pattern-tracking only, per the rubric's
own instruction that this checklist item exists "for pattern-spotting...
not for scoring."

### Environmental/protocol

| Failure mode | Count | Response IDs |
|---|---:|---|
| Environment/project-path leakage | 6 | python `explain_code`/original; typescript `security_analysis`/original; go `explain_code`/original; yaml `explain_code`/original; properties `generate_unit_tests`/original; properties `generate_unit_tests`/sanitized |
| Other protocol deviations (not project-path leakage) | 0 | — |

All 6 are variants of the same underlying pattern — see §9 for full
discussion; none was excluded from this table, and none was silently
dropped from either the dataset or this analysis.

## 9. Environmental-deviation analysis

The 6 documented deviations, isolated exactly as specified:

| # | Language | Task | Condition | Confidence (as documented) |
|---|---|---|---|---|
| 1 | python | `explain_code` | original | High (exact, distinctive project-directory-name string) |
| 2 | typescript | `security_analysis` | original | Low/uncertain (a generic word that also matches the session's working-directory path component) |
| 3 | go | `explain_code` | original | High |
| 4 | yaml | `explain_code` | original | High |
| 5 | properties | `generate_unit_tests` | original | High |
| 6 | properties | `generate_unit_tests` | sanitized | High — most severe instance (project name **and** full absolute filesystem path) |

**These are explicitly not treated as evidence of sanitizer leakage.**
In every one of the 6 cases, the leaked information is the *Claude Code
session's own working-directory name or path* — never a scrubbed secret
value from a candidate file, and never derived from the sanitized
file's content. All 6 sessions reported `tool_uses: 0`, meaning the
information could not have come from exploring the repository; the
`batch_record.md` for each affected batch attributes this to ambient
subagent-runtime session metadata exposure, a property of the evaluation
tooling itself, unrelated to whether or how a file was sanitized.

**Scoring impact:** all 6 affected responses had their deviation content
explicitly excluded from credit on every dimension during human
evaluation (documented in each response's evidence text and reflected in
the `deviation` column of `evaluation_dataset.csv`). Their numeric scores
in this dataset (all 5/5/5/5 on the four always-scored dimensions)
reflect only their legitimate task content, not the deviation.

**Could this influence interpretation of the experiment?** Two
considerations, stated without resolving them:

- Because the deviations were excluded from scoring credit at the
  evaluation stage, they do not directly bias any number reported in
  §2–§6 above.
- However, 5 of the 6 instances occurred in the **original** condition
  and 1 in the **sanitized** condition (`properties`/`generate_unit_tests`,
  which also shows the experiment's only instance of *two* deviation
  sentences in one response). This asymmetry is worth noting rather than
  dismissing: it is consistent with the ambient-metadata-leakage
  explanation being independent of condition (5 original + 1 sanitized
  out of 48 each is not an extreme imbalance for a low-frequency,
  apparently-random event), but the sample is small enough (6 events)
  that this asymmetry cannot itself be interpreted as showing anything
  about original vs. sanitized conditions specifically — it is presented
  as an observation, not a finding.

## 10. Normal-variability / control analysis

**Byte-identical original vs. sanitized input:** only the `properties`
(`edge_cases/false_positives.properties`) file has this property — it is
the experiment's negative control, with zero ground-truth detections, so
its frozen sanitized fixture is byte-identical to the original. All 6
`properties` task pairs therefore received **literally identical prompt
content** in both conditions.

| Task | Δ Correctness | Δ Completeness | Δ Consistency | Δ Usefulness |
|---|---:|---:|---:|---:|
| `explain_code` | 0 | 0 | 0 | 0 |
| `identify_bug` | 0 | 0 | 0 | 0 |
| `security_analysis` | 0 | 0 | 0 | 0 |
| `generate_unit_tests` | 0 | 0 | 0 | 0 |
| `suggest_refactoring` | 0 | **−2** | 0 | **−1** |
| `explain_config_relationships` | 0 | 0 | 0 | 0 |

5 of the 6 `properties` pairs show zero difference on every dimension,
as expected when the input text is identical. **One pair —
`suggest_refactoring` — shows a Completeness/Usefulness decrease (−2/−1)
despite the two conditions having received the exact same file content.**
This is direct, unambiguous evidence that a paired-response quality
difference can occur **without any sanitization having taken place at
all** — i.e., it demonstrates that ordinary session-to-session AI
response variability alone is sufficient to produce a delta of this
magnitude and direction. This is an important control: it means the
similarly-shaped decreases seen elsewhere in `suggest_refactoring` for
`go`, `csharp`, `typescript` (§4) **cannot be attributed to sanitization
with confidence from this data alone** — the same pattern, same task,
same direction, occurred once with zero possible sanitization effect.

No other systematic byte-identical comparison exists elsewhere in the
dataset (every other file's sanitized fixture differs from its original
by construction, since the engine detected and replaced at least one
value in every other candidate file). This limits how far the
normal-variability control can be generalized — it is directly
demonstrated for one task on one file, and offered as a caution against
over-attributing the `suggest_refactoring` pattern specifically, not as
proof that no part of any observed decrease is sanitization-related.

## 11. Preliminary observations

Stated descriptively, without causal claims beyond what is directly
supported:

1. **Correctness and Consistency show essentially no observed
   difference between conditions** across all 48 pairs (Consistency:
   zero change in every single pair; Correctness: one pair changed, and
   that change traces to an original-condition reproduction slip, not a
   sanitized-condition improvement in general reasoning).
2. **Completeness and Usefulness show a modest, non-uniform decrease in
   the sanitized condition**, concentrated in a minority of pairs
   (6/48 and 7/48 respectively, both ≤14.6%) rather than spread evenly
   across the dataset — most pairs (85%+) show no change on either
   dimension.
3. **The decreases cluster in two tasks** — `generate_unit_tests` (2
   pairs, both −3, the largest observed drops) and `suggest_refactoring`
   (3–4 pairs, −1 to −2) — with `security_analysis` contributing one
   further −1/−1 pair. `explain_code`, `identify_bug`, and
   `explain_config_relationships` show zero decreases anywhere.
4. **At least one of these decreases is demonstrably not caused by
   sanitization**: the `properties`/`suggest_refactoring` pair shows an
   equivalent decrease with byte-identical input in both conditions
   (§10), which is direct evidence that ordinary response variability
   alone can produce this signature. This does not rule out a genuine
   sanitization effect in the *other* `suggest_refactoring` cases — it
   only means the data does not, by itself, distinguish "caused by
   sanitization" from "ordinary variability that happened to land in the
   sanitized-condition session" for those cases.
5. **The `generate_unit_tests` decreases have a more specific,
   qualitatively-documented mechanism**: in both affected pairs
   (`javascript`, `yaml`), the sanitized-condition response is recorded
   as declining to produce any test code at all, reasoning (in each
   evaluator's judgment) from the visible presence of placeholder syntax
   toward a broader "this whole file is an external fixture, not worth
   testing" conclusion — a plausible sanitization-related effect,
   distinct in character from the `suggest_refactoring` pattern.
6. **Dimension 5 (placeholder handling) shows the dataset's strongest,
   most consistent result**: 46 of 48 sanitized responses (95.8%) show
   no sign of misunderstanding a placeholder at all; the 2 exceptions
   are both mild/hedged and both isolated to `java`; zero instances of
   false merge, false split, reconstructed secrets, placeholder-as-
   security-issue, or unrunnable placeholder reuse were found anywhere
   in 96 responses.
7. **Environmental deviations (6 responses) are a tooling artifact, not
   a sanitization signal**: they leak the evaluation session's own
   directory/path, never a candidate file's scrubbed value, and were
   excluded from scoring credit before any number in this report was
   computed.
8. **One genuinely surprising pattern deserving further investigation**:
   the single Correctness increase in the whole dataset
   (`json`/`suggest_refactoring`) occurred because the *original*
   condition — not the sanitized one — made a factual error (reproducing
   a secret value's prefix incorrectly in an illustrative example). This
   is a reminder that "sanitized" does not only remove information — it
   also removes the *opportunity* for a response to misstate the
   removed information, which is a distinct mechanism from either
   condition being generally more or less capable.

**These are observations from a descriptive pass over one experiment's
96 responses, not statistically validated findings.** Whether any of the
patterns above hold up under formal hypothesis testing, whether the
observed effect sizes are distinguishable from chance given the small
per-cell sample sizes (as few as N=3 pairs for some task/language
breakdowns), and whether the `generate_unit_tests` and
`suggest_refactoring` patterns reflect a real, reproducible sanitization
cost or a small-sample artifact are all open questions for the next
analysis phase.

## 12. Limitations

- **Small N throughout most breakdowns.** The overall N=48 pairs is
  workable for the top-line dimensions, but every task-level breakdown
  has N=9 or N=3 pairs, and every language-level breakdown has N=5 or
  N=6 pairs — small enough that single-pair events (like the one
  `json`/`suggest_refactoring` Correctness increase) visibly move the
  reported means and should not be over-interpreted as stable patterns.
- **Single-rater scoring.** All 96 scores come from one human evaluator
  applying one rubric once per response; there is no inter-rater
  reliability measure, and no response was scored twice.
- **Consistency and (mostly) Correctness show a ceiling effect** — with
  scores clustered almost entirely at 5, these two dimensions currently
  carry very little discriminative signal in this dataset (already
  flagged in `scoring_integrity_audit.md`'s "Issues requiring manual
  review").
- **Dimension 6's N=6 is too small for any general claim** about
  relationship-preservation performance beyond the specific 3
  files/1 task actually tested.
- **The properties/`suggest_refactoring` control is a single data
  point.** It demonstrates that ordinary variability *can* produce a
  Completeness/Usefulness decrease of this shape, but one instance
  cannot establish *how much* of the other, non-byte-identical
  decreases are attributable to variability versus sanitization.
- **The comparative failure-mode checklist item ("missed a
  sanitization-independent issue") depends on evaluator judgment about
  what is "independently derivable"** — a defensible, documented judgment
  call each time, but not a mechanically-verifiable one, unlike the
  numeric dimension scores.
- **Dimension 6's applicability rule changed once already** (the
  post-audit Java normalization) — this dataset reflects the current,
  normalized state throughout, but this history is a reminder that
  methodology decisions in this experiment have evolved and should be
  checked against the frozen rubric and manifest before any further
  reuse of these numbers.
- **This is a descriptive pass only.** No claim in this document should
  be read as a statistically validated finding; §11's "preliminary
  observations" are exactly that — candidates for the next, more
  rigorous analysis phase, not conclusions.
