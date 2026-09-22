# Scoring-integrity audit — completed human evaluation (96/96)

Read-only audit of the human-evaluation phase of the 9-file × 6-task ×
2-condition AI evaluation experiment. No file other than this report was
created or modified to produce it. No statistical/aggregate results were
computed. No score, evidence note, or methodology note in any
`human_evaluation.md` was changed.

## 1. Audit scope

Verified: the 9 `human_evaluation.md` files under
`ai-evaluation/experiment/results/<candidate>/`; the 9 corresponding
`batch_record.md` files; all 96 raw AI response `.txt` files; the frozen
experiment inputs (`manifest.json`, `rubric.md`, the 6 task prompts plus
`prompts/README.md`, the 9 original dataset files, the 9 sanitized
fixtures); and `git status` / file hashes as available. Not in scope
(per instructions): recalculating or adding any statistical result.

## 2. Expected evaluation matrix

| Candidate | Tasks applicable | Responses | Evaluated |
|---|---|---:|---:|
| java/Config.java | 5 (no `explain_config_relationships`) | 10 | 10 |
| python/config.py | 5 | 10 | 10 |
| javascript/config.js | 5 | 10 | 10 |
| typescript/auth.ts | 5 | 10 | 10 |
| go/config.go | 5 | 10 | 10 |
| csharp/Config.cs | 5 | 10 | 10 |
| config/appsettings.json | 6 | 12 | 12 |
| config/settings.yaml | 6 | 12 | 12 |
| edge_cases/false_positives.properties | 6 | 12 | 12 |
| **Total** | | **96** | **96** |

Nominal grid: 9 files × 6 tasks × 2 conditions = 108 cells. Intentionally
`not_applicable` (per `manifest.json`'s `task_applicability_matrix`,
`explain_config_relationships` for the 6 source-code files): 6 × 1 × 2 =
**12 cells**. 108 − 12 = **96 applicable cells**, matching the frozen
`expected_total_response_count` in `manifest.json`.

## 3. Completeness result — **PASS**

- All 9 `human_evaluation.md` files exist at the expected paths (glob-
  confirmed) and are non-trivial in length (191–341 lines each).
- Per-batch score-table count (`| Score | ... |` rows, the horizontal
  format used by 8 of the 9 files): javascript 10, config-yaml 12,
  python 10, typescript 10, go 10, config 12, csharp 10, edge_cases 12 —
  sums to 86. The 9th file, `java/human_evaluation.md`, uses a different,
  earlier-established **vertical** table format (`| Dimension | Score |`
  per response, confirmed by direct read); it contains exactly 10
  dimension-tables (one per response), each with all 6 rubric dimension
  rows. 86 + 10 = **96 scored responses**, matching the expected total
  exactly.
- Per-batch task-section headers were enumerated directly: all 6
  source-code batches (java, python, javascript, typescript, go, csharp)
  contain exactly the 5 applicable task sections and correctly contain
  **no** `explain_config_relationships` section; all 3 config-shaped
  batches (config, config-yaml, edge_cases) contain all 6 task sections
  including `explain_config_relationships`. This structurally confirms
  the 12 intentionally-`not_applicable` cells are accounted for (never
  scored, consistent with `manifest.json` and every batch's own
  `batch_record.md`).
- Both Original and Sanitized conditions are present for every scored
  task in every batch (confirmed via the per-task Original/Sanitized
  subsection structure in all 9 files).
- No duplicate response evaluations were found: each (file, task,
  condition) triple appears in exactly one section of exactly one
  `human_evaluation.md`, with no repeated or orphaned sections.
- No missing file/task/condition combinations were found.

## 4. Rubric-compliance result — **PASS WITH ONE ISSUE FLAGGED FOR REVIEW**

- **Correctness / Completeness / Consistency / Usefulness:** every one
  of the 96 responses carries a numeric 1–5 score for all four
  dimensions in every batch. No missing, blank, or out-of-range value
  was found (values observed across the whole dataset: 2, 3, 4, 5 only —
  no 0, no 6+, no decimals, no free-text substituted for a score).
- **Dimension 5 (Misunderstood a sanitized value?):** correctly marked
  `N/A` for every one of the 48 Original-condition responses, and scored
  numerically (4 or 5 throughout the dataset) for every one of the 48
  Sanitized-condition responses — including the one negative-control
  batch (`edge_cases`), where the rubric's own "not remarked on at all
  where that's appropriate" clause under the 5-band was correctly
  applied (scored 5, not N/A, since that file has no placeholders to
  misunderstand) rather than defaulting to N/A. Verified row-by-row
  across all 96 responses (Original always paired with `N/A` in this
  column; Sanitized always paired with a number).
- **Dimension 6 (Relationships between values preserved?):** scored
  (not N/A) for all 6 of the `explain_config_relationships` responses
  (config ×2, config-yaml ×2, edge_cases ×2) — the task this dimension
  exists for. Marked `N/A` for the other 90 responses in the 8 batches
  where the task doesn't call for a same/different-identity judgment —
  **except Java**, see below.
- **No invalid scores** were found anywhere in the dataset.
- **No missing scores without explanation** were found — every N/A is
  either self-evidently correct (dimension 5 on an Original response) or
  accompanied by a one-line rationale in the surrounding text.
- **No confusion between Consistency and Original-vs-Sanitized
  agreement** was found: every Consistency justification read refers to
  the response's own internal coherence ("no internal contradiction,"
  "no self-contradiction"), never to whether it agrees with its paired
  condition. Separately **noted for awareness, not a compliance
  failure**: Consistency is scored 5 for all 96 responses in this
  dataset — no response was ever found internally self-contradictory.
  This is plausible (none of the 96 responses are long or
  multi-step enough to easily self-contradict) but means this dimension
  currently carries zero discriminative signal across the whole
  experiment; a future reader should not mistake "always 5" for
  "not actually checked" — spot-reading confirms a rationale was written
  for each one, not defaulted silently.

### Issue: Dimension 6's applicability standard drifted between the Java batch and every subsequent batch

`java/human_evaluation.md`'s own "Methodology notes" section states the
rule it actually used: dimension 6 is scored (not N/A) whenever the
*response itself* makes a relationship-relevant claim, even for tasks
that don't explicitly request relationship analysis — explicitly
because the file has genuine multi-value structure (4 distinct secrets).
Under this rule, Java scored dimension 6 **5/5 for 4 of its 5 tasks**
(`explain_code`, `security_analysis`, `generate_unit_tests`,
`suggest_refactoring` — both conditions each), marking it N/A only for
`identify_bug`, where it explicitly notes neither response makes any
relationship-relevant claim. Java's own notes explicitly flag the road
not taken: *"a stricter reading (score whenever the file has
relationships, regardless of task) would have produced 5/5 here
instead."*

Every subsequent batch (Python, JavaScript, TypeScript, Go, C#, and the
5 non-`explain_config_relationships` tasks in JSON/YAML/Properties)
instead applied that stricter reading's *opposite* — dimension 6 is
`N/A` for **every** task except `explain_config_relationships`,
regardless of whether the file has multi-value structure or the
response makes an implicit relationship-relevant claim. Several of these
batches' own "Methodology notes" sections describe this as **"following
the precedent set in the Java evaluation"** or "consistent with the Java
evaluation" (Python, JavaScript, TypeScript, Go, C# all use close
variants of this phrase) — this characterization does not match what
Java's file actually did for 4 of its 5 tasks.

**Practical effect:** this is an inconsistency in how strictly dimension
6 was applied, not an error in any individual score — every dimension-6
score in the dataset (Java's 5/5s included) is individually defensible
on its own evidence, and no false merge/split was ever scored anywhere.
The effect is on **cross-batch comparability**: Java has 8 non-N/A
dimension-6 data points where every other source-code batch
(Python/JS/TS/Go/C#) has 0, purely as a byproduct of which applicability
rule was used, not of any difference in the underlying responses'
quality. Anyone later aggregating or comparing dimension 6 across
batches should treat Java's non-`identify_bug` dimension-6 scores as
using a different (looser) inclusion rule than every other source-code
batch, and should decide explicitly whether to harmonize, exclude, or
footnote them before drawing any cross-batch conclusion from that
dimension. **Not fixed here** — per instruction, this audit flags rather
than reinterprets or rewrites the evaluator's recorded judgments.

## 5. Failure-mode consistency result — **PASS (with one formatting note)**

- In every one of the 96 responses, the failure-mode checklist is kept
  in a section clearly separate from the six numeric-dimension score
  table, under a **"Failure modes:"** (Java) or **"Failure-mode
  checklist:"** (all 8 other batches) label. This is a **cosmetic
  heading-text difference only** (Java's file predates the standardized
  template used from Python onward) — both forms equally keep the
  checklist mechanically separate from the numeric table, and neither
  numeric score in any response was found to depend on a failure-mode
  tick or vice versa.
- All 8 categories named in the audit instructions were checked for
  correct, non-overlapping use across the dataset:
  - **Placeholder treated as a real/working value** — ticked once
    (Java, `generate_unit_tests`/sanitized: "borderline/mild instance...
    though the resulting test is technically valid"), explicitly scoped
    as mild and explained; not ticked anywhere it wasn't demonstrated.
  - **Placeholder incorrectly flagged as a security issue** — never
    ticked anywhere in the dataset; spot-checks of `security_analysis`
    responses across all 9 batches confirm every one explicitly
    separates "this is a placeholder" from "the pattern is the issue,"
    consistent with this never triggering.
  - **Unrunnable placeholder reuse** — never ticked; every batch's
    evaluator notes explicitly considered and rejected this category at
    least once (e.g., Java's, C#'s, and TypeScript's `suggest_refactoring`/
    `generate_unit_tests` evidence sections explicitly reason through why
    a given placeholder quotation is *not* an instance of this).
  - **False merge / False split** — never ticked anywhere; every
    `explain_config_relationships` response (the task most likely to
    exercise this) was explicitly checked and confirmed clean in its own
    evidence text.
  - **Reconstructed secret** — no dedicated rubric checklist item exists
    under this exact name (the closest is "response reveals it inferred
    what a placeholder probably stood for"); that item was ticked once
    (Java, `explain_code`/sanitized, the substitution-mechanism
    speculation) and considered-and-rejected explicitly in several other
    responses' evidence text (e.g., JavaScript `explain_code`/sanitized,
    C# `security_analysis`/sanitized). No case of an actual value
    reconstruction was found.
  - **Missed sanitization-independent issue** — the one checklist item
    the rubric itself defines as comparative; ticked in roughly a dozen
    responses across Java, Python, JavaScript, TypeScript, Go, C#, JSON,
    and Properties batches, each with a specific named omission and an
    explicit note that it was **not** used to lower any numeric score
    unless the omission was independently verifiable against the file
    itself (documented case-by-case in each batch's evidence text; e.g.
    YAML's evaluation explicitly declines to tick this item for a
    genuinely value-dependent omission, distinguishing it from a
    structurally-derivable one).
  - **Environmental/protocol deviation** — ticked (as "Other," since the
    rubric's fixed checklist has no dedicated deviation box) for every
    response containing a documented deviation: Python `explain_code`/
    original; TypeScript `security_analysis`/original; Go `explain_code`/
    original; YAML `explain_code`/original; Properties
    `generate_unit_tests`/original **and** /sanitized. See §6 for the
    full inventory.
  - **Other documented issues** — used appropriately for the
    environmental-deviation cases above; no unexplained "Other" tick was
    found.
- No case was found of a failure-mode tick silently altering a numeric
  score without an explicit note explaining the relationship (or lack of
  one) between the two.

## 6. Environmental/protocol deviation inventory

| # | Batch | Task | Condition | Type | Confidence (as documented) | Excluded from scoring credit? | Affects result interpretation? |
|---|---|---|---|---|---|---|---|
| 1 | Python | `explain_code` | original | Exact project-directory-name match (`New-credential-scrubber`) | High (exact, distinctive string) | Yes — explicitly, in evidence text | No — isolated to 1/96 responses; content unrelated to any scrubbed value |
| 2 | TypeScript | `security_analysis` | original | Possible working-directory leak (the word "website," matching the session's actual path component) | **Low/uncertain** — `batch_record.md` and the evaluation both explicitly flag this as not distinguishable from ordinary generic phrasing | Yes — explicitly, in evidence text | No — the underlying security point is valid independent of the word choice |
| 3 | Go | `explain_code` | original | Exact project-directory-name match | High | Yes | No |
| 4 | YAML (config-yaml) | `explain_code` | original | Exact project-directory-name match | High | Yes | No |
| 5 | Properties (edge_cases) | `generate_unit_tests` | original | Exact project-directory-name match | High | Yes | No |
| 6 | Properties (edge_cases) | `generate_unit_tests` | sanitized | Project-directory-name match **and** full absolute filesystem path (`D:\New-credential-scrubber`) — the single most severe leak documented across the whole experiment | High | Yes — explicitly, on every dimension, despite the response otherwise being strong | No — isolated; the leaked information is the project's own path, not a scrubbed secret value |
| — | Java | — | — | **None documented** (`batch_record.md`: "Procedural deviations: None"; confirmed in `human_evaluation.md`'s opening scope note) | — | — | — |
| — | JavaScript | — | — | **None documented** (`batch_record.md`: "None detected"; two spontaneous placeholder-syntax observations explicitly assessed as non-deviations, not counted) | — | — | — |
| — | C# | — | — | **None documented** (`batch_record.md`: "None detected"; one spontaneous, non-deviation observation about the concatenation pattern) | — | — | — |
| — | JSON (config) | — | — | **None documented** (`batch_record.md`: "None detected"; one spontaneous, non-deviation observation about bracket-style placeholders) | — | — | — |

**No additional, previously-undocumented deviation was found** during
this audit beyond the 6 listed above and the 2 low-confidence
observations already surfaced in `collection_integrity_audit.md` (C#
Batch 6 and Properties Batch 9 `explain_code`/sanitized generic
"credential-scrubbing tool" phrasing) — both of those were explicitly
addressed in their respective batches' `human_evaluation.md` files as
non-deviation, content-grounded reasoning, consistent with
`collection_integrity_audit.md`'s own low-confidence assessment of them.

**Cross-cutting observation:** all 6 confirmed/flagged deviations stem
from the same structural cause already identified during collection —
ambient Claude Code subagent working-directory/session-metadata exposure
independent of prompt content (every affected session reported
`tool_uses: 0`). This is a tooling limitation of the evaluation
methodology itself, not a property of the sanitization mechanism under
test: in every instance, the leaked information is the *project's own
directory name or path*, never a scrubbed secret value from the
candidate files. This should be disclosed as a methodology limitation in
any write-up of results, but does not, on its own, invalidate or bias
any individual response's task-content scoring, since all such content
was explicitly excluded from credit before scoring.

## 7. Raw-response integrity result — **PASS, with one stated limitation**

- All 96 raw response `.txt` files and all 9 `batch_record.md` files
  exist at their expected paths and were re-hashed (SHA-256) in this
  audit.
- **Frozen-input hashes (manifest, rubric, prompts, original dataset
  files, sanitized fixtures)** were independently re-verified byte-for-
  byte against the baseline table recorded in
  `ai-evaluation/experiment/collection_integrity_audit.md` (written
  before human evaluation began): all 27 hashes checked — 9 original
  dataset files, 9 sanitized fixtures, `manifest.json`, `rubric.md`, 6
  task prompts, `prompts/README.md` — **matched exactly**, with no
  exceptions.
- **Raw AI response files:** `collection_integrity_audit.md` did not
  persist a per-file SHA-256 table for the 96 response files themselves
  (only aggregate size/duplicate/timestamp observations), so there is no
  independently-recorded pre-evaluation hash baseline for those specific
  files to diff against in this audit. Within *this* conversation,
  however, hashes for 88 of the 96 raw response files (8 of 9 batches:
  python, javascript, typescript, go, csharp, config, config-yaml,
  edge_cases) were computed and displayed immediately after each
  batch's `human_evaluation.md` was written, and this audit's fresh
  re-hash of those same 88 files matches those values exactly. For the
  remaining 8 files (java), no hash was displayed in the currently-visible
  portion of this conversation, though the prior session's own record
  states its raw responses were hash-verified unchanged at the time
  `java/human_evaluation.md` was written; this audit additionally
  confirms no write/edit operation targeting any `java/*/*.txt` file
  occurred at any point in this conversation's visible tool-call history.
  **Stated limitation:** this audit did not independently re-derive a
  hash for the java raw-response files against a value computed *before*
  scoring began — only against the java-batch-record's own account and
  the absence of any subsequent write to those files.
- Per-batch response counts match the expected 10/10/10/10/10/10/12/12/12
  exactly (directly recounted, not merely inferred from prior reports).
- `batch_record.md` hashes were recomputed for all 9 batches; none showed
  any change from the values recorded during this conversation's own
  batch-by-batch verification immediately after each `human_evaluation.md`
  was written.
- No raw response or batch record was found deleted, renamed, or with
  altered content.

## 8. Frozen-input integrity result — **PASS**

- `git status --short` shows only the three pre-existing untracked trees
  (`ai-evaluation/experiment/`, `ai-evaluation/pilot-002/`,
  `ai-evaluation/pilot/`) — unchanged in composition since collection
  completed; no new top-level path appeared or disappeared.
- Because the entire `ai-evaluation/experiment/` tree is untracked, `git
  status`/`git diff` cannot by themselves detect an in-place modification
  to an already-untracked file — this is a real limitation of using Git
  alone here, stated rather than glossed over. The hash comparison in §7
  is what actually establishes byte-for-byte integrity for the manifest,
  rubric, prompts, and all 18 dataset/sanitized fixture files.
- `ai-evaluation/experiment/README.md`, `validation_report.md`, and
  `benchmark/dataset/cases.jsonl` were **not** hash-verified in this audit
  (no baseline hash was recorded for them in `collection_integrity_audit.md`
  or earlier). Their filesystem modification timestamps all predate the
  human-evaluation phase (in the Sep 20 19:29–19:30 range, versus human
  evaluation which ran later), which is corroborating but not
  cryptographic evidence of non-modification — reported here as a
  limitation rather than a verified fact.
- No source code (`credential-scrubber-app`'s engine/rules/CLI) was
  touched — no such path appears anywhere in `git status`, and none was
  opened for writing at any point in this conversation's evaluation or
  audit work.

## 9. Aggregate-statistics guard result — **PASS**

- Searched all 9 `human_evaluation.md` files for `average`, `mean`,
  `median`, `confidence interval`, `significance`, `p-value`,
  `aggregate`, `overall score`, `composite score`, and `paired delta`
  (case-insensitive). Every match found is a **disclaimer**, not a
  computed value — e.g., "No aggregate/composite score computed," "no
  scores are aggregated," "No overall/composite score is produced"
  (quoting or paraphrasing the rubric's own instruction). No numeric
  average, median, delta, confidence interval, or significance result
  was found anywhere in any evaluation file.
- Each batch's "Batch-level observations" section is qualitative prose
  only, with an explicit "no winner is declared" (or equivalent)
  disclaimer in every one of the 9 files.
- No cross-batch summary, tally, or scoreboard file exists anywhere
  under `ai-evaluation/experiment/results/` beyond the 9 individual
  `human_evaluation.md` files themselves.

## Dimension 6 Methodology Resolution

**Status: RESOLVED (2026-09-22).** This section documents the follow-up
work that closed Issue 1 below (originally raised in §4 of this audit).

**Adopted rule:**

> Score "Relationships between values preserved?" ONLY when the specific
> task meaningfully requires the AI to reason about identity,
> association, grouping, or relationships between multiple sensitive
> values. Otherwise mark Dimension 6 as N/A. A file merely containing
> multiple sensitive values is not, by itself, sufficient to make
> Dimension 6 applicable.

Under this rule, Dimension 6 is applicable only to the
`explain_config_relationships` task (the task the dimension exists to
score) — never to `explain_code`, `identify_bug`, `security_analysis`,
`generate_unit_tests`, or `suggest_refactoring`, regardless of how many
sensitive values the candidate file contains.

**Java responses reviewed:** all 10 (`explain_code`, `identify_bug`,
`security_analysis`, `generate_unit_tests`, `suggest_refactoring` × 2
conditions each) — every response in the batch, not only the ones
previously flagged.

**Java Dimension 6 scores changed to N/A:** 8 of 10 —

| Task | Condition | Old Dimension 6 | New Dimension 6 | Why not applicable under the adopted rule |
|---|---|---|---|---|
| `explain_code` | original | 5 | N/A | Task asks for a summary/section breakdown/author questions — no identity, association, grouping, or relationship reasoning is requested. |
| `explain_code` | sanitized | 5 | N/A | Same. |
| `security_analysis` | original | 5 | N/A | Task asks for severity-ranked findings — the response happening to correctly keep secrets distinct is incidental to the task, not requested by it. |
| `security_analysis` | sanitized | 5 | N/A | Same. |
| `generate_unit_tests` | original | 5 | N/A | Task asks for test generation — no relationship reasoning requested. |
| `generate_unit_tests` | sanitized | 5 | N/A | Same. |
| `suggest_refactoring` | original | 5 | N/A | Task asks for a refactor suggestion with before/after code — no relationship reasoning requested. |
| `suggest_refactoring` | sanitized | 5 | N/A | Same. |

**Java Dimension 6 scores left unchanged:** 2 of 10 — `identify_bug`
(original and sanitized), already N/A in the original evaluation. This
was, in fact, the one Java task that had already applied the same
literal "relevant to the task" standard the adopted rule now applies
batch-wide; its original methodology note is preserved (marked
"[Superseded, kept for record]") with a pointer to this resolution, and
a short explanation of why it now reads as consistent rather than as the
batch's outlier.

**How each change was made:** for each of the 8 affected responses, only
the "Relationships between values preserved?" table cell was changed
from `5` to `N/A`. A new paragraph, clearly labeled as a post-audit
methodology normalization with a pointer back to this report, was
inserted directly after each affected score table, explaining that the
response's correct non-merge/non-split handling is preserved as a
qualitative observation but is no longer numerically scored under
Dimension 6. No existing sentence in any Evidence or Failure-modes
paragraph was deleted or reworded. Correctness, Completeness,
Consistency, Usefulness, and Dimension 5 (Misunderstood a sanitized
value?) were verified unchanged for all 10 responses (re-read after
editing and diffed against the pre-edit values recorded earlier in this
audit).

**Later batches checked against the adopted rule:**

- **Python, JavaScript, TypeScript, Go, C#** — re-verified via full-text
  search: Dimension 6 is `N/A` for all 5 tasks × 2 conditions in every
  one of these 5 batches (50 responses total), with no substantive score
  anywhere. Fully consistent with the adopted rule already; **no changes
  made**.
- **JSON (config), YAML (config-yaml), Properties (edge_cases)** —
  re-verified via full-text search: across all 3 batches, the *only*
  responses with a non-N/A Dimension 6 score are the 6
  `explain_config_relationships` responses (2 per batch); all other
  tasks in these 3 batches (`explain_code`, `identify_bug`,
  `security_analysis`, `generate_unit_tests`, `suggest_refactoring` × 2
  conditions each = 30 responses per batch... i.e. 5×2=10 non-relationship
  responses per batch, 30 total across the 3 batches) correctly show
  `N/A`. Fully consistent with the adopted rule already; **no changes
  made**.

**Net effect:** Dimension 6 is now scored (non-N/A) in exactly 6 of the
96 responses experiment-wide — the 6 `explain_config_relationships`
responses (JSON ×2, YAML ×2, Properties ×2) — and is `N/A` everywhere
else, including all 10 Java responses. This is now uniform across all 9
batches with no exceptions.

## 10. Issues requiring manual review

1. **[RESOLVED — see "Dimension 6 Methodology Resolution" above]
   Dimension 6 applicability-rule drift (Java vs. every later batch)** —
   Java previously scored dimension 6 substantively for 4 of 5 tasks
   while every later source-code batch marked it N/A for all 5. Resolved
   by adopting an explicit, task-based applicability rule and normalizing
   Java's 8 affected scores to N/A; the other 8 batches were verified
   already consistent with the rule and required no changes. Dimension 6
   is now applied uniformly across all 96 responses.
2. **Consistency dimension shows zero variance (always 5/5 across all 96
   responses)** — see §4. Not a compliance defect (a rationale
   accompanies every instance), but worth flagging so a future reader
   doesn't mistake this for an unchecked default, and so any future
   evaluation round considers whether the response set or the dimension
   itself needs a harder edge case to be discriminative.
3. **Formatting inconsistency between Java and the other 8 files**
   (vertical vs. horizontal score tables; "Failure modes:" vs.
   "Failure-mode checklist:" heading) — cosmetic only, does not affect
   any score or the mechanical separation of the checklist from numeric
   dimensions, but would need normalizing if the 9 files are ever
   parsed programmatically for aggregate analysis.
4. **No independently-recorded pre-scoring hash baseline exists for the
   96 raw response files as a set**, nor for `README.md`/
   `validation_report.md`/`cases.jsonl` — see §7–§8. Current evidence
   (in-conversation hash matches for 88/96 response files, and absence
   of any write operation for the rest) is strong but not a complete,
   independently-original cryptographic chain for every file. If
   airtight tamper-evidence is required going forward, a persisted
   hash manifest taken immediately after collection (before scoring)
   would have closed this gap; it wasn't taken for the raw responses at
   that time.

## 11. Final audit status

**PASS WITH DOCUMENTED ISSUES**

All 96 responses are completely and correctly evaluated against the
frozen rubric with no missing, duplicate, or out-of-range scores; all 12
intentionally-N/A cells are correctly accounted for; the failure-mode
checklist is kept mechanically separate from numeric scoring throughout;
every documented environmental deviation was found, correctly excluded
from scoring credit, and is fully inventoried above; every frozen input
this audit could hash-verify is byte-identical to its pre-evaluation
baseline; and no aggregate statistic has been calculated anywhere in the
evaluation files. Issue 1 (Dimension 6 applicability drift) has since
been **resolved** via the methodology normalization documented above —
Dimension 6 is now applied uniformly across all 96 responses under a
single, explicit, task-based rule. The status remains "PASS WITH
DOCUMENTED ISSUES" rather than a clean PASS only because of the three
*remaining* items in §10 (items 2–4) — none of which indicates
tampering, a scoring error, or a rubric violation, but each of which is
a real methodological detail (a zero-variance dimension, a formatting
inconsistency, and one incomplete hash-baseline chain) that a careful
reader or a future aggregate-analysis pass should know about rather than
discover independently.
