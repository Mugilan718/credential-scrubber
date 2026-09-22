# Human evaluation — Pilot 002 (config/appsettings.json × explain_config_relationships)

**Status: provisional, single-pilot record.** One file, one task, one
model, one response per condition. This is not a general claim about the
Credential Scrubber system, not a statistically powered result, and not
proof that AI usefulness survives sanitization in general — see
[§E. Limitations](#e-limitations).

## Experiment metadata

| Field | Value |
|---|---|
| File | `config/appsettings.json` |
| Task | `explain_config_relationships` (`ai-evaluation/prompts/explain_config_relationships.md`, used verbatim) |
| Model | Claude Sonnet 5 (`claude-sonnet-5`) |
| Conditions | Original vs. sanitized |
| Responses scored | One per condition (no repeated sampling) |
| Rubric | `ai-evaluation/rubric/rubric.md` — used exactly as written; no new dimensions added |
| Original source | `ai-evaluation/pilot-002/original/config/appsettings.json` |
| Sanitized source | `ai-evaluation/pilot-002/sanitized/config/appsettings.json` |
| Original response | `ai-evaluation/pilot-002/results/original_explain_config_relationships.txt` (unedited) |
| Sanitized response | `ai-evaluation/pilot-002/results/sanitized_explain_config_relationships.txt` (unedited) |
| Execution record | `ai-evaluation/pilot-002/results/README.md` (model/settings/independence confirmation) |
| Rater | Single human evaluator (this record), scores provisional |

## Original condition

**Input:** the unmodified `appsettings.json` fixture — `AppName`,
`Environment`, `Port` as flat top-level values; a nested `Logging.Level`;
a nested `Database` object containing `Host`, `Username`, and `Password`;
a top-level `ApiKey`; and a top-level `CustomerId`, all with their real
(synthetic-fake) literal values.

**Response summary (factual, not evaluative):** the response organized
the file into five groups — app runtime (`AppName`/`Environment`/`Port`),
database credentials (`Database.Host`/`Username`/`Password`), logging
(`Logging.Level`), and two standalone values (`ApiKey`, `CustomerId`) —
with a stated rationale for each grouping and a closing numbered summary.
Full text: `original_explain_config_relationships.txt`.

## Sanitized condition

**Input:** the same file with `placeholder_mode=True` engine output —
`Database.Host` → `<URL_1>`, `Database.Password` → `<PASSWORD_1>`,
`ApiKey` → `<API_KEY_1>`; `Database.Username`, `CustomerId`, and all
other fields unchanged (`Database.Username` because it isn't detected as
sensitive, `CustomerId` because no detection rule exists for it — see
[§D](#d-automated-benchmark--security-results)).

**Response summary (factual, not evaluative):** the response organized
the file into six groups — application identity
(`AppName`/`Environment`), network/runtime binding (`Port`), logging
(`Logging.Level`), database connection
(`Database.Host`/`Username`/`Password`), an external API credential
(`ApiKey`), and a customer/tenant identifier (`CustomerId`) — plus a
closing structural summary. Full text:
`sanitized_explain_config_relationships.txt`.

## A. Formal rubric scores

Exactly `rubric.md`'s six named dimensions, no relabeling and no new
dimensions added.

| # | Rubric dimension | Original | Sanitized |
|---|---|---:|---:|
| 1 | Correctness | 4 | 4 |
| 2 | Completeness | 5 | 5 |
| 3 | Consistency | 5 | 5 |
| 4 | Usefulness | 5 | 5 |
| 5 | Misunderstood a sanitized value? | N/A | 5 |
| 6 | Relationships between values preserved? | 5 | 5 |

### 1. Correctness — 4 / 4
*Rubric 4 = "Accurate overall; one minor inaccuracy that doesn't affect the main point."*

Both responses correctly identify the major configuration relationships
and groups. Both also contain minor speculative interpretations that go
beyond what the JSON itself establishes:

- **Original:** *"likely credentials for an outbound third-party API
  integration"* (`ApiKey`) and *"looks like a tenant/customer identifier
  for multi-tenant deployments or license tracking"* (`CustomerId`) — the
  file gives no evidence of "third-party," "multi-tenant," or "license"
  specifically; these are plausible but unverified inferences.
- **Sanitized:** *"ambiguous which external service it authenticates
  to... likely worth nesting under a service-specific block"* (`ApiKey`)
  and *"likely used for multi-tenant identification, billing, or
  licensing"* (`CustomerId`) — the same category of unverified inference,
  present in this condition too.

Neither response states anything the file actually contradicts, and the
speculation doesn't affect the main groupings, which are correct — hence
4/5 rather than 5/5 for both, not a difference between conditions.

### 2. Completeness — 5 / 5
*Rubric 5 = "Fully addresses every part of the task's requested structure"* (a short list of groups, each with member settings + rationale, and ungrouped settings listed separately).

Both responses cover all nine leaf/parent values present in the file —
`AppName`, `Environment`, `Port`, `Logging.Level`, `Database.Host`,
`Database.Username`, `Database.Password`, `ApiKey`, `CustomerId` — with a
stated rationale per group and explicit "stands alone" treatment for
values that don't belong to a group, exactly as the template's
instruction ("If a setting doesn't seem to belong to any group, list it
separately") asks for.

### 3. Consistency — 5 / 5
*Rubric 5 = "Fully internally consistent."* Strictly: does the response
contradict itself, or does its stated confidence not match what it
demonstrates — nothing broader (not "semantic understanding," not
original-vs-sanitized agreement, per the rubric's own definition).

Both responses are internally coherent throughout — no statement in
either response is contradicted by a later statement, and each response's
hedged language ("likely," "ambiguous," "appears to") matches the actual
certainty its reasoning demonstrates. No internal contradiction found in
either condition.

### 4. Usefulness — 5 / 5
*Rubric 5 = "Directly actionable; a developer could act on it with no further digging."*

Both responses give a developer an accurate, structured map of which
settings belong together and why, including a concrete, actionable
observation in the sanitized response about `ApiKey`'s missing
namespace ("worth nesting under a service-specific block"). No
usefulness gap between conditions for this task.

### 5. Misunderstood a sanitized value? — N/A / 5
*Rubric: "Specific to responses on the sanitized condition (mark N/A for original-condition responses)."*

- **Original: N/A.** No placeholder is present in the original condition
  for the response to misunderstand.
- **Sanitized (5):** the response correctly derived the role of every
  sanitized value from its key name and structural context alone — e.g.
  it describes `Database.Host`/`Database.Password` as *"an endpoint plus
  credentials to authenticate against it"* and `ApiKey` as *"conceptually
  similar to `Database.Password` (a secret)"* — without needing, or
  appearing to need, the real literal values to explain the
  configuration. It never treated a placeholder token as a real, working
  value, never flagged a placeholder itself as a security issue, and
  never reused placeholder text as if it were literal data. No sign of
  misunderstanding.

### 6. Relationships between values preserved? — 5 / 5
*Rubric 5 = "All same/different relationships correctly reflected."*

Both responses correctly preserve the file's one genuine grouping
relationship — `Database.Host` + `Database.Username` + `Database.Password`
as a single database connection/credential group (*"these three only make
sense together"* / *"meaningless without each other"*) — and correctly
keep it distinct from `Logging.Level` and from the independent top-level
values (`AppName`, `Environment`, `Port`, `ApiKey`, `CustomerId`). No
false merge (no two independent values treated as related) and no false
split (the Database trio is never fragmented) in either condition. This
is the most direct test this pilot has of the research question's
grouping-preservation claim, and it held identically in both conditions.

## B. Failure-mode checklist

| Failure mode | Original | Sanitized |
|---|---|---|
| False negative (a real issue present in the original that sanitization/response handling missed) | No | No |
| Partial sanitization (secret fragment survives) | No | No |
| Placeholder correlation failure (same value given different tokens, or vice versa) | N/A | No |
| Over-specific placeholder interpretation | N/A | Yes — minor |
| Misunderstood sanitized value (treated as real/working, or flagged as itself a vulnerability) | N/A | No |
| Lost structural relationship (Database grouping broken or misattributed) | No | No |
| Reconstructed original secret | No | No |

**Over-specific interpretation, detailed:** the sanitized response
characterizes `ApiKey` as authenticating to an "external service" /
"third-party" context and speculates it should be nested under a
service-specific block. The key name (`ApiKey`) supports that it *is* an
API key; the JSON alone does not establish that it belongs to a
third-party (as opposed to first-party/internal) service. The response
also describes `CustomerId` as plausibly for "multi-tenant
identification, billing, or licensing" — again a reasonable but
unverified inference from the key name alone. **Both are treated as
minor inference limitations, not sanitization failures** — the
*original*-condition response makes essentially the same category of
speculative inference about both of these same two values (see
[§A.1](#1-correctness--4--4)), so this pattern is not attributable to
sanitization; it reflects how the model reasons about ambiguous key names
in general, with or without placeholders present.

## C. Qualitative observations

- **The sanitized response derived structural and semantic meaning from
  key names and JSON nesting alone**, with no access to any real literal
  value — e.g., correctly inferring that `Database.Host` /
  `Database.Password` form a connection/credential pair purely from their
  shared parent object and their key names, not from the (absent) real
  hostname or password text.
- **The sanitized response's grouping decisions were structurally
  identical to the original response's**, down to which values it
  treated as standalone (`ApiKey`, `CustomerId`) versus grouped
  (`Database.*`, `Logging.Level`). The two responses organize the
  material slightly differently (five groups vs. six — the sanitized
  response splits `Port` out from the app-identity group; the original
  keeps it merged with `AppName`/`Environment`) but arrive at the same
  underlying relationships.
- **The over-specific `ApiKey`/`CustomerId` interpretations appear in
  both conditions**, not only the sanitized one — this is evidence that
  the pattern originates from the ambiguity of the key names themselves,
  not from the presence of a placeholder. This is a different observation
  from Pilot 001, where the analogous over-specific-inference pattern
  (e.g. "OAuth-style client secret") was specific to the sanitized
  condition only, since Pilot 001's original condition never needed to
  speculate — it could describe the (fake) literal values directly.

## D. Automated benchmark / security results

Not rubric-scored — these are facts already established by the engine
and the existing benchmark/pilot-preparation tooling at Pilot 002's
preparation step (`ai-evaluation/pilot-002/metadata.json`), cited here,
not re-verified by running anything as part of this evaluation record.
Kept explicitly separate from the human-rated scores above, per the
distinction `ai-evaluation/README.md` draws between automated
sanitization/detection validation and human-rated task usefulness.

- **Detection/leakage (automated, already measured):** three true
  positives matched to `benchmark/dataset/cases.jsonl` ground truth
  (`Database.Host` → `URL`, `Database.Password` → `PASSWORD`, `ApiKey` →
  `API_KEY`); no original secret value found anywhere in the sanitized
  output; MASK-mode and placeholder-mode detection shape identical;
  placeholder-mode scan deterministic across two runs.
- **Structural/syntax preservation (automated + manual diff, already
  measured):** sanitized JSON parses successfully via the real parser
  (`json.loads`); line count preserved (15 → 15); `Database.Host` and
  `Database.Password` confirmed still nested inside the same `Database`
  object as `Database.Username` after sanitization.
- **`CustomerId` gap (documented, pre-existing):** `"CustomerId":
  "PF001"` is unchanged in both conditions — not a leak, but the known,
  intentional absence of a customer/user-identifier detection rule (see
  `BENCHMARK.md` Limitations). Both AI responses' speculation about
  `CustomerId`'s purpose is therefore based on the *real* value in both
  conditions, not a placeholder — worth noting when reading
  [§A.1](#1-correctness--4--4) and [§B](#b-failure-mode-checklist)'s
  `CustomerId` observations, since this value was never actually
  sanitized in either condition.

## E. Limitations

- **Sample size: one file, one task, one model, one run per condition.**
  These scores describe this single `(file, task)` pair only. They are
  not a benchmark result, not a claim about Credential Scrubber's
  placeholder scheme in general, and not evidence about any other file,
  task, or model. No statistical significance is claimed or computable
  from n=1.
- **`CustomerId` was not actually sanitized in this pilot** (see
  [§D](#d-automated-benchmark--security-results)) — both conditions saw
  the real value `"PF001"`, so this pilot does not test placeholder
  handling for that specific field, only for `Database.Host`,
  `Database.Password`, and `ApiKey`.
- **Residual synthetic signals remain in the original condition**
  (`"AppName": "BenchmarkDemo"`, `fake-`-prefixed values) — documented
  before this evaluation ran, in `ai-evaluation/pilot-002/README.md`.
- **Single human rater, provisional scores.** No second rater, no
  inter-rater agreement measure, and no blind-rating separation were
  applied here (the evaluator saw both condition labels while scoring).
- **Procedural caveats carried over from response collection**, unchanged
  by this record (full detail in
  `ai-evaluation/pilot-002/results/README.md`): temperature and
  max-output-tokens were not independently controllable through the
  tooling used to collect these two responses, and the "AI agent" used
  was a Claude Code subagent rather than a bare model API call. Both
  applied identically to both conditions; both invocations used zero
  tool calls, confirming no repository or cross-condition access
  occurred.
- **This record does not establish a "winner."** Scores are identical or
  N/A-vs-5 across every dimension in this pilot; no ranking, overall
  score, or composite comparison is computed or implied anywhere in this
  document, per `rubric.md`'s own instruction to keep dimensions
  separate.

## Conclusion

Pilot 002 provides evidence that, on this one file and task, the
sanitized configuration retained enough structural and semantic
information for the model to correctly explain the file's important
relationships — in particular, the `Database.Host` /
`Database.Username` / `Database.Password` connection-credential grouping
— without access to the original sensitive literal values. The
sanitized-condition response derived this understanding entirely from
key names and JSON nesting, showed no sign of treating a placeholder as
a real value, and reached the same underlying groupings as the
original-condition response. This is a **single-file, single-task,
single-run pilot** and therefore does not establish general performance,
does not carry statistical significance, and is not evidence about any
other file, config shape, or task — it is one data point supporting
continued use of this experimental procedure at scale, not a conclusion
about the Credential Scrubber system as a whole.
