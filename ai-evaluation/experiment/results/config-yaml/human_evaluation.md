# Human evaluation — Batch 8 (`config/settings.yaml`)

Scored against `ai-evaluation/rubric/rubric.md`'s six dimensions only.
Each response scored independently on the six numeric dimensions; the
failure-mode checklist's comparative item is applied comparatively, per
the rubric's own design (consistent with prior batches). No LLM judge
used. No aggregate/composite score computed.

Dimension key: **1** Correctness, **2** Completeness, **3** Consistency,
**4** Usefulness, **5** Misunderstood a sanitized value? (N/A for
original), **6** Relationships between values preserved? (N/A unless the
task itself calls for same/different-value identity judgments — scored
for `explain_config_relationships`, as in the JSON batch).

**Batch/candidate:** `benchmark/dataset/files/config/settings.yaml`,
all 6 tasks applicable per `manifest.json` (no discrepancy this time
between batch instructions and manifest, per `batch_record.md`).
**Responses evaluated: 12/12.**

**File note:** `service.session_key`'s real value in the original file is
the literal word `dummy` — not a secret-shaped string at all — yet it is
sanitized to `<GENERIC_SECRET_1>`, a placeholder indistinguishable in
appearance from a genuine secret category. This creates a real,
structural information-loss case discussed under several tasks below:
the original condition can see (and reason about) how trivial the actual
value is; the sanitized condition cannot.

**Protocol deviation — flagged, high confidence:** `explain_code/original.txt`
contains *"...matching the working directory name
'New-credential-scrubber'..."* — an exact match to the repository's
actual project directory name, the same high-confidence pattern
documented in Batches 2 and 5. Preserved unedited; scored below with
**no credit given for the project-name knowledge**. Several other
responses' generic, content-grounded observations about the visible
`<...>` placeholder syntax (e.g., `explain_code/sanitized`,
`security_analysis` responses) are, per `batch_record.md`, correctly
not treated as deviations.

---

## Task: explain_code

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Accurate three-part breakdown of the `service`
block, correctly distinguishing the realistic-looking `encryption_key`
from the bare-word `session_key: dummy`. Good author questions,
including why the two secret fields differ so much in realism and
whether the `fake-` prefix could interfere with pattern-matching. Scored
on this legitimate content; the flagged deviation sentence is excluded
from credit.

**Failure-mode checklist:** ticking **Other** — environmental deviation
(project-directory-name leak), documented above, not scored or credited.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Same structure, fully accurate; correctly treats
`<URL_1>`/`<PRIVATE_KEY_1>`/`<GENERIC_SECRET_1>` as "clearly stand-ins
(redacted or template tokens)." Asks a sharp, well-grounded question
about whether `encryption_key`/`session_key` being assigned distinct
categories (`PRIVATE_KEY` vs. `GENERIC_SECRET`) is deliberate test
coverage — correct, appropriately-hedged reasoning about the
categorization itself.

**Failure-mode checklist:** none apply.

---

## Task: identify_bug

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Correctly finds no functional bug. Quality
notes: plaintext secrets pattern; and a sharp, value-grounded
observation that `session_key: dummy` "reads like a placeholder that
was never filled in — worth confirming it's intentional rather than a
forgotten TODO," directly enabled by seeing the actual literal value. No
deviation.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Correctly finds no functional bug. Quality
notes: plaintext secrets pattern, appropriately caveated as only a
concern "if this pattern were copied into a real file"; and an
independently sharp new observation — `port: 8080` with
`environment: production` is unusual for an internet-facing service
typically fronted by a privileged port. Does not (and structurally
cannot) reproduce the original's "looks like a forgotten TODO"
observation about `session_key`, since that depended on seeing the
literal value `dummy`, which sanitization replaced — **not** treated as
a missed sanitization-independent issue, since it genuinely is
value-dependent (see file note above), not a gap the response could have
closed.

**Failure-mode checklist:** none apply.

---

## Task: security_analysis

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Four findings (High/Medium/Low/Low). Notably
nuanced: Finding 2 (`session_key`) is scored Medium rather than High,
explicitly because "the placeholder value itself isn't sensitive"
(`dummy`) even though the *pattern* (a dedicated secret field
hardcoded) still warrants flagging — a calibrated judgment only possible
because the actual value is visible. Also flags the internal endpoint
disclosure and the lack of an explicit "this file is templated"
convention. No deviation.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Four findings (High/High/Medium/Low), covering
the same substantive ground as the original plus a constructive
CI-secret-scanner-policy suggestion. `session_key` is scored High rather
than the original's Medium — a defensible independent severity call,
not an error, but see the file note: this response has no way to know
the underlying value was the trivial word `dummy`, so it reasonably
treats `<GENERIC_SECRET_1>` at face value as a genuine secret-shaped
field, the same as `<PRIVATE_KEY_1>`. Ends with an explicit, exemplary
caveat: "All values in this file are placeholders...I'm not treating
them as real leaked credentials, but the *pattern*...is a legitimate
security anti-pattern." Correctness/Completeness/Usefulness scored 5 —
the severity difference reflects genuine information asymmetry between
conditions, not a response defect.

**Failure-mode checklist:** none apply. (The session-key severity
difference is discussed in Batch-level observations rather than ticked
as a "missed issue," since it is not sanitization-independent.)

---

## Task: generate_unit_tests

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Carefully distinguishes "logic" tests (not
applicable — the file has none) from legitimate **structural/schema**
tests, and delivers five well-justified pytest tests (valid-YAML/mapping
check, required-keys-present, field-type check, port-range check,
endpoint-is-a-well-formed-URL), explicitly flagging that these test
invariants the author chose to assert, not hidden business logic — an
honest, useful, and unusually thorough response for this task type. No
deviation.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 2 | 5 | 2 | 5 | N/A |

**Evidence/rationale:** Correctly reasons that asserting hardcoded
key-value pairs "would only amount to...re-stating the YAML content in
code form," but — unlike the original — does not consider or deliver
any structural/schema-validation tests (required keys present, correct
field types, port range, URL well-formedness), even though every one of
those tests is exactly as derivable and valuable against the sanitized
file as against the original (none depend on the actual secret values,
only on structure/type). The original condition's own delivered work on
this identical structural pattern demonstrates this was a real, missed
opportunity, not an unavailable one. Completeness and Usefulness are
each scored 2: the response correctly identifies why naive
literal-equality tests are meaningless but does not follow through to
the legitimate schema-validation category it could have (and, in the
other condition, did) reach.

**Failure-mode checklist:** none of the seven specific items apply
precisely (this is not a placeholder misunderstanding); recorded instead
via the Completeness/Usefulness reduction and this note, consistent with
how the JavaScript batch's equivalent `generate_unit_tests` gap was
handled.

---

## Task: suggest_refactoring

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Proposes externalizing `encryption_key` and
`session_key` to environment-variable references; the "after" YAML fully
implements the fix, leaving `endpoint` as a literal (a defensible scope
choice — `endpoint` is topology information, not a credential). No
deviation.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Proposes a broader scope — externalizing
`endpoint` as well as both secrets, consistent with this response's own
`security_analysis` sibling flagging the endpoint as a minor exposure
risk too. The "after" YAML fully implements all three env-var
references. A defensible, internally-consistent broader interpretation,
not an error; fully delivered in code.

**Failure-mode checklist:** none apply.

---

## Task: explain_config_relationships

*Dimension 6 is applicable to this task.*

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | 5 |

**Evidence/rationale:** Groups `name`/`environment`/`port`/`endpoint`/
`region` as one "service identity/networking" unit (reasoning that port
and endpoint are directly linked) and `encryption_key`/`session_key` as
a "credential/secret material" category — explicitly noting they are
"independent of *each other* functionally" despite being grouped by
type, so no false merge. Uniquely (enabled by seeing the actual literal
values), notes "`session_key` is a placeholder (`dummy`) while
`encryption_key` is a fake but realistic-looking key string —
structurally analogous fields despite the different-looking values" — an
accurate, evidence-grounded distinction unavailable to the sanitized
condition. No deviation.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | 5 |

**Evidence/rationale:** A more granular taxonomy than the original
(splitting "identity" from "network binding" rather than merging them) —
a defensible alternative grouping, not an error. Correctly groups
`encryption_key`/`session_key` as a functional "credentials" cluster
while explicitly noting they "likely serve different purposes (data
encryption vs. session signing)" — the same correct non-merging the
original achieves, reached here from field names/types alone rather than
from the literal values. No false merge or split anywhere.

**Failure-mode checklist:** none apply.

---

## Batch-level observations

(Qualitative only — no winner is declared, no scores are aggregated.)

- One flagged, high-confidence environmental deviation this batch
  (`explain_code/original`), isolated to 1 of 12 responses, preserved
  unedited, excluded from scoring credit.
- **This batch's standout qualitative finding:** `session_key`'s real
  value (`dummy`) is not secret-shaped at all, yet the engine sanitizes
  it to `<GENERIC_SECRET_1>` — a placeholder visually indistinguishable
  from a genuine secret. In the original condition, both `identify_bug`
  and `security_analysis` responses noticed the value's triviality and
  produced more calibrated judgments (a "looks like a forgotten TODO"
  observation; a Medium- rather than High-severity finding explicitly
  reasoned from the value's non-sensitive appearance). The sanitized
  condition's responses could not access this nuance and reasonably
  treated the placeholder at face value as a genuine secret. This is not
  a response-quality defect in either condition — it is a direct,
  observable instance of the sanitization approach trading away a
  legitimate signal (how convincingly secret-shaped a value actually is)
  for safety, directly relevant to this experiment's core research
  question.
- `generate_unit_tests` is this batch's one substantive quality gap: the
  original condition correctly recognized and delivered legitimate
  schema/structural-validation tests; the sanitized condition declined
  testing altogether without considering that (sanitization-independent)
  angle, despite it being equally available.
- `explain_config_relationships` was handled well by both conditions —
  different but equally defensible groupings, no false merges or splits
  in either — with the original condition able to draw on one additional,
  literal-value-dependent piece of evidence unavailable to the sanitized
  condition.
- No instance in this batch of a placeholder treated as a real/working
  value, flagged as itself a security issue, reused in code that
  wouldn't run, or of a false merge/split.

## Methodology notes

- **Relationships-preserved (dimension 6) was scored for
  `explain_config_relationships`**, consistent with the JSON batch; N/A
  elsewhere.
- **The `session_key`/`dummy` information-loss pattern was deliberately
  *not* ticked under the "missed a sanitization-independent issue"
  failure-mode item anywhere in this batch**, following the refinement
  established in the TypeScript evaluation: that checklist item is
  reserved for issues genuinely independent of the specific (redacted)
  value, and this one is not — it depends entirely on seeing that the
  real value was the trivial word `dummy`. It is instead surfaced
  explicitly in the batch-level observations, since it is a legitimate
  and important qualitative finding in its own right.
- **`generate_unit_tests/sanitized`'s Completeness/Usefulness reduction**
  was based on a directly observable gap versus what the identical
  structural pattern permits (proven achievable by the original
  condition's own delivered tests), not on forcing parity between
  conditions.
