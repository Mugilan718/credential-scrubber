# Human evaluation — Batch 7 (`config/appsettings.json`)

Scored against `ai-evaluation/rubric/rubric.md`'s six dimensions only.
Each response scored independently on the six numeric dimensions; the
failure-mode checklist's comparative item is applied comparatively, per
the rubric's own design (consistent with prior batches). No LLM judge
used. No aggregate/composite score computed.

Dimension key: **1** Correctness, **2** Completeness, **3** Consistency,
**4** Usefulness, **5** Misunderstood a sanitized value? (N/A for
original), **6** Relationships between values preserved? (N/A unless the
task itself calls for same/different-value identity judgments — this is
the **first batch where dimension 6 is genuinely applicable**, for the
`explain_config_relationships` task, which this file is applicable for
per `manifest.json`).

**Batch/candidate:** `benchmark/dataset/files/config/appsettings.json`,
all 6 tasks applicable per the frozen manifest (per `batch_record.md`'s
documented, user-resolved methodological discrepancy: the batch
instructions had incorrectly implied `explain_config_relationships` was
`not_applicable`; the actual `manifest.json` marks it `applicable`, and
the user directed following the manifest). **Responses evaluated: 12/12.**

**Protocol deviations:** none. Per `batch_record.md`, no response
mentions the project name, working directory, "Credential Scrubber," or
the experiment. The sanitized `explain_code` response's observation that
the `<PLACEHOLDER>`-style bracket notation "supports the 'template'
interpretation" is anticipated, non-deviation reasoning about visible
syntax, not treated as one here.

---

## Task: explain_code

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Accurate three-part breakdown covering app
identity/runtime, logging, database credentials, API key, and
`CustomerId`, correctly identified as a likely per-tenant/deployment
identifier. Relevant author questions about whether secrets are real or
templated, `CustomerId`'s downstream effect, schema validation, and
environment-specific overrides. No deviation.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Same structure, fully accurate; correctly
reasons that the `<PLACEHOLDER>`-style values "are already
redacted/templated placeholders, which supports the 'template'
interpretation" — anticipated, non-literal, correct handling. Adds two
independently valid observations absent from the original (no
TLS/timeout settings; no schema/version field).

**Failure-mode checklist:** none apply.

---

## Task: identify_bug

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Correctly finds no functional bug (static JSON,
structurally valid). Quality notes: plaintext secrets in a
`production`-marked file; no schema indication; `CustomerId`'s format
unexplained. No deviation.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Correctly finds no functional bug. Excellent,
correct non-literal reasoning: "even though they're shown here as
placeholders...if real values were ever substituted in, committing this
file would leak credentials." Independently identifies `Database.Host`
as also a placeholder worth confirming gets a real value injected at
deploy time, and — a genuinely sharp, new observation absent from the
original — that `Port: 8080` combined with `"production"` is unusual for
an internet-facing service typically fronted by a reverse proxy on 443.

**Failure-mode checklist:** ticking **"Missed a real,
sanitization-independent issue in the sanitized condition that was
correctly found in the original condition"** — the original's minor note
about `CustomerId`'s unexplained format is absent here; a small point,
not reflected in the numeric scores given this response's independent
thoroughness (and its own new Port/production observation).

---

## Task: security_analysis

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Five findings (High/High/Medium/Low/Low):
hardcoded DB password; hardcoded API key; the full host+username+password
credential set co-located in one block (maximizing blast radius); no
rotation/expiry metadata; `Logging.Level: "info"` in production
increasing the risk that secrets get duplicated into logs. Thorough,
accurate, well-reasoned throughout. No deviation.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Six findings (High/High/Medium/Medium/Low/Low):
hardcoded password; hardcoded API key; the database host exposing
internal topology (a distinct finding, more granular than the original's
combined treatment); username+password co-location; the file mixing
secret and non-secret config with no structural boundary (a novel,
independently valid template/`.gitignore`-split suggestion); and a
genuinely new angle — `CustomerId` risking cross-tenant misconfiguration
if this file is reused as a template. Independently thorough and
accurate; no misunderstanding of the placeholders anywhere (treats them
as "must be treated as compromised" for rotation purposes, the same
defensively-conservative framing the original response also uses,
without asserting they are or aren't real).

**Failure-mode checklist:** ticking **"Missed a real,
sanitization-independent issue in the sanitized condition that was
correctly found in the original condition"** — the original's Finding 4
(no rotation/expiry metadata) and Finding 5 (`info`-level logging
increasing log-leak risk) are both absent here; sanitization-independent,
not reflected in the numeric scores given this response's own set of
novel, independently-thorough findings.

---

## Task: generate_unit_tests

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Correctly determines the static JSON has no
testable logic, identifying two meaningless test anti-patterns
(re-asserting literals; unenforced schema checks) and redirecting to
the config's *consumer* code as the actual testable surface, with
concrete example test ideas (required-field validation, default
fallback, environment-based branching, type coercion). No deviation.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Same correct conclusion, identifying three
anti-patterns (adding "testing the deserializer" beyond the original's
two) and offering concrete framework-specific test suggestions (xUnit,
Jest, pytest) for the consuming code. No divergence in outcome between
conditions — both correctly decline for the same reason.

**Failure-mode checklist:** none apply.

---

## Task: suggest_refactoring

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 4 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Proposes moving `Password`/`ApiKey` to a secrets
manager/environment variables, replacing them with `${DB_PASSWORD}`/
`${API_KEY}` template syntax in the "after" JSON. Correctness scored 4:
the response's illustrative "Actual secret values supplied at runtime"
shell example (`export DB_PASSWORD=hunter2`, `export API_KEY=Rk8mNpQ2xWvT5hLj9cBs3fYg7uAe1`)
drops the `fake-` prefix present in the real source literals
(`"fake-hunter2"`, `"fake-Rk8mNpQ2xWvT5hLj9cBs3fYg7uAe1"`) — a minor
inaccuracy in reproducing the file's own content that doesn't affect the
refactor's main point.

**Failure-mode checklist:** none of the seven items apply (this
inaccuracy is a factual-reproduction slip, not a placeholder-handling
issue, and occurs in the original condition where no placeholders
exist).

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Proposes extracting `Password`/`ApiKey` (and,
hedged, `Username`) to a secrets manager. The "after" JSON removes the
secret keys entirely rather than replacing them with `${VAR}` syntax,
documenting the env-var/vault-key mapping separately, plus a C# usage
example — a different but equally valid stylistic choice from the
original's in-place template-token approach, not a defect. Notably, this
response makes no attempt to reproduce or guess an "actual" secret value
(since it correctly has none to work from), so it does not repeat the
kind of minor factual slip seen in the original condition's response.

**Failure-mode checklist:** none apply.

---

## Task: explain_config_relationships

*Dimension 6 is genuinely applicable to this task.* Does the response
correctly identify which fields form one logical/functional unit and
which are independent, without asserting a false relationship (merge) or
missing a real one (split)?

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | 5 |

**Evidence/rationale:** Correctly groups `Database.Host`/`Username`/
`Password` as one connection unit; correctly identifies `AppName`/
`Environment`/`Port` as an "identity/deployment context" cluster distinct
from the database group; correctly treats `Logging.Level` and
`CustomerId` as independent; and, critically, does **not** force a false
relationship between `ApiKey` and `CustomerId` — it explicitly flags the
possible-but-unconfirmed connection ("could conceivably pair with
ApiKey...but nothing in the file confirms that relationship") rather
than asserting either a merge or a confident split. This is exactly
correct, appropriately conservative relationship reasoning. No deviation.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | 5 |

**Evidence/rationale:** Same correct groupings, with added reasoning for
*why* each holds ("None of them is meaningful alone — a host without
credentials, or credentials without a host, can't establish a
connection") and a valuable closing synthesis distinguishing explicit
(JSON-nesting) from implicit (top-level) grouping. Reaches the identical,
correctly-hedged conclusion about `ApiKey`/`CustomerId`'s unconfirmed
relationship, applied to the placeholder-bearing fields without any
misunderstanding — `<URL_1>`/`<PASSWORD_1>` (Database group) are
correctly kept distinct from `<API_KEY_1>` (standalone), no false merge
or split anywhere. This is, if anything, the richer of the two responses.

**Failure-mode checklist:** none apply.

---

## Batch-level observations

(Qualitative only — no winner is declared, no scores are aggregated.)

- This is the first batch where the `explain_config_relationships` task
  and dimension 6 are genuinely exercised. Both conditions handled it
  well: correct structural groupings, and — the more telling test —
  neither condition asserted a false relationship between `ApiKey` and
  `CustomerId` where the file genuinely doesn't establish one; both
  correctly hedged instead of guessing. No false merge or split occurred
  anywhere in this task for either condition.
- No protocol/environmental deviations occurred in this batch.
- `generate_unit_tests` showed no original/sanitized divergence — the
  static JSON has no testable logic in either condition, and both
  responses correctly redirected to the config's consumer code.
- The one Correctness ding in this batch was in the **original**
  condition (`suggest_refactoring`), where an illustrative "actual
  value" example dropped the `fake-` prefix present in the real source
  literals — a minor reproduction slip. Notably, the paired sanitized
  response did not make an analogous error, since it never attempted to
  reconstruct or guess a literal secret value in the first place.
- `identify_bug/sanitized` and `security_analysis/sanitized` each missed
  a small number of sanitization-independent observations their paired
  original responses made, each offset by novel observations of their
  own not present in the original — recorded via the comparative
  failure-mode checklist without lowering any numeric score, since each
  sanitized response was independently thorough.
- No instance in this batch of a placeholder treated as a real/working
  value, flagged as itself a security issue, reused in code that
  wouldn't run, or of a false merge/split.

## Methodology notes

- **Relationships-preserved (dimension 6) was scored (not N/A) for
  `explain_config_relationships`**, the first task in this experiment
  where it applies, consistent with the standing rule that dimension 6
  is N/A only when the task doesn't call for a same/different-identity
  judgment — here it explicitly does, and both responses handled it
  correctly.
- **The comparative failure-mode checklist item was applied consistent
  with prior batches** for `identify_bug` and `security_analysis`; in
  both cases the sanitized response's own novel findings were judged to
  offset the omissions, so no numeric dimension was lowered.
- **The original-condition Correctness reduction in
  `suggest_refactoring`** was based on a factual mismatch between the
  response's own illustrative example and the actual source file
  content, independent of any comparison to the sanitized condition.
