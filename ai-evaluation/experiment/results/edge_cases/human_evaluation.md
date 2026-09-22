# Human evaluation — Batch 9 (`edge_cases/false_positives.properties`)

Scored against `ai-evaluation/rubric/rubric.md`'s six dimensions only.
Each response scored independently on the six numeric dimensions; the
failure-mode checklist's comparative item is applied comparatively, per
the rubric's own design (consistent with prior batches). No LLM judge
used. No aggregate/composite score computed.

Dimension key: **1** Correctness, **2** Completeness, **3** Consistency,
**4** Usefulness, **5** Misunderstood a sanitized value?, **6**
Relationships between values preserved?

**Batch/candidate:** `benchmark/dataset/files/edge_cases/false_positives.properties`,
all 6 tasks applicable per `manifest.json` (negative control: zero
ground-truth true positives). **Responses evaluated: 12/12.**

**Negative-control file note:** every line in this file's real value is
non-sensitive; the engine detects nothing, so the frozen sanitized
fixture is **byte-identical** to the original. There are no placeholders
anywhere in this batch's sanitized-condition responses to potentially
misunderstand. Per the rubric's own dimension-5 definition — "No sign of
misunderstanding...**or not remarked on at all where that's
appropriate**" falls under the **5 (best)** band, not N/A — dimension 5
is scored **5**, not N/A, throughout this batch's sanitized-condition
responses, since correctly not treating anything as a placeholder is
itself the correct behavior here.

**Protocol deviations — flagged, both in `generate_unit_tests`, per
`batch_record.md`:**
- `generate_unit_tests/original.txt`: *"...its context (directory
  `New-credential-scrubber`) strongly suggest this is a fixture..."* —
  exact project-directory-name match.
- `generate_unit_tests/sanitized.txt`: **two** instances — *"...evidently
  a credential/secret scrubber, given the 'New-credential-scrubber'
  project context..."* and, more severely, *"...point me at the
  scrubber/scanner source (or the directory it lives in under
  `D:\New-credential-scrubber`)"* — a **full absolute filesystem path**,
  the single most severe leak documented across this entire 96-response
  experiment.

Both responses were preserved unedited per instruction. **No credit is
given anywhere in this evaluation for the project-name or path
knowledge** in either response — their legitimate task content is scored
independently below, with the deviation content excluded from
consideration.

---

## Task: explain_code

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Accurate three-part breakdown. Correctly and
honestly identifies the "trap" entries (`username`, `database`) and
"word-collision" entries, explicitly hedging where a claimed collision
isn't obvious ("`ghost_writer` isn't an obvious collision...") rather
than fabricating a false pattern match — good epistemic honesty. Sharp
author question noting the header comment claims a "key"-containing
example exists but none is actually present in the file. No deviation.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Same accurate structure; independently notices
the same comment/content mismatch (claimed "key" collision, none
present) and flags it as possibly "a leftover/inaccurate comment from a
template." No deviation; no placeholders to misunderstand.

**Failure-mode checklist:** none apply.

---

## Task: identify_bug

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Correctly finds no functional bug. Quality
notes: `timeout` has no unit indicated; inconsistent (harmless) quoting;
`username = "admin"` fine as a stated placeholder but would warrant a
clarifying comment in a real config. No deviation.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Correctly finds no functional bug, explicitly
verifying all ten entries. Quality notes: the same quoting inconsistency;
a new observation that the file mixes unrelated concerns with no
sectioning. Because the sanitized file is **byte-identical** to the
original here, any content difference between the two responses is, by
construction, trivially sanitization-independent.

**Failure-mode checklist:** ticking **"Missed a real,
sanitization-independent issue in the sanitized condition that was
correctly found in the original condition"** — the original's minor
`timeout`-unit-ambiguity note is absent; given the byte-identical file,
this is unambiguously not an information-loss case, just a response-level
omission. Not reflected in the numeric scores (minor, and offset by the
sanitized response's own new sectioning observation).

---

## Task: security_analysis

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Correctly reports **no findings**, with explicit
reasoning through every "trap" entry (`username`, `ghost_writer`,
`authored_by`, `tokenizer_version`, `concert_hall`, `database`)
confirming none is an actual credential — exactly the correct behavior
for a negative-control file. No deviation.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Same correct "no findings" conclusion, with
essentially equivalent reasoning through each trap entry (expected,
since the input is byte-identical). Explicitly states flagging any of
these lines "would be a false positive" — precise, correct framing.

**Failure-mode checklist:** none apply. Both conditions reached the
ideal response for this negative-control task.

---

## Task: generate_unit_tests

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Correctly determines the static `.properties`
file has no testable logic and explains the tautology problem with
literal-equality tests. Offers to write real tests against the scrubber
itself if pointed to its source. Scored on this legitimate content; the
flagged deviation sentence is excluded from credit entirely.

**Failure-mode checklist:** ticking **Other** — environmental deviation
(project-directory-name leak), documented above, not scored or credited.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Same correct conclusion, with a concrete,
well-constructed illustrative JUnit 5 test skeleton showing what
*should* be tested (the scrubber's `scan()` returning zero findings for
this fixture) — genuinely more concrete than the original's equivalent
offer. Scored on this legitimate content only; **both** flagged deviation
sentences (the project name and, more severely, the full absolute path)
are completely excluded from credit on every dimension, per instruction,
despite the response otherwise being strong.

**Failure-mode checklist:** ticking **Other** — severe environmental
deviation (project name **and** full absolute filesystem path),
documented above, not scored or credited under any circumstance.

---

## Task: suggest_refactoring

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Proposes namespacing keys (`server.*`, `app.*`,
`metadata.*`). The delivered "after" block fully regroups **all ten**
keys from the file, including the four benchmark-only fields
(`ghost_writer`, `concert_hall`, `authored_by`, `tokenizer_version`).
Complete, accurate, well-justified. No deviation.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 3 | 5 | 4 | 5 | N/A |

**Evidence/rationale:** Proposes the same namespacing approach
(`server.*`, `db.*`, `app.*`) and explicitly discusses, in prose, that
"the benchmark-only fields (`ghost_writer`, `concert_hall`, `authored_by`,
`tokenizer_version`)" also sit at the flat top level needing grouping —
but the delivered "before"/"after" code blocks show and regroup only
**6 of the file's 10 keys**, omitting all four benchmark-only fields
from the actual delivered refactor. Because the sanitized file is
**byte-identical** to the original here, this gap cannot be attributed to
any sanitization-driven information loss — the full 10-key content was
equally available to both conditions, and the original condition's own
response demonstrates a complete regrouping was straightforward.
Completeness is scored 3 (the task's core is addressed but a discussed,
clearly-intended part of the deliverable is not actually delivered);
Usefulness scored 4 (the approach is sound and directly extensible, but
a developer must finish the omitted 4 keys themselves).

**Failure-mode checklist:** none of the seven items apply precisely
(not a placeholder-handling issue); recorded via the Completeness/
Usefulness reduction and this note. Not ticked as "missed a
sanitization-independent issue" since that item is about a missed
finding/observation, not an incomplete code deliverable — but the
underlying point is the same in spirit: on identical input, one
condition's response was less complete than the other's.

---

## Task: explain_config_relationships

*Dimension 6 is applicable.* For a negative-control file, the correct
behavior is to identify only the relationships genuinely supported by
the file (the loose `timeout`/`port` and `username`/`database` pairings)
and to **not** invent false relationships among the trigger-word-bearing
decoy fields, which is exactly what a true negative control tests for at
the relationship-reasoning level.

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | 5 |

**Evidence/rationale:** Groups `timeout`/`port` (server connection),
`environment`/`country` (deployment context), and `username`/`database`
(database connection) — explicitly noting "`username = 'admin'` is a
generic/placeholder value, not a real secret, but structurally it groups
with `database`," correctly separating sensitivity from structural
relationship. Correctly leaves `ghost_writer`, `concert_hall`,
`authored_by`, `tokenizer_version` as independent singletons, explicitly
explaining why each superficial trigger-word resemblance doesn't
establish a real connection. No false merge or split anywhere. No
deviation.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | 5 |

**Evidence/rationale:** A slightly different but equally defensible
taxonomy (groups `environment` with `timeout`/`port` as "service
runtime" rather than with `country`) — not an error. Same correct
`username`/`database` pairing with the same appropriate non-sensitivity
caveat. Same correct treatment of the four decoy fields as independent,
with an explicit closing summary. No false merge or split.

**Failure-mode checklist:** none apply.

---

## Batch-level observations

(Qualitative only — no winner is declared, no scores are aggregated.)

- This batch's sanitized fixture is **byte-identical** to the original
  (zero ground-truth detections), so dimension 5 was scored 5 (not N/A)
  throughout per the rubric's own wording, and any response differences
  in this batch cannot be attributed to information loss from
  sanitization — a useful methodological contrast to Batches 5, 6, 8,
  and 9's other tasks, where such attribution required care.
- Two severe, high-confidence environmental deviations occurred in this
  batch, both in `generate_unit_tests` — including the single most
  severe leak of the entire experiment (a full absolute filesystem path
  in the sanitized condition). Both were preserved unedited and fully
  excluded from scoring credit; the surrounding legitimate content in
  both responses was otherwise strong.
- `security_analysis` and `explain_config_relationships` are this
  batch's cleanest results: both conditions reached essentially the
  ideal response for a negative control — zero false-positive findings,
  explicit reasoning through every trap entry, and no invented
  relationships among the trigger-word-bearing decoy fields in either
  condition.
- `suggest_refactoring/sanitized` delivered an incomplete regrouping (6
  of 10 keys) despite discussing all 10 in its own prose — notable
  specifically because the byte-identical input rules out any
  sanitization-driven explanation; it stands as a plain example of
  per-response quality variance independent of the sanitization
  treatment itself.
- No instance in this batch of a placeholder treated as a real/working
  value (there were none to treat), flagged as itself a security issue,
  reused in code that wouldn't run, or of a false merge/split.

## Methodology notes

- **Dimension 5 (Misunderstood a sanitized value?) was scored 5, not
  N/A, for every sanitized-condition response in this batch**, per the
  rubric's explicit "or not remarked on at all where that's appropriate"
  clause under the 5 (best) band — this file has no placeholders, and
  correctly not treating anything as one is the correct outcome, not an
  inapplicable dimension.
- **Both `generate_unit_tests` deviations were excluded from credit on
  every dimension**, including the otherwise-strong illustrative test
  code in the sanitized response, consistent with the standing rule that
  environmental-deviation content never receives scoring credit
  regardless of how well-constructed the surrounding response is.
- **The comparative failure-mode checklist item was applied consistent
  with prior batches** for `identify_bug/sanitized`; for
  `suggest_refactoring/sanitized`, the gap was scored directly via
  Completeness/Usefulness rather than forced into a checklist item, since
  none of the seven fixed items describe an incomplete code deliverable
  on identical input.
