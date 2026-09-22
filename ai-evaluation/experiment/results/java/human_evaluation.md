# Human evaluation — Batch 1: `java/Config.java`

**Rubric used:** `ai-evaluation/rubric/rubric.md`, unmodified, six dimensions only. **Scope:** 5 tasks × 2 conditions = 10 responses. `explain_config_relationships` is `not_applicable` for this source-code file (per the frozen manifest) and is not scored here.

**Environmental deviations for this batch:** `ai-evaluation/experiment/results/java/batch_record.md` records **no** documented protocol deviations for any of the 10 Java responses ("Procedural deviations: None"). No response in this batch required special handling on that basis; none was excluded or altered.

**Scoring discipline:** each response is scored on its own merits against the task prompt and the file it was actually given. Numeric dimensions were not assigned by comparing conditions against each other. The one rubric item that is explicitly comparative by design — the failure-mode checklist's "missed a real, sanitization-independent issue" — is noted where applicable, consistent with how `rubric.md`'s own `security_analysis` notes define that item.

---

## explain_code

### Original
| Dimension | Score |
|---|---:|
| Correctness | 5 |
| Completeness | 5 |
| Consistency | 5 |
| Usefulness | 5 |
| Misunderstood a sanitized value? | N/A |
| Relationships between values preserved? | N/A |

**Dimension 6 methodology normalization (post-audit, see `scoring_integrity_audit.md` § Dimension 6 Methodology Resolution):** changed from 5 to N/A. `explain_code`'s task template does not itself require reasoning about identity/association/grouping between sensitive values — the file merely happening to contain multiple sensitive values is not sufficient under the adopted rule. The response's correct non-merge/non-split handling (see Evidence below) is preserved as qualitative observation, just no longer numerically scored under Dimension 6.

**Evidence:** Correctly describes all 4 fields, `connect()`'s three literals, and `buildAuthToken()`'s three-fragment concatenation ("Builds a token from three string literals concatenated with `+` across multiple lines"). Follows the exact 3-part template (summary / per-section / questions). No internal contradiction. Correctly treats `apiKey`/`dbPassword`/`clientSecret` as three distinct values and the three `buildAuthToken()` fragments as building **one** token — no merge or split.

**Failure modes:** none applicable.

### Sanitized
| Dimension | Score |
|---|---:|
| Correctness | 5 |
| Completeness | 5 |
| Consistency | 5 |
| Usefulness | 5 |
| Misunderstood a sanitized value? | 4 |
| Relationships between values preserved? | N/A |

**Dimension 6 methodology normalization (post-audit, see `scoring_integrity_audit.md` § Dimension 6 Methodology Resolution):** changed from 5 to N/A. `explain_code`'s task template does not itself require reasoning about identity/association/grouping between sensitive values — the file merely happening to contain multiple sensitive values is not sufficient under the adopted rule. The response's correct non-merge/non-split handling (see Evidence below) is preserved as qualitative observation, just no longer numerically scored under Dimension 6.

**Evidence:** Correctly names all three `connect()` placeholders (`<GENERIC_SECRET_1>`, `<PASSWORD_1>`, `<GENERIC_SECRET_2>`) in the right variable order, and correctly describes `buildAuthToken()`'s `<ACCESS_TOKEN_1>` + two empty strings. Same 3-part structure fully present; no contradiction.
Dimension 5 scored 4, not 5: the response hypothesizes *"these look like template slots meant to be substituted with realistic-looking fake secret strings **before** the file is fed to whatever tool is being benchmarked"* — this gets the substitution direction backwards (the real values were replaced *out*, producing this as the final artifact; nothing is substituted *in* afterward). The claim is appropriately hedged as a question for the author, doesn't affect the response's main conclusions, and matches rubric 4 ("a very minor, inconsequential mis-handling... with no effect on the response's substance").
Relationships: three distinct placeholders kept distinct; `buildAuthToken()` still correctly treated as one reconstructed value.

**Failure modes:** [x] Response reveals it inferred (correctly or not) what a placeholder probably stood for — the substitution-mechanism speculation above.

---

## identify_bug

### Original
| Dimension | Score |
|---|---:|
| Correctness | 5 |
| Completeness | 5 |
| Consistency | 5 |
| Usefulness | 5 |
| Misunderstood a sanitized value? | N/A |
| Relationships between values preserved? | N/A |

**Evidence:** Correctly concludes no functional bug exists (accurate — the file has no control flow to contain one). Quality notes are all verifiably true (unused fields, no separator in the `println`, hardcoded-secret pattern). Matches the requested format (explicit no-bug statement + labeled quality concerns) exactly. Relationships marked N/A — the task doesn't call for discussing value relationships and the response makes no relationship-relevant claim.

**Failure modes:** none applicable.

### Sanitized
| Dimension | Score |
|---|---:|
| Correctness | 5 |
| Completeness | 5 |
| Consistency | 5 |
| Usefulness | 5 |
| Misunderstood a sanitized value? | 5 |
| Relationships between values preserved? | N/A |

**Evidence:** Correctly concludes no functional bug; quality notes are accurate, including correctly identifying `"<ACCESS_TOKEN_1>" + "" + ""` as redundant. Explicitly and correctly frames the values as *"explicitly fake placeholders per the file's own comment"* — no misunderstanding, full marks. Relationships N/A for the same reason as original.

**Failure modes:** none applicable.

---

## security_analysis

### Original
| Dimension | Score |
|---|---:|
| Correctness | 5 |
| Completeness | 5 |
| Consistency | 5 |
| Usefulness | 5 |
| Misunderstood a sanitized value? | N/A |
| Relationships between values preserved? | N/A |

**Dimension 6 methodology normalization (post-audit, see `scoring_integrity_audit.md` § Dimension 6 Methodology Resolution):** changed from 5 to N/A. `security_analysis`'s task template does not itself require reasoning about identity/association/grouping between sensitive values — the file merely happening to contain multiple sensitive values is not sufficient under the adopted rule. The response's correct non-merge/non-split handling (see Evidence below) is preserved as qualitative observation, just no longer numerically scored under Dimension 6.

**Evidence:** All four findings are accurate and grounded in the actual code (hardcoded secrets, the specific concatenated fragments quoted correctly, `println` exposure, `String`-vs-`char[]` memory-retention concern). Full severity/location/description/why/fix format for every finding. Finding 2 correctly treats the three `buildAuthToken()` fragments as one secret rather than three; Finding 1 correctly treats `apiKey`/`dbPassword`/`clientSecret` as three distinct secrets.

**Failure modes:** none applicable.

### Sanitized
| Dimension | Score |
|---|---:|
| Correctness | 5 |
| Completeness | 5 |
| Consistency | 5 |
| Usefulness | 5 |
| Misunderstood a sanitized value? | 5 |
| Relationships between values preserved? | N/A |

**Dimension 6 methodology normalization (post-audit, see `scoring_integrity_audit.md` § Dimension 6 Methodology Resolution):** changed from 5 to N/A. `security_analysis`'s task template does not itself require reasoning about identity/association/grouping between sensitive values — the file merely happening to contain multiple sensitive values is not sufficient under the adopted rule. The response's correct non-merge/non-split handling (see Evidence below) is preserved as qualitative observation, just no longer numerically scored under Dimension 6.

**Evidence:** All three findings are accurate (correctly verifies `buildAuthToken()` is in fact `public`). Full format for every finding. Dimension 5 is a clean 5: the response explicitly separates the fixture's fakeness from the pattern being reviewed — *"Even though these particular values are fake placeholders in this benchmark, the pattern itself is the vulnerability being flagged"* — never treats a placeholder as a real, working secret, never flags the placeholder itself as a new vulnerability. Relationships: three distinct placeholders kept distinct, `buildAuthToken()`'s reconstructed value not split.

**Failure modes:** [x] Missed a real, sanitization-independent issue in the sanitized condition that was correctly found in the original condition — the original's Finding 2 treats the multi-fragment string concatenation itself as a **High**-severity, dedicated finding ("a common technique to evade... scanners... indicates possible intentional scanner evasion"). The sanitized response notices the same structural pattern (`+ "" + ""`) but explicitly downgrades it: *"dead code / a code smell, not a security issue — worth cleaning up but not part of this review's scope."* This concatenation-as-fragmentation pattern is a property of the code's **structure**, present identically in both conditions, independent of whether the underlying value is real or a placeholder — so the divergence in how seriously it's treated is a genuine instance of this failure mode. (This did not lower the sanitized response's own dimension scores above, which were judged on the response's internal merits per the scoring-discipline note; it is recorded here because this specific checklist item is explicitly comparative by the rubric's own design.)

---

## generate_unit_tests

### Original
| Dimension | Score |
|---|---:|
| Correctness | 5 |
| Completeness | 5 |
| Consistency | 5 |
| Usefulness | 5 |
| Misunderstood a sanitized value? | N/A |
| Relationships between values preserved? | N/A |

**Dimension 6 methodology normalization (post-audit, see `scoring_integrity_audit.md` § Dimension 6 Methodology Resolution):** changed from 5 to N/A. `generate_unit_tests`'s task template does not itself require reasoning about identity/association/grouping between sensitive values — the file merely happening to contain multiple sensitive values is not sufficient under the adopted rule. The response's correct non-merge/non-split handling (see Evidence below) is preserved as qualitative observation, just no longer numerically scored under Dimension 6.

**Evidence:** Test assertions are verified correct against the actual source: `buildAuthToken()`'s expected concatenation (`"fakeAB12CD34secretEF56GH78token90"`) and `connect()`'s expected println output both match the real literals exactly, in the right order. Framework stated (JUnit 5), behavior documented per test, explicit "not meaningfully testable" reasoning for the private fields. Self-aware, non-contradictory note about its own `connect()` test's brittleness. No value merged or split.

**Failure modes:** none applicable.

### Sanitized
| Dimension | Score |
|---|---:|
| Correctness | 5 |
| Completeness | 5 |
| Consistency | 5 |
| Usefulness | 5 |
| Misunderstood a sanitized value? | 4 |
| Relationships between values preserved? | N/A |

**Dimension 6 methodology normalization (post-audit, see `scoring_integrity_audit.md` § Dimension 6 Methodology Resolution):** changed from 5 to N/A. `generate_unit_tests`'s task template does not itself require reasoning about identity/association/grouping between sensitive values — the file merely happening to contain multiple sensitive values is not sufficient under the adopted rule. The response's correct non-merge/non-split handling (see Evidence below) is preserved as qualitative observation, just no longer numerically scored under Dimension 6.

**Evidence:** Test assertion `assertEquals("<ACCESS_TOKEN_1>", token)` is factually correct — `buildAuthToken()` really does return that exact string in the sanitized file — so Correctness stays 5. Framework and reasoning otherwise mirror the original's structure and quality.
Dimension 5 scored 4: the response pins the placeholder text as the expected, stable test value with no acknowledgment anywhere in this response that it's a substituted/sanitized value rather than an ordinary literal (contrast with this same batch's `explain_code`/`security_analysis`/`identify_bug` sanitized responses, which all explicitly named the values as placeholders). This is exactly the pattern `ai-evaluation/prompts/generate_unit_tests.md`'s own notes anticipated watching for. It does not affect the response's substance or produce incorrect code — the test is valid and would pass — so this is scored as rubric 4 ("very minor, inconsequential mis-handling... no effect on the response's substance"), not lower.
Relationships: nothing merged or split; `buildAuthToken()` still tested as one value.

**Failure modes:** [x] Treated a placeholder as a real, working value — borderline/mild instance: the placeholder text was used directly as ordinary test-fixture data with no distinguishing treatment, though the resulting test is technically valid.

**Note (not scored):** the sanitized response omits an equivalent to the original's `connect_printsConcatenatedCredentialsToStdOut` test (a full stdout-capture assertion); it only smoke-tests `connect()` for non-throwing. This is a scope/depth difference, not an issue, bug, or misunderstanding — see Batch-level observations.

---

## suggest_refactoring

### Original
| Dimension | Score |
|---|---:|
| Correctness | 5 |
| Completeness | 5 |
| Consistency | 5 |
| Usefulness | 5 |
| Misunderstood a sanitized value? | N/A |
| Relationships between values preserved? | N/A |

**Dimension 6 methodology normalization (post-audit, see `scoring_integrity_audit.md` § Dimension 6 Methodology Resolution):** changed from 5 to N/A. `suggest_refactoring`'s task template does not itself require reasoning about identity/association/grouping between sensitive values — the file merely happening to contain multiple sensitive values is not sufficient under the adopted rule. The response's correct non-merge/non-split handling (see Evidence below) is preserved as qualitative observation, just no longer numerically scored under Dimension 6.

**Evidence:** Accurate before/after; the suggested `requireEnv` helper is valid Java. Full 3-part format (refactoring / why / snippet). `apiKey`, `dbPassword`, `clientSecret` kept as three distinct env-var lookups; `authToken` referenced as one entity in prose.

**Failure modes:** none applicable.

### Sanitized
| Dimension | Score |
|---|---:|
| Correctness | 5 |
| Completeness | 5 |
| Consistency | 5 |
| Usefulness | 5 |
| Misunderstood a sanitized value? | 5 |
| Relationships between values preserved? | N/A |

**Dimension 6 methodology normalization (post-audit, see `scoring_integrity_audit.md` § Dimension 6 Methodology Resolution):** changed from 5 to N/A. `suggest_refactoring`'s task template does not itself require reasoning about identity/association/grouping between sensitive values — the file merely happening to contain multiple sensitive values is not sufficient under the adopted rule. The response's correct non-merge/non-split handling (see Evidence below) is preserved as qualitative observation, just no longer numerically scored under Dimension 6.

**Evidence:** Accurate before/after with valid Java. Dimension 5 is a clean 5: *"they're a serious security liability even in 'synthetic'/example form, since real codebases modeled on this pattern leak credentials this way"* — correctly separates the fixture's fakeness from the real-world pattern risk, without over-claiming. Three placeholders kept as three distinct `requireEnv` calls with three distinct env-var names — no merge or split.

**Failure modes:** none applicable.

---

## Batch-level observations

*(Qualitative only — no winner or aggregate score implied.)*

- Both conditions independently produced technically correct, well-structured responses across all 5 tasks; no response in this batch scored below 4 on any applicable numeric dimension.
- The one substantive content difference observed was in `security_analysis`: the original treated the multi-fragment string concatenation as a dedicated High-severity "scanner evasion" finding, while the sanitized response reasoned about the same structural pattern and explicitly classified it as a non-security code smell instead. Both are internally coherent, defensible readings of the same *structural* pattern (which is present identically in both files) — the divergence is recorded as a failure-mode instance above per the rubric's own definition, not as an error in either individual response.
- In `generate_unit_tests`, the sanitized response's one placeholder-as-literal test assertion (`assertEquals("<ACCESS_TOKEN_1>", token)`) is the only place in this batch where a response used sanitized content without any explicit placeholder acknowledgment elsewhere in the same response — contrasted with `explain_code`, `identify_bug`, and `security_analysis`'s sanitized responses, all of which explicitly named the tokens as placeholders/fakes somewhere in their text.
- The sanitized `generate_unit_tests` response also tested less of `connect()` than the original (smoke test only, vs. a full stdout-capture assertion in the original) — a scope choice each response explained on its own terms, not attributable to any misunderstanding.
- No response in either condition treated a placeholder as a functioning secret, attempted to "use" one, or flagged a placeholder's mere presence as a new vulnerability distinct from the underlying pattern.

## Methodology notes

- **[Superseded, kept for record] Original relationships-preserved N/A judgment call:** for `identify_bug`, both conditions were marked N/A rather than scored, since the task doesn't request relationship analysis and neither response makes a relationship-relevant claim, even though the underlying file does have multi-value structure. This follows the interpretation rule's "relevant to the task" qualifier literally; a stricter reading (score whenever the *file* has relationships, regardless of task) would have produced 5/5 here instead, since neither response merges or splits anything. Flagging this as the one real interpretive ambiguity encountered in this batch. **Post-audit update:** the scoring-integrity audit (`scoring_integrity_audit.md`) found that this batch's *other* four tasks (`explain_code`, `security_analysis`, `generate_unit_tests`, `suggest_refactoring`) had in fact taken the stricter reading explicitly rejected here — scoring Dimension 6 substantively (5/5) purely because the file has multi-value structure, inconsistent with `identify_bug`'s own literal application of the "relevant to the task" qualifier and with every later batch's practice. Per the adopted Dimension 6 Methodology Resolution, those 8 scores (all 4 of the other tasks × 2 conditions) have been normalized to N/A, bringing this entire batch in line with `identify_bug`'s original, correctly-literal reading. See `scoring_integrity_audit.md` § "Dimension 6 Methodology Resolution" for the full rationale and change log.
- **Comparative vs. independent scoring tension:** the failure-mode checklist's "missed a sanitization-independent issue" item is inherently comparative (per `rubric.md`'s own `security_analysis` notes), which sits in tension with the task's "do not compare while assigning an individual score" rule. Resolved by keeping the six numeric dimensions strictly independent per response (verified by re-deriving each score without reference to the paired condition) while still applying the one checklist item as designed. This is noted explicitly rather than silently applying one standard or the other.
- **Dimension 5 for `generate_unit_tests`/sanitized** was the closest scoring call in this batch (4 vs. 5) — resolved in favor of 4 because the pattern the task's own design notes explicitly flagged for attention (asserting against placeholder text) is present, even though it does not produce an incorrect or non-functional test.
