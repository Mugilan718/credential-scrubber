# Human evaluation — Batch 5 (`go/config.go`)

Scored against `ai-evaluation/rubric/rubric.md`'s six dimensions only.
Each response scored independently on the six numeric dimensions; the
failure-mode checklist's comparative item is applied comparatively, per
the rubric's own design (consistent with prior batches). No LLM judge
used. No aggregate/composite score computed.

Dimension key: **1** Correctness, **2** Completeness, **3** Consistency,
**4** Usefulness, **5** Misunderstood a sanitized value? (N/A for
original), **6** Relationships between values preserved? (N/A unless the
task itself calls for same/different-value identity judgments — not
applicable to any of this file's 5 tasks; the file has only 2 sensitive
values, `apiKey`/`accessToken`, in different categories).

**Batch/candidate:** `benchmark/dataset/files/go/config.go`,
5 applicable tasks × 2 conditions. **Responses evaluated: 10/10.**

**Protocol deviation — flagged, high confidence:** `explain_code/original.txt`
contains *"...matching the 'New-credential-scrubber' project this lives
in)..."* — an exact, verbatim match to the repository's actual project
directory name, per `batch_record.md` assessed as high-confidence ambient
working-directory leakage (same pattern as Batch 2's confirmed
deviation), not caused by the prompt (`tool_uses: 0`, no project name in
prompt). Preserved unedited; scored below with **no credit given for the
project-name knowledge** — the response's legitimate task content is
scored on its own merits.

---

## Task: explain_code

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** All three parts present and accurate: summary;
breakdown of the package/imports, the five local variables (three
benign, two `fake-`-prefixed credential-shaped strings), and the
`fmt.Println` output; relevant author questions about whether the
fixture tests true-positive detection, false-positive avoidance, or a
specific provider's key format. Correctness/Completeness/Usefulness
scored on this legitimate content — the flagged deviation sentence is
excluded from credit per instruction.

**Failure-mode checklist:** ticking **Other** — environmental deviation
(project-directory-name leak), documented above, not scored or credited.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Same structure, fully accurate. Correctly
reasons that `<GENERIC_SECRET_1>`/`<ACCESS_TOKEN_1>` are "template
placeholders...presumably meant to be substituted by whatever benchmark
harness generates or scans this fixture" — an accurate, non-literal
reading. No mention of the project name or working directory.

**Failure-mode checklist:** none apply.

---

## Task: identify_bug

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Correctly finds no functional bug (compiles and
runs correctly, no logic to misbehave). Quality notes: hardcoded
secret-shaped literals flagged as a poor real-code pattern; notes the
example is minimal/trivial. No deviation.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Correctly finds no functional bug. Quality
notes: hardcoding pattern correctly caveated as "not a real issue" given
the explicit placeholder/fixture context (good, non-literal reasoning);
a genuinely new, independently valid observation absent from the
original — `timeout := 5000` has no unit indicated (seconds vs.
milliseconds); notes all variables are only ever printed. Independently
thorough.

**Failure-mode checklist:** none apply. No sanitization-independent
observation from the original response is missing here.

---

## Task: security_analysis

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Three findings (High/Medium/Low): hardcoded
secrets; the secrets being printed to stdout via `fmt.Println` — a
distinctive, correctly-caught risk specific to this file's actual
behavior (unlike other candidates in this experiment, this file
literally emits the secret values at runtime); and a Low finding that
relying on a source comment rather than a technical control (`.gitignore`/
secret-scanning) doesn't prevent real values from being copy-pasted in
later. No deviation.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Finding 1 (High, hardcoded secrets) and Finding
2 (Medium, secrets printed to stdout) both match the original's
substantive findings with equivalent accuracy and actionable fixes.
Adds an independently valid Minor/Informational note (interspersing
`dbName`/`timeout` with the secret variables increases risk that future
edits add more sensitive fields to the same log line unnoticed) that the
original lacks. Explicitly and correctly reasons about the placeholders'
nature: "these particular values are placeholders in this synthetic
fixture, the pattern shown...is exactly the anti-pattern." Independently
thorough, so Completeness/Usefulness scored 5 on their own merits.

**Failure-mode checklist:** ticking **"Missed a real,
sanitization-independent issue in the sanitized condition that was
correctly found in the original condition"** — the original's Low
finding (relying on a source comment instead of a technical
`.gitignore`/scanner safeguard) is absent here; this is genuinely
sanitization-independent since the same comment text is present verbatim
in the sanitized file. Not reflected in the numeric scores since this
response's own set of findings is independently thorough (and includes
one informational note the original lacks).

---

## Task: generate_unit_tests

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Correctly determines `main()` has no
independently testable logic (no exported functions, no branching, no
return values) and explains why a test would be a "tautology dressed up
as one." Correctly redirects: if this is a fixture for a scrubber, the
scrubber's own detection logic is what merits testing. Fully correct,
complete response for a file with zero testable logic. No deviation.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | 5 | N/A |

**Evidence/rationale:** Same correct conclusion, with additional rigor:
explicitly considers capturing `os.Stdout` and asserting against the
literal printed string (`"...<GENERIC_SECRET_1> <ACCESS_TOKEN_1>\n"`)
before explaining why that would still be a non-meaningful, refactor-
brittle tautology — using the placeholder text only as an illustrative
example of what *not* to write, never as something to reuse functionally.
Adds a constructive suggestion (exposing logic as `buildConfig`/`redact`
functions would make the file genuinely testable) absent from the
original. No divergence in outcome between conditions here — both
correctly decline for the same underlying reason.

**Failure-mode checklist:** none apply.

---

## Task: suggest_refactoring

### Original

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 5 | 5 | 5 | N/A | N/A |

**Evidence/rationale:** Proposes grouping the five loose variables into
a `Config` struct and **implements** a `String()` method in the
"after" code that redacts `APIKey`/`AccessToken` before printing —
directly fixing the plaintext-secret-logging issue this same task's
`security_analysis` sibling identified. Accurate, syntactically valid
Go, fully delivers what it proposes. No deviation.

**Failure-mode checklist:** none apply.

### Sanitized

| Dim | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score | 5 | 4 | 5 | 4 | 5 | N/A |

**Evidence/rationale:** Proposes the same `Config`-struct grouping, with
accurate reasoning about maintainability as fields grow. However, unlike
the original response, the delivered "after" code does **not** implement
a redacting `String()` method — it calls `fmt.Println(cfg)` on a plain
struct with no custom formatting, which (absent a `String()`/`GoString()`
method) would print `APIKey`/`AccessToken` in the clear via Go's default
`%v` formatting. The response acknowledges this only in a closing
parenthetical ("as a bonus, this also makes it natural to give `Config`
a custom `String()` method...") without delivering it in code. This is
directly verifiable in the response's own generated code, independent of
comparison: the "before/after" part of the task's requested structure is
present but its content doesn't fully deliver the security benefit the
response's own text claims is available. Completeness and Usefulness are
each scored 4 — a developer following this suggestion literally would
still need to write the redaction logic themselves.

**Failure-mode checklist:** ticking **"Missed a real,
sanitization-independent issue in the sanitized condition that was
correctly found in the original condition"** — the plaintext-secret-in-
`fmt.Println`-output issue is identically present in both conditions'
source file, was fully fixed in the original condition's delivered
refactor code, and was only gestured at (not fixed) in the sanitized
condition's delivered code.

---

## Batch-level observations

(Qualitative only — no winner is declared, no scores are aggregated.)

- One flagged, high-confidence environmental deviation this batch
  (`explain_code/original`, exact project-directory-name match),
  isolated to 1 of 10 responses, preserved unedited, and excluded from
  scoring credit.
- This file's distinctive property — secrets are not just hardcoded but
  also actively printed via `fmt.Println` — was correctly caught as an
  added risk dimension by both conditions' `security_analysis` responses
  and by the original condition's `suggest_refactoring` response (which
  fully fixed it in code). The one place this file's print-exposure risk
  went unfixed was the sanitized condition's `suggest_refactoring`
  response, which identified the fix conceptually but didn't deliver it.
- `generate_unit_tests` showed no original/sanitized divergence — `main()`
  has zero testable logic in either condition, and both responses reached
  the same correct conclusion with comparable (sanitized: slightly
  greater) rigor.
- `security_analysis/sanitized` missed one minor, sanitization-independent
  observation the original made (reliance on a comment rather than a
  technical safeguard), offset by an informational note of its own the
  original lacked — recorded via the comparative failure-mode checklist
  without lowering any numeric score, since the response was
  independently thorough.
- No instance in this batch of a placeholder treated as a real/working
  value, flagged as itself a security issue, reused in code that
  wouldn't compile, or of a false merge/split.

## Methodology notes

- **Relationships-preserved (dimension 6) marked N/A throughout** — this
  file has only two sensitive values (`apiKey`, `accessToken`) in
  different categories, and no applicable task calls for a
  same/different-identity judgment between them.
- **The comparative failure-mode checklist item was applied consistent
  with prior batches**, including one within-task application
  (`suggest_refactoring/sanitized`'s unredacted "after" code vs. the
  original's redacted one) rather than only the cross-batch pattern seen
  in earlier evaluations — the item's spirit (a real, sanitization-
  independent issue addressed under original but not under sanitized)
  fits this case even though both findings come from the same task
  rather than from a sibling task.
