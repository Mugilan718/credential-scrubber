# Human evaluation — Batch 2 (`python/config.py`)

Scored against `ai-evaluation/rubric/rubric.md`'s six dimensions only.
Each response scored independently of its paired condition (no
"which is better" comparison feeds into any numeric score), except
where the rubric's own failure-mode checklist explicitly calls for a
comparative judgment (see Methodology notes). No LLM judge used. No
aggregate/composite score computed, per the rubric's own instruction.

Dimension key: **1** Correctness, **2** Completeness, **3** Consistency,
**4** Usefulness, **5** Misunderstood a sanitized value? (N/A for
original), **6** Relationships between values preserved? (N/A unless
the task itself calls for same/different-value identity judgments).

---

## Task: explain_code

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** The response's three required parts (one-sentence
summary; section-by-section breakdown of the config constants, the three
fake-credential declarations, and `get_note()`; questions for the
original author) are all present and accurate. Its description of each
credential's declaration style is correct: `DB_PASSWORD` via
`os.getenv` with a fallback, `api_key` as a bare hardcoded string,
`API_SECRET` as "implicitly concatenating three adjacent string literals
across separate lines."

**Documented environmental deviation — excluded from scoring credit:**
this response contains the sentence *"...this pattern...is likely
designed to exercise a credential-scanning or secret-detection tool
(consistent with the working directory name `New-credential-scrubber`)..."*,
recorded in `batch_record.md` as a protocol deviation (ambient
subagent-runtime working-directory leakage, not derived from the prompt
or the file content — `tool_uses: 0`). Per instruction, the response was
preserved unedited and its legitimate task content is scored normally
above, but **no credit was given** on any dimension for the model
"knowing" the project name — that information was not legitimately
supplied by the source file or prompt, so it plays no role in the
Correctness=5 score (which reflects only the response's claims about the
code itself, all of which are accurate).

**Failure-mode checklist:** none of the seven specific items apply. Ticking
**Other** — see note: the working-directory leak is an environmental
deviation, not a placeholder-handling failure; it does not fit any of
the placeholder-specific checklist items since this is the
original-condition response (no placeholders exist here to misunderstand).

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Same three-part structure, fully and accurately
covered. Correctly explains `<PASSWORD_1>` sits behind a legitimate
`os.getenv` pattern, `<GENERIC_SECRET_2>` (`api_key`) is a bare hardcoded
literal ("the pattern that's generally flagged as risky"), and
`<GENERIC_SECRET_1>` (`API_SECRET`) is built from one literal plus two
now-empty string fragments, correctly identified as "functionally
no-ops" and hypothesized as "leftover formatting from a string that used
to be split across lines...or an attempt to obscure/pad the assignment"
— an accurate, appropriately-hedged reading of what is now visible in
the sanitized file, not an inference about the placeholder's original
content. No mention of the experiment, the project, or any working
directory. Explicitly reiterates the file's own synthetic-fixture
comment rather than treating any value as real.

**Failure-mode checklist:** none apply. The placeholder is at no point
treated as a real/working value, flagged as itself a security issue, or
reused in code that wouldn't run; no false merge/split; the response
does not claim to have inferred what any placeholder "really" stood for
— its concatenation hypothesis is drawn entirely from the visible
structure of the sanitized text itself.

---

## Task: identify_bug

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Correctly concludes "No functional bug found"
(accurate — the file has no control flow to misbehave). Quality notes
are all accurate: the three hardcoded/defaulted secrets, the
`DB_PASSWORD`/`API_SECRET`/`api_key` casing inconsistency
(SCREAMING_SNAKE_CASE vs. snake_case), the multi-line string
concatenation being valid-but-confusable Python, and unused module-level
constants. No deviation present in this response.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Same "no functional bug" conclusion, accurately
reasoned. Quality notes: `<GENERIC_SECRET_1>` concatenated with two empty
strings is correctly called out as dead/no-op code; unused module-level
constants noted; `os.getenv(..., "<PASSWORD_1>")` is correctly reasoned
about as a general pattern ("independent of this being synthetic data,
defaulting a secret to a hardcoded value is a practice worth avoiding")
— the placeholder is treated purely as a stand-in for "a secret," never
as a real password.

Independently, this response's own set of observations is thorough and
internally complete, so Completeness is scored 5 on its own merits (the
rubric scores completeness against the task's request, not against the
other condition's response).

**Failure-mode checklist:** ticking **"Missed a real,
sanitization-independent issue in the sanitized condition that was
correctly found in the original condition."** The original response's
naming-convention observation (`DB_PASSWORD`/`API_SECRET` in
SCREAMING_SNAKE_CASE vs. `api_key` in snake_case) is a real,
sanitization-independent issue — variable *names* are untouched by
placeholder substitution — that this sanitized-condition response does
not mention. Per the rubric's own design (this checklist item is
explicitly comparative), this is recorded here rather than reflected in
any numeric dimension.

---

## Task: security_analysis

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Five findings (High/High/High/Medium/Low), each
with severity, location, description, "why it matters," and a suggested
fix, plus a "Non-issues" section. All claims are accurate: hardcoded
`DB_PASSWORD` fallback, hardcoded `api_key`, the `API_SECRET`
multi-fragment-concatenation-as-scanner-evasion pattern, secrets mixed
with plain config in the same file, and the `environment = "production"`
context amplifying risk if replicated with real values. No deviation
present in this response.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 4 | 5 | 4 | 5 | N/A |

**Evidence/rationale:** Three findings (High/Medium/Low), each accurate:
hardcoded `<GENERIC_SECRET_1>`/`<GENERIC_SECRET_2>` with no
environment-variable sourcing; `DB_PASSWORD`'s hardcoded
`<PASSWORD_1>` fallback correctly reasoned about as a silent-failure
risk independent of whether the value is real; the `API_SECRET`
concatenation-with-empty-strings pattern correctly flagged as a possible
scanner-evasion technique, hedged appropriately ("if intentional...even
if unintentional, it's dead/confusing code"). Completeness is marked 4
rather than 5: independent of any comparison, two real,
still-detectable issues in the sanitized file itself go unmentioned —
secrets mixed with plain config in the same file, and the
`environment = "production"` context — both of which remain visible and
findable in the sanitized file exactly as in the original (neither
depends on the actual secret values). Usefulness marked 4 for the same
reason: the three findings given are each fully actionable, but the
narrower coverage means a developer acting only on this response would
miss two real risk factors that remain present after sanitization.

**Failure-mode checklist:** ticking **"Missed a real,
sanitization-independent issue in the sanitized condition that was
correctly found in the original condition"** — the original response's
Finding 4 (secrets mixed with non-sensitive config in the same file) and
Finding 5 (production-environment context) are both sanitization-independent
(neither depends on the specific secret values) and are absent here.

---

## Task: generate_unit_tests

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Correctly identifies the only two pieces of
genuinely testable logic (`get_note()` and the `DB_PASSWORD`
env-var/fallback line) and explicitly, correctly declines to write
no-op tests asserting static literals equal themselves ("this is not
meaningful verification"). Uses `pytest` + `monkeypatch` +
`importlib.reload`, correctly reasoning that `DB_PASSWORD` is computed
at import time. Generated tests are syntactically valid and would run
against a module matching the file. No deviation present.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Same correct identification of `get_note()` and
the `DB_PASSWORD` fallback as the only testable logic, with the same
sound reasoning for declining to test static literals. Additionally adds
a third, explicitly-labeled "config-content check, not real logic" test
guarding `API_SECRET`'s concatenation against future accidental
whitespace/character changes — a reasonable, correctly-scoped addition
that does not overstate its own value. The generated assertion
`module.DB_PASSWORD == "<PASSWORD_1>"` is **not** a placeholder-reuse
failure: it checks the sanitized file's own actual literal default
value, which the sanitized module genuinely contains, so the test is
correct and would actually pass/run against that file. No hint that the
model believes `<PASSWORD_1>` or `<GENERIC_SECRET_1>` are real values or
is attempting to reconstruct what they originally were.

**Failure-mode checklist:** none apply. Explicitly checked "reused
placeholder text literally in generated code in a way that wouldn't
run/compile" — does not apply here since the placeholder text is used
only to assert equality against the sanitized source's own actual
content, which is correct, runnable behavior, not a misuse.

---

## Task: suggest_refactoring

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Proposes loading `api_key` and `API_SECRET` from
environment variables the same way `DB_PASSWORD` already is, correctly
identifies the inconsistency across the three secrets and the
string-splitting-looks-like-scanner-evasion angle as motivation, and
gives a concrete, accurate before/after code block. No deviation present.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Same core refactor (route `api_key`/`API_SECRET`
through `os.getenv`, matching `DB_PASSWORD`'s pattern), and additionally,
correctly, calls out dropping "the empty-string concatenation used to
build `API_SECRET`" as dead code — an accurate observation about the
visible structure of the sanitized file, not an inference about what the
placeholder originally stood for. The "after" code block sets
placeholder-free fallback defaults (`os.getenv("API_KEY", "")`) rather
than reusing `<GENERIC_SECRET_2>`/`<GENERIC_SECRET_1>` as literal
fallback values — correct, sensible handling that avoids baking a
placeholder into generated code as if it were a real default.

**Failure-mode checklist:** none apply. Considered and rejected ticking
"response reveals it inferred what a placeholder probably stood for" —
the dead-code observation about `API_SECRET`'s trailing empty strings is
grounded entirely in what is visibly present in the sanitized text, not
in any claim about the placeholder's original value.

---

## Batch-level observations

(Qualitative only — no winner is declared, no scores are aggregated.)

- Across all 5 tasks, both conditions produced internally consistent,
  well-structured, technically accurate responses matching each task's
  requested format.
- The one environmental deviation in this batch (`explain_code/original`
  naming the working directory) was isolated to a single response out
  of 10 and did not affect that response's task content, which was
  scored on its own merits with the deviation excluded from credit.
- A recurring, narrower pattern appeared in `identify_bug` and
  `security_analysis`: each sanitized-condition response omitted one or
  more sanitization-independent observations that its paired
  original-condition response caught (a naming-convention inconsistency;
  secrets-mixed-with-config and the production-environment context).
  These were recorded via the rubric's comparative failure-mode checklist
  item rather than by penalizing every numeric dimension; `security_analysis`'s
  omissions were judged independently verifiable enough (the missed
  issues remain fully visible/findable in the sanitized file itself) to
  also lower that response's own Completeness and Usefulness scores.
- `generate_unit_tests` and `suggest_refactoring` showed no such gap in
  either direction — the sanitized-condition responses in both cases
  were, if anything, marginally more thorough (an added guard test; an
  explicit call-out of a sanitization-introduced dead-code artifact).
- No instance anywhere in this batch of a placeholder being treated as a
  real/working value, flagged as itself a security issue, reused in code
  that wouldn't run, or of a false merge/split.

## Methodology notes

- **Relationships-preserved (dimension 6) marked N/A throughout,
  following the precedent set in the Java evaluation:** although
  `python/config.py` contains three distinct sensitive values, none of
  the 5 applicable tasks (`explain_code`, `identify_bug`,
  `security_analysis`, `generate_unit_tests`, `suggest_refactoring`)
  specifically calls for a same/different-identity judgment across
  values, so this dimension was left N/A rather than force-scored. No
  response in this batch exhibited a false merge or false split in any
  case.
- **The failure-mode checklist's "missed a sanitization-independent
  issue" item was applied comparatively**, per rubric.md's own design
  (its notes for this item are explicitly framed against the paired
  condition), while every one of the six *numeric* dimensions was scored
  from each response considered on its own — the one exception is
  `security_analysis/sanitized`'s Completeness and Usefulness scores,
  which were lowered based on an independently-verifiable absence (the
  missed issues are still findable directly in the sanitized file,
  not only "missing relative to the other response").
- **Handling of the documented `explain_code/original` deviation:**
  per instruction, the response was preserved exactly as collected,
  scored normally for its legitimate task content, and given no credit
  on any dimension for the model's knowledge of the project's working
  directory name — that information was not legitimately available from
  the source file or prompt. It is recorded via the failure-mode
  checklist's "Other" box on that response rather than folded into any
  numeric score.
- **Sanitization-introduced artifacts vs. placeholder misunderstanding:**
  the `API_SECRET` field's two trailing empty-string fragments are a
  visible, genuine feature of the sanitized file (the placeholder scheme
  collapsed a three-fragment concatenation into one placeholder plus two
  now-empty fragments). Responses that noticed and discussed this
  structure (`identify_bug/sanitized`, `security_analysis/sanitized`,
  `suggest_refactoring/sanitized`, `explain_code/sanitized`) were not
  penalized or flagged for "inferring what a placeholder stood for" —
  they were reasoning correctly about content that is actually present
  in the sanitized file, not reconstructing the redacted original.
