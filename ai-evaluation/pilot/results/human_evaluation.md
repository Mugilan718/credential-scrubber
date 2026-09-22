# Human evaluation — Pilot 001 (java/Config.java × explain_code)

**Status: provisional, single-pilot record.** One file, one task, one
model, one response per condition. This is not a general claim about the
Credential Scrubber system, not a statistically powered result, and not
proof that AI usefulness survives sanitization in general — see
[Limitations](#8-limitations-of-this-pilot).

## 1. Experiment metadata

| Field | Value |
|---|---|
| File | `java/Config.java` |
| Task | `explain_code` (`ai-evaluation/prompts/explain_code.md`, used verbatim) |
| Model | Claude Sonnet 5 (`claude-sonnet-5`) |
| Conditions | Original vs. sanitized |
| Responses scored | One per condition (no repeated sampling) |
| Rubric | `ai-evaluation/rubric/rubric.md` (existing rubric, unmodified, no new dimensions added) |
| Original source | `ai-evaluation/pilot/original/java/Config.java` |
| Sanitized source | `ai-evaluation/pilot/sanitized/java/Config.java` |
| Original response | `ai-evaluation/pilot/results/original_explain_code.txt` |
| Sanitized response | `ai-evaluation/pilot/results/sanitized_explain_code.txt` |
| Execution record | `ai-evaluation/pilot/results/README.md` (model/settings/independence confirmation) |
| Rater | Single human evaluator (this record), scores provisional |

## 2. Original condition

**Input:** the unmodified `Config.java` fixture — a class with four
"normal" fields, a `connect()` method declaring three real fake-secret
string literals (`apiKey`, `dbPassword`, `clientSecret`) and printing
their concatenation, and a `buildAuthToken()` method building one token
from three concatenated literal fragments.

**Response summary (factual, not evaluative):** the response gave a
one-sentence purpose statement, five section paragraphs (header comment,
fields, `connect()`, `buildAuthToken()`, and an explicit restatement of
the header comment's intent), and three "things I'd ask the author"
questions. It named and quoted the real literal fragments
(`"fakeAB12"`, `"CD34secretEF56"`, `"GH78token90"`) when describing
`buildAuthToken()`, and explicitly called out the `connect()` →
`System.out.println` pattern as "a serious secrets-leak issue" in a real
codebase. Full text: `original_explain_code.txt`.

## 3. Sanitized condition

**Input:** the same file with `placeholder_mode=True` engine output —
`apiKey`/`dbPassword`/`clientSecret` replaced with
`<GENERIC_SECRET_1>`/`<PASSWORD_1>`/`<GENERIC_SECRET_2>`, and
`buildAuthToken()`'s three fragments replaced with `<ACCESS_TOKEN_1>`
followed by two emptied fragments (line count and concatenation
structure unchanged).

**Response summary (factual, not evaluative):** same three-part
structure (summary, section breakdown, author questions). It correctly
described the four placeholder tokens as belonging to `connect()`
(three, individually distinguished) and `buildAuthToken()` (one, with two
empty continuation fragments), described `connect()`'s `println` as "a
sink... where the secret is used/exposed," and explicitly characterized
the tokens as "placeholder tokens" / "clearly templated stand-ins rather
than actual string literals." Full text: `sanitized_explain_code.txt`.

## 4. Score table (rubric.md's existing six dimensions, 1–5)

The human evaluator supplied scores under six plain-language labels
(`Code understanding`, `Structure preservation`, `Semantic
understanding`, `Task usefulness`, `Security/sanitization`, `Placeholder
impact`). These labels are not the literal dimension names in
`rubric/rubric.md`. To satisfy "use the existing rubric, do not invent a
new one," the table below is built on **rubric.md's own six named
dimensions**, with the evaluator's original label shown alongside each
row as the working title it was scored under. **No numeric score was
changed** — every value below is exactly as supplied. The mapping itself
is an interpretation, documented row by row in [§5](#5-evidence-supporting-every-score),
with one pairing (row 3) explicitly flagged as the weakest fit.

| Rubric dimension (`rubric.md`) | Evaluator's label | Original | Sanitized | Δ |
|---|---|---:|---:|---:|
| 1. Correctness | Code understanding | 5 | 5 | 0 |
| 2. Completeness | Structure preservation | 5 | 5 | 0 |
| 3. Consistency | Semantic understanding | 5 | 4 | −1 |
| 4. Usefulness | Task usefulness | 5 | 5 | 0 |
| 5. Misunderstood a sanitized value? | Placeholder impact | 5* | 4 | −1 |
| 6. Relationships between values preserved? | Security/sanitization | 5 | 5 | 0 |

\* Rubric.md defines dimension 5 as "specific to responses on the
**sanitized** condition (mark N/A for original-condition responses)" —
there is no placeholder in the original condition to misunderstand. The
evaluator recorded `5` for the original row rather than `N/A`; read as
"not applicable / no issue present" rather than a literal quality score.
This is a labeling technicality, not a contradiction with the response
text, so the value is preserved unchanged per instruction.

## 5. Evidence supporting every score

### 1. Correctness ("Code understanding") — 5 / 5
Rubric 5 = "Everything stated is accurate; no factual errors about the
code's behavior."
- **Original (5):** every structural claim checks out against the
  source — four fields correctly named, `connect()` correctly described
  as declaring three secret-like locals and printing their concatenation,
  `buildAuthToken()` correctly described as concatenating three literal
  fragments into one returned value. No factual error found.
- **Sanitized (5):** every structural claim checks out against the
  *sanitized* source it was actually given — three placeholder-valued
  locals in `connect()`, one non-empty placeholder plus two empty
  fragments in `buildAuthToken()`, correctly attributed to the right
  lines/methods. Correctness is evaluated against what each response was
  shown, not against the hidden original values — consistent with
  `ai-evaluation/README.md`'s framing (Phase 2 measures response quality
  given the input actually provided).

### 2. Completeness ("Structure preservation") — 5 / 5
Rubric 5 = "Fully addresses every part of the task's requested
structure" (one-sentence summary; per-section paragraph; open questions).
- **Original (5):** summary sentence present; five section paragraphs
  (more granular than the minimum three logical blocks, but nothing
  requested is skipped); three explicit author-questions.
- **Sanitized (5):** summary sentence present; "Section breakdown" with
  four sub-bullets covering header/fields/`connect()`/`buildAuthToken()`;
  three explicit author-questions. Same structural completeness as the
  original, one-for-one against the template's three numbered parts.

### 3. Consistency ("Semantic understanding") — 5 / 4 — *weakest-fit row, see caveat*
Rubric.md's "Consistency" is about **internal self-contradiction** — does
the response disagree with itself. On a close read, **neither response
contains a literal internal contradiction**; both are self-consistent
prose. The evaluator's own label for this row, "semantic understanding,"
describes a different property than rubric.md's "Consistency" defines,
and no single remaining rubric dimension is a clean match for it (the
other five rows already account for correctness, completeness,
usefulness, placeholder-misunderstanding, and value-relationships). The
mapping above places it here only because it is the one dimension left
once the other five labels are matched to their best-fitting rubric
counterpart — **flagged explicitly as an unresolved labeling gap**,
worth the evaluator relabeling or re-deriving in a future pass rather
than treating this row's rubric-dimension name as authoritative.

What *is* concretely observable, and is the most likely basis for the
provisional 1-point gap: the sanitized response states more specific
interpretations than the placeholder text alone supports — e.g. calling
`<GENERIC_SECRET_2>`/`clientSecret` "an OAuth-style client secret" (a
specific sub-type the generic placeholder does not itself indicate). That
is real, quotable evidence of a *lower-certainty basis* for the
sanitized response's claims, even though it does not rise to a literal
self-contradiction. The score (5, 4) is preserved as given because
nothing in either response actively contradicts it — but the dimension
name it is filed under here should be read with that caveat.

### 4. Usefulness ("Task usefulness") — 5 / 5
Rubric 5 = "Directly actionable; a developer could act on it with no
further digging."
- **Both (5):** for a pure comprehension task, both responses give a
  developer an accurate, structured, immediately usable orientation to
  the file, plus concrete follow-up questions. No meaningful usefulness
  gap for *this* task — `explain_code` does not require knowing the real
  secret values to be useful, only the file's shape and intent.

### 5. Misunderstood a sanitized value? ("Placeholder impact") — 5\* / 4
Rubric 4 = "A very minor, inconsequential mis-handling (e.g. slightly odd
phrasing) with no effect on the response's substance."
- **Original:** N/A per rubric.md's own instruction (no placeholder
  present) — recorded as 5/"no issue" here; see the table footnote.
- **Sanitized (4):** the response explicitly and correctly named the
  tokens as stand-ins — *"clearly templated stand-ins rather than actual
  string literals"* — and never treated one as a real, working value or
  flagged a placeholder itself as a vulnerability (both of rubric.md's
  worse failure modes, 1–2, are absent). The 4-rather-than-5 is supported
  by two concrete, quotable over-specifications beyond what the
  placeholder itself licenses: labeling `clientSecret`'s placeholder "an
  OAuth-style client secret," and speculating the real value might look
  like *"`sk_live_...`-style or AWS-key-shaped strings."* Neither claim
  affects the response's main conclusions (which are about the file's
  structure and intent, not the secrets' real content) — matching
  rubric.md's "4" description precisely: minor, inconsequential,
  substance unaffected.

### 6. Relationships between values preserved? ("Security/sanitization") — 5 / 5
Rubric 5 = "All same/different relationships correctly reflected."
- **Original (5):** `apiKey`/`dbPassword`/`clientSecret` correctly kept
  as three distinct values; `buildAuthToken()`'s three fragments
  correctly described as building **one** `authToken`, not three secrets.
- **Sanitized (5):** `<GENERIC_SECRET_1>`/`<PASSWORD_1>`/`<GENERIC_SECRET_2>`
  correctly kept as three distinct values; `<ACCESS_TOKEN_1>` plus two
  empty fragments correctly described as **one** reconstructed token, not
  three. No false merge, no false split, in either condition. This row
  is the closest thing this pilot has to a direct test of the research
  question's core claim (deterministic, typed, per-value placeholders —
  as opposed to one shared mask — preserve which values are the same vs.
  different) and, on this one file, it held.

## 6. Failure-mode checklist (`rubric.md`, sanitized condition)

- [ ] Treated a placeholder as a real, working value
- [ ] Flagged a placeholder itself as a security issue
- [ ] Reused placeholder text literally in generated code in a way that wouldn't run/compile *(N/A — task doesn't generate code)*
- [ ] False merge — treated two different real values as the same
- [ ] False split — treated the same real value as two different ones
- [ ] Missed a real, sanitization-independent issue in the sanitized condition that was correctly found in the original condition *(near-miss, not checked — see note below)*
- [x] Response reveals it inferred (correctly or not) what a placeholder probably stood for
- [ ] Other

**Note on the near-miss:** the original response explicitly called the
`connect()` → `println` pattern "a serious secrets-leak issue" in a real
codebase; the sanitized response described the same line as "a sink...
where the secret is used/exposed." Both flag the same underlying
concern, in different words — not counted as "missed," but close enough
to note explicitly rather than silently pass over.

## 7. Important observations about placeholder interpretation

- **The sanitized response correctly recognized placeholders as
  stand-ins**, not as real values: *"The placeholders
  (`<GENERIC_SECRET_1>`, `<PASSWORD_1>`, etc.) are clearly templated
  stand-ins rather than actual string literals."* It never attempted to
  use one as a literal value, and never treated the presence of a
  placeholder as itself a new vulnerability distinct from the underlying
  (absent) secret.
- **The sanitized response inferred semantic information from variable
  names and program structure**, not from placeholder content it could
  not see — e.g. it described `<GENERIC_SECRET_1>` (whose category label
  is the generic `GENERIC_SECRET`, not `API_KEY` — see
  `ai-evaluation/pilot/README.md`'s documented category-resolution
  observation for this file) as standing in for *"a generic API key,"*
  recovering that specific meaning purely from the variable name
  `apiKey` and the surrounding code, independent of the placeholder's own
  (less specific) category label. This is directly relevant to the
  research question: variable-name and structural signal appear to be
  carrying real semantic weight here, separately from placeholder
  category precision.
- **The sanitized response also made some assumptions about the
  specific meaning of placeholders** beyond what the placeholder text
  itself supports — most notably reading `clientSecret`'s
  `<GENERIC_SECRET_2>` as *"an OAuth-style client secret"* specifically,
  and speculating about concrete real-value shapes (*"`sk_live_...`-style
  or AWS-key-shaped strings"*). **This is recorded as an observation and
  a limitation, not as proof of a failure** — nothing here caused an
  incorrect conclusion about the file's structure or purpose, and it is
  exactly the kind of pattern the rubric's failure-mode checklist exists
  to surface for tracking across many results, not to penalize in
  isolation on one pilot.

## 8. Limitations of this pilot

- **Sample size: one file, one task, one model, one run per condition.**
  These scores describe this single `(file, task)` pair only. They are
  not a benchmark result, not a claim about Credential Scrubber's
  placeholder scheme in general, and not evidence about any other file,
  task, or model. No statistical significance is claimed or computable
  from n=1.
- **The fixture's own header comment is identical in both conditions.**
  Both `original/java/Config.java` and `sanitized/java/Config.java`
  carry the same `// Synthetic benchmark fixture - every value below is
  fake and was invented for this benchmark. None of it is a real
  credential.` comment, inherited from the underlying dataset fixture,
  not introduced by sanitization. Both responses correctly picked up on
  this and described the file as a benchmark/test fixture throughout —
  this is not a condition leak (both conditions carry the same text, so
  it can't reveal *which* condition a response is looking at), but it
  does mean neither response reflects how a model would read an
  unlabeled, ordinary developer file. This was already flagged before
  the responses were collected (`ai-evaluation/pilot/README.md`) and is
  reconfirmed here as observed in both raw responses.
- **Category-label imprecision on this specific file.** As documented
  before this pilot ran, `apiKey` and `clientSecret` resolve to the
  generic `GENERIC_SECRET` category rather than the more descriptive
  `API_KEY`, a known engine behavior not modified for this evaluation.
  The sanitized response still recovered "API key" semantics for
  `apiKey` from the variable name, independent of the less-specific
  category label — worth tracking whether that holds on files where
  variable names are less self-descriptive.
- **Single human rater, provisional scores.** No second rater, no
  inter-rater agreement measure, no blind-rating separation was applied
  for this pilot (the evaluator saw both `condition` labels while
  scoring, unlike the blind-rating process `results/README.md` describes
  for the full experiment).
- **Procedural caveats carried over from response collection** (full
  detail in `ai-evaluation/pilot/results/README.md`): temperature and
  max-output-tokens were not independently controllable through the
  tooling used to collect these two responses, and the "AI agent" used
  was a Claude Code subagent rather than a bare model API call. Both
  caveats applied identically to both conditions.
- **The rubric-dimension mapping in §4 is an interpretation**, not a
  literal restatement of scores the evaluator explicitly assigned to
  `rubric.md`'s named dimensions — see the row-3 caveat in particular.

## 9. Conclusion

On this single file, task, and model: the sanitized-condition response
correctly explained the code's structure and intent, correctly
recognized every placeholder as a stand-in rather than a real value, and
correctly preserved which secrets were the same value versus different
ones — the property the deterministic placeholder design exists to
provide. The two dimensions with a provisional 1-point gap (sanitized
lower) both trace to the same observed pattern: the sanitized response
occasionally inferred more specific meaning for a placeholder than the
placeholder's own content licenses, drawing on variable names and
structure to do so. That is a real, evidenced observation from this one
run, worth tracking across the full 9-file × 6-task experiment — it is
**not** evidence that sanitization "works" or "preserves usefulness" as
a general claim, not a result with any statistical backing, and not a
substitute for running the fuller experiment this pilot exists to
validate the procedure for.
