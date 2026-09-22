# Human evaluation — Batch 4 (`typescript/auth.ts`)

Scored against `ai-evaluation/rubric/rubric.md`'s six dimensions only.
Each response scored independently of its paired condition on the six
numeric dimensions; the failure-mode checklist's comparative item is
applied comparatively, per the rubric's own design (consistent with the
precedent set in the Java, Python, and JavaScript evaluations). No LLM
judge used. No aggregate/composite score computed.

Dimension key: **1** Correctness, **2** Completeness, **3** Consistency,
**4** Usefulness, **5** Misunderstood a sanitized value? (N/A for
original), **6** Relationships between values preserved? (N/A unless the
task itself calls for same/different-value identity judgments).

**Batch/candidate:** `benchmark/dataset/files/typescript/auth.ts`,
5 applicable tasks × 2 conditions. **Responses evaluated: 10/10.**

**File note:** the sanitized fixture assigns `authToken` → `<ACCESS_TOKEN_1>`,
`secretKey` → `<GENERIC_SECRET_1>`, and `bearerHeader` → `<ACCESS_TOKEN_2>` —
`authToken` and `bearerHeader` share the `ACCESS_TOKEN` category (different
ordinals, i.e. correctly recognized as two *different* values of the same
type) despite holding differently-shaped original literals (a bare token
vs. a full `"Bearer <jwt-like-string>"` string). No response in this batch
conflated `authToken` and `bearerHeader` as the same value.

**Protocol deviation — flagged, uncertain confidence:** `security_analysis/original.txt`
contains the phrase *"if this file is part of a `website` project and ever
gets imported into client-side/browser-bundled code..."* This session's
actual Claude Code working directory is `D:\New-credential-scrubber\website`,
so "website" matches the real path's final component exactly, following the
same suspected ambient-environment-leakage pattern as Batch 2's confirmed
`New-credential-scrubber` deviation — but, per `batch_record.md`,
"website" is also a generic word a reviewer would plausibly reach for
independent of any environment awareness, so this is reported with
explicit uncertainty, not asserted as confirmed leakage. Per instruction,
the response was preserved unedited; its legitimate security content is
scored on its own merits below, and **no credit is given anywhere in this
evaluation for the word "website" itself** — the finding it appears in
is scored based on the security reasoning alone (hardcoded secrets risk
shipping to client bundles), which holds regardless of the specific noun
used and does not depend on knowledge of this repository.

---

## Task: explain_code

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** All three requested parts present and accurate:
summary; breakdown of the 3 benign constants vs. the 3 credential-shaped
fake values (correctly ties each to the `fake-` prefix / file comment);
relevant author questions about the `secretKey: string` type-annotation
inconsistency and the lack of any export. No deviation.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Same structure, fully accurate — placeholders
correctly described as "placeholder tokens...rather than actual
credentials." Notably asks *"why are there two 'access token' placeholders
(`authToken` and `bearerHeader`) but only one 'generic secret' placeholder
— is there significance to that distribution?"* — this correctly
recognizes `authToken` and `bearerHeader` as distinct entities sharing a
category, hedged as a question rather than asserted as fact; not a false
merge and not scored under dimension 6 (task doesn't call for a
relationship judgment), but noted here as evidence of correct handling.

**Failure-mode checklist:** none apply.

---

## Task: identify_bug

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Correctly finds no functional bug (file has no
control flow). Quality notes: `secretKey`'s inconsistent type annotation;
unused/unexported constants; and a genuinely sharp observation that
`bearerHeader` "holds only the token value (`'Bearer ...'`) but is named
as if it were a full header" — grounded in the file's actual content
(`bearerHeader = "Bearer fake.jwt.header-payload-signature123456"`). No
deviation.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Correctly finds no functional bug. Quality notes:
recommends `readonly`/branded types for the three credential-named
constants (a genuinely useful, independently-valid TS-specific
observation absent from the original response); the `secretKey`
annotation inconsistency (matches original); unused/unexported constants
(matches original); and a note that placing fake secrets in a plain
`.ts` file is worth avoiding "since secret scanners often flag it
regardless of intent" — correct, non-literal reasoning about the
placeholder's status. Independently thorough, so Completeness is scored
5 on its own merits.

**Failure-mode checklist:** ticking **"Missed a real,
sanitization-independent issue in the sanitized condition that was
correctly found in the original condition."** The `bearerHeader`
naming/purpose-mismatch observation from the original response is
absent here. This is confirmed genuinely *sanitization-independent* —
not merely value-dependent — because this same batch's
`security_analysis/sanitized` response (see below) independently makes
an equivalent observation reasoning from the variable **name** alone
(`bearerHeader`), which is untouched by placeholder substitution; the
insight was available to this response and simply not raised.

---

## Task: security_analysis

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** One consolidated High-severity finding covering
all three hardcoded credential-shaped values, with a thorough "why it
matters" (VCS history persistence, the flagged `website`/client-bundle
point, the `fake-` prefix providing no real protection, `Bearer`-header
logging risk) and a concrete fix (env vars/secrets manager, isolating
test fixtures into a clearly-named module). Scored on the strength of
this reasoning, not on the specific word "website" (see deviation note
above) — the client-side-bundle-exposure point is valid security
reasoning independent of that word choice.

**Failure-mode checklist:** ticking **Other** — environmental deviation
(possible/uncertain working-directory leak via the word "website"),
documented above; not scored or credited on any dimension.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Finding 1 (High) covers the three hardcoded
credential-shaped placeholders with equivalent thorough reasoning
(VCS persistence, copy-paste risk, matches credential-scanner target
patterns). Finding 2 (Low) independently identifies the same
`bearerHeader` naming/purpose mismatch the original `identify_bug`
response found — reasoning explicitly from the variable name
("The variable name suggests this stores a full `Authorization: Bearer
<token>` header value rather than just a token"), confirming this
insight does not depend on seeing the original literal value. Explicitly
and correctly addresses the placeholder's synthetic nature without being
misled by it: *"The file's own comment states these are synthetic/fake
values...That doesn't change the review outcome — a PR reviewer has no
way to verify a string literal is 'fake' from the code alone, and the
finding above is about the pattern."* This is exemplary placeholder
handling — reasoning about the pattern-level risk rather than the
specific (redacted) value.

**Failure-mode checklist:** none apply.

---

## Task: generate_unit_tests

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Correctly determines the file has **zero**
testable logic — unlike the JavaScript batch's `buildSecret()`, this
file contains no functions, classes, or exports of any kind, only bare
`const` declarations. Explains clearly why literal-equality tests would
be tautological, and offers to write real tests against the scrubber's
own logic if pointed to it. This is the fully correct, complete response
for a file with no logic to test. No deviation.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Same correct conclusion (no testable logic, same
tautology reasoning), reaching an identical, appropriate bottom line to
the original response. Unlike the JavaScript batch's
`generate_unit_tests` pair — where a real function existed and the two
conditions diverged on whether to test it — this file has no function in
either condition, so both correctly decline for the same, symmetric
reason. No misunderstanding of the placeholders.

**Failure-mode checklist:** none apply.

---

## Task: suggest_refactoring

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Proposes a `requireEnv()` helper and sources all
three hardcoded values from environment variables — directly addresses
this file's primary characteristic (hardcoded credential-shaped
literals) with a concrete, accurate before/after. No deviation.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 4 | 5 | N/A |

**Evidence/rationale:** Proposes grouping the three values into a typed
`AuthConfig` object and renaming `bearerHeader` → `bearerToken` since it
holds a token value, not a header — a correct, independently valid
naming fix (consistent with the naming insight `security_analysis/sanitized`
also found from the variable name alone). Fully addresses the requested
3-part structure (refactor / why / before-after), so Completeness is
scored 5. However, the proposed "after" code still assigns the
placeholder values as **literal, hardcoded strings** inside the new
object (`authToken: "<ACCESS_TOKEN_1>"`, etc.) — it does not source any
value from an environment variable or secrets manager, so the file's
primary, sanitization-independent risk (credentials hardcoded in source)
is unaddressed by this suggestion, even though this same response's
`security_analysis` sibling explicitly identified hardcoding as the
core issue. This is directly verifiable in the response's own "after"
code, independent of any comparison. Usefulness is scored 4
accordingly: the naming/grouping improvement is real and useful, but a
developer following this suggestion literally would still have all
three secrets hardcoded in source, an obvious and natural follow-up left
unaddressed.

**Failure-mode checklist:** ticking **"Missed a real,
sanitization-independent issue in the sanitized condition that was
correctly found in the original condition"** — externalizing the
hardcoded values to environment variables, which the original response's
refactor addressed directly and this response's refactor does not,
despite the issue being equally present (and independently
identifiable, as this file's own `security_analysis` sanitized response
shows) in the sanitized file.

---

## Batch-level observations

(Qualitative only — no winner is declared, no scores are aggregated.)

- One flagged environmental deviation this batch (`security_analysis/original`,
  the word "website"), reported with explicit uncertainty per
  `batch_record.md` and excluded from scoring credit either way.
- `generate_unit_tests` showed no original/sanitized divergence in this
  batch, unlike the JavaScript batch — `auth.ts` has no function in
  either condition, so both correctly and symmetrically decline to write
  tests for the same reason.
- A recurring thread across three tasks (`identify_bug`, `security_analysis`,
  `suggest_refactoring`) concerned the `bearerHeader` variable: its name
  alone (unaffected by sanitization) is enough to correctly infer it
  holds a bare token rather than a full header value — both
  `security_analysis/sanitized` and `suggest_refactoring/sanitized`
  independently made this observation from the name, while
  `identify_bug/sanitized` did not, confirming the miss there was a
  genuine, avoidable omission rather than an inherent sanitization
  limitation.
- `suggest_refactoring/sanitized` is this batch's one substantive
  quality gap: its proposed refactor improves organization/naming but
  leaves the file's primary hardcoded-credential problem unaddressed,
  something the original condition's refactor solved directly.
- No instance in this batch of a placeholder treated as a real/working
  value, flagged as itself a security issue, reused in code that
  wouldn't compile, or of a false merge/split — `authToken` and
  `bearerHeader` (sharing the `ACCESS_TOKEN` category) were consistently
  treated as distinct entities everywhere they were discussed.

## Methodology notes

- **Relationships-preserved (dimension 6) marked N/A throughout**,
  consistent with prior batches: none of the 5 applicable tasks calls
  for an explicit same/different-value judgment, even though
  `authToken`/`bearerHeader` sharing a category made this file a
  plausible candidate for a false merge — none occurred.
- **The comparative failure-mode checklist item was applied per
  established precedent**, with one refinement made explicit in this
  batch: before ticking "missed a sanitization-independent issue," this
  evaluation confirmed the missed observation was genuinely derivable
  without the original (redacted) value — using corroborating evidence
  from a sibling sanitized-condition response in the same batch
  (`security_analysis/sanitized` reasoning from the `bearerHeader` name
  alone) — rather than assuming any information difference between
  conditions is automatically "sanitization-independent."
- **`suggest_refactoring/sanitized`'s Usefulness reduction** was based
  on a directly observable property of that response's own generated
  code (literal hardcoded placeholder values in its "after" block), not
  on a comparison to the original response's chosen refactor target.
