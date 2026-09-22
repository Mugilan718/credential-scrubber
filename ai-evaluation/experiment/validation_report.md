# Experiment validation report

Validates all 9 frozen candidate files against the current, unmodified
Credential Scrubber engine (commit `c291785`). Every check below was
produced by actually running `engine.scan_project()` — via
`benchmark/dataset_loader.FILES_DIR`, the real dataset directory — in
both `placeholder_mode=False` and `placeholder_mode=True`, plus a
second `placeholder_mode=True` run for determinism, all writing to
throwaway temp directories. **No file under `benchmark/dataset/` was
modified.** No detection rule, engine code, rubric, or results-template
file was changed to produce these results.

Note on this report's scan scope vs. the actual experiment's: for
efficiency, this validation scanned the *entire* `benchmark/dataset/files/`
tree in one pass (16 files, not just the 9 candidates), which is why the
placeholder ordinals shown below (e.g. `<ACCESS_TOKEN_7>`) are
cross-file-shared rather than starting at 1 per file. This is a property
of validating at whole-dataset scope, not a property of any individual
file. When sanitized fixtures are actually generated for the experiment,
each file will be scanned in isolation (one file per scan, matching
Pilot 001/Pilot 002's precedent — see `manifest.json`'s
`sanitized_fixture_generation_method`), giving each file clean,
self-contained `<CATEGORY_1>`-style numbering. The **categories**
assigned below (e.g. `GENERIC_SECRET` vs. `API_KEY`) are scan-scope
independent and will be identical whichever way the file is scanned.

## 1. `java/Config.java`

| | |
|---|---|
| Type/language | Java (`.java`) |
| Ground-truth true positives | 6 (`api_key`, `password`, `client_secret`, 3× `multiline_secret` fragments of one value) |
| Engine-detected entries | 6 — matches ground truth exactly |
| Sanitization validation | No leaked original value in sanitized output |
| Syntax validation | `heuristic_valid` (original and sanitized) — Java has no stdlib parser (`BENCHMARK.md` documented limitation) |
| Determinism | Identical output across two `placeholder_mode=True` runs |
| Categories assigned | `apiKey` → `GENERIC_SECRET`, `dbPassword` → `PASSWORD`, `clientSecret` → `GENERIC_SECRET`, `authToken` (multiline) → `ACCESS_TOKEN` |
| Known limitation | `apiKey` and `clientSecret` resolve to the generic `GENERIC_SECRET` category rather than `API_KEY`, a pre-existing, documented engine behavior (see `BENCHMARK.md` Limitations and Pilot 001's record) — a regex-backtracking artifact specific to the **single-line source-code `code_variable_pattern` detection path**, where the "key" alternative is reached before the more specific "apikey"/"api_key" alternative. Not modified here. |
| Task applicability | All 6 tasks applicable |

## 2. `python/config.py`

| | |
|---|---|
| Type/language | Python (`.py`) |
| Ground-truth true positives | 5 (`password` via `os.getenv`, `api_key`, 3× `multiline_secret` fragments) |
| Engine-detected entries | 5 — matches ground truth exactly |
| Sanitization validation | No leaked original value |
| Syntax validation | `valid` (real parser — `compile()`), both conditions |
| Determinism | Identical across two runs |
| Categories assigned | `DB_PASSWORD` (via `os.getenv`) → `PASSWORD`, `api_key` → `GENERIC_SECRET`, `API_SECRET` (multiline) → `GENERIC_SECRET` |
| Known limitation | `api_key` (snake_case, not camelCase) **also** resolves to `GENERIC_SECRET` rather than `API_KEY` — confirms this validation's finding that the category-imprecision limitation is **not** camelCase-specific (as Pilot 001 alone might have suggested); it is a general property of the single-line code-identifier detection path whenever a shorter alternative ("key") is reachable by regex backtracking before a longer, more specific one. Not modified here. |
| Task applicability | All 6 tasks applicable |

## 3. `javascript/config.js`

| | |
|---|---|
| Type/language | JavaScript (`.js`) |
| Ground-truth true positives | 5 (`access_token`, `webhook_secret`, 3× `multiline_secret` fragments) |
| Engine-detected entries | 5 — matches ground truth exactly |
| Sanitization validation | No leaked original value |
| Syntax validation | `heuristic_valid` (no stdlib parser for JS) |
| Determinism | Identical across two runs |
| Categories assigned | `apiToken` → `ACCESS_TOKEN`, `webhookSecret` → `GENERIC_SECRET`, `secretKey` (multiline) → `GENERIC_SECRET` |
| Known limitation | None specific to this file — `GENERIC_SECRET` is the *intended*, correct category here (both names are rooted in "secret", not "key" being shadowed by a more-specific alternative), unlike files 1/2/5 below. |
| Task applicability | All 6 tasks applicable |

## 4. `typescript/auth.ts`

| | |
|---|---|
| Type/language | TypeScript (`.ts`) |
| Ground-truth true positives | 3 (`access_token`, `client_secret` [typed declaration], `bearer_token` [value-pattern match, not key-name match]) |
| Engine-detected entries | 3 — matches ground truth exactly |
| Sanitization validation | No leaked original value |
| Syntax validation | `heuristic_valid` (no stdlib parser for TS) |
| Determinism | Identical across two runs |
| Categories assigned | `authToken` → `ACCESS_TOKEN`, `secretKey` → `GENERIC_SECRET` (correct — "secret"-rooted), `bearerHeader` (value-pattern match) → `ACCESS_TOKEN` |
| Known limitation | None specific to this file. Notable as the only candidate exercising the **value-pattern** detection path (not a key-name match) among the 6 code files. |
| Task applicability | All 6 tasks applicable |

## 5. `go/config.go`

| | |
|---|---|
| Type/language | Go (`.go`) |
| Ground-truth true positives | 2 (`api_key`, `access_token`) |
| Engine-detected entries | 2 — matches ground truth exactly |
| Sanitization validation | No leaked original value |
| Syntax validation | `heuristic_valid` (no stdlib parser for Go) |
| Determinism | Identical across two runs |
| Categories assigned | `apiKey` → `GENERIC_SECRET`, `accessToken` → `ACCESS_TOKEN` |
| Known limitation | Same `apiKey` → `GENERIC_SECRET` category-imprecision as files 1 and 2 (single-line code-identifier path). Not modified here. |
| Task applicability | All 6 tasks applicable |

## 6. `csharp/Config.cs`

| | |
|---|---|
| Type/language | C# (`.cs`) |
| Ground-truth true positives | 4 (`access_token`, 3× `multiline_secret` fragments of `client_secret`) |
| Engine-detected entries | 4 — matches ground truth exactly |
| Sanitization validation | No leaked original value |
| Syntax validation | `heuristic_valid` (no stdlib parser for C#) |
| Determinism | Identical across two runs |
| Categories assigned | `sessionToken` → `ACCESS_TOKEN`, `clientSecret` (multiline) → **`API_KEY`** |
| Known limitation | None — and notably, `clientSecret` here correctly resolves to `API_KEY`, *not* `GENERIC_SECRET`, because the **multiline** detection path (`scan_multiline_plus` → `_multiline_category` → `_most_specific_category`) checks the identifier against every matching `key_pattern`, the same reconciliation logic the config-key path uses — unlike the single-line `code_variable_pattern` path (files 1/2/5), which only ever captures one keyword via regex backtracking. This is a precise, useful confirmation of the category-imprecision bug's exact scope: it affects single-line source-code assignments specifically, not multiline concatenations. |
| Task applicability | All 6 tasks applicable |

## 7. `config/appsettings.json`

| | |
|---|---|
| Type/language | JSON config (`.json`) |
| Ground-truth true positives | 3 (`internal_url`/`Database.Host`, `password`/`Database.Password`, `api_key`/`ApiKey`) |
| Engine-detected entries | 3 — matches ground truth exactly |
| Sanitization validation | No leaked original value; `CustomerId`/`"PF001"` confirmed unchanged (documented detection gap, not a leak) |
| Syntax validation | `valid` (real parser — `json.loads`), both conditions |
| Determinism | Identical across two runs |
| Categories assigned | `Database.Host` → `URL`, `Database.Password` → `PASSWORD`, `ApiKey` → `API_KEY` — all three distinct and specific |
| Known limitation | `CustomerId`/`customer_id` detection gap (documented, pre-existing — `BENCHMARK.md` Limitations); no category-imprecision issue on this file (config-key path correctly reconciles). |
| Task applicability | All 6 tasks applicable (config file — in scope for `explain_config_relationships`) |

## 8. `config/settings.yaml`

| | |
|---|---|
| Type/language | YAML config (`.yaml`) |
| Ground-truth true positives | 3 (`internal_url`, `encryption_key`, `session_key` [documented to bypass the placeholder allow-list]) |
| Engine-detected entries | 3 — matches ground truth exactly |
| Sanitization validation | No leaked original value |
| Syntax validation | `valid` (real parser — `pyyaml.safe_load`), both conditions |
| Determinism | Identical across two runs |
| Categories assigned | `endpoint` → `URL`, `encryption_key` → `PRIVATE_KEY`, `session_key` → `GENERIC_SECRET` (correct/intended per `KEY_PATTERN_CATEGORY`, not a collapse) |
| Known limitation | None specific to this file — all three categories are correct and specific. |
| Task applicability | All 6 tasks applicable (config file — in scope for `explain_config_relationships`) |

## 9. `edge_cases/false_positives.properties`

| | |
|---|---|
| Type/language | `.properties` config — **negative control** |
| Ground-truth true positives | 0 (by design — every value is deliberately non-sensitive, several containing suspicious *substrings* like `ghost_writer`, `tokenizer_version`, `authored_by` that must NOT trigger detection) |
| Engine-detected entries | 0 — matches ground truth exactly (no false positives fired) |
| Sanitization validation | Trivially clean — nothing is redacted; original and sanitized output are byte-identical |
| Syntax validation | `not_applicable` — `.properties` has no syntax to violate (per `benchmark/syntax_check.py`) |
| Determinism | Identical across two runs |
| Categories assigned | None (no findings) |
| Known limitation | None — this file exists specifically to test false-positive avoidance, and does so cleanly. |
| Task applicability | All 6 tasks applicable, including `explain_config_relationships` (in scope, `.properties`) — expected to yield a low-relationship-density response since the file is flat with no grouping structure at all, which is itself a meaningful negative-control observation for that task, not a reason to mark it N/A. |

## Totals

| Check | Result |
|---|---|
| Files confirmed to exist in `benchmark/dataset/files/` | 9 / 9 |
| Files confirmed part of `benchmark/dataset/cases.jsonl` ground truth | 9 / 9 |
| Files with detection shape identical between MASK and placeholder mode | 9 / 9 |
| Files with zero leaked original values in sanitized output | 9 / 9 |
| Files passing syntax validation (real parser, heuristic, or not-applicable as appropriate) in both conditions | 9 / 9 |
| Files with deterministic placeholder-mode output across two runs | 9 / 9 |
| Total ground-truth true positives across all 9 files | 31 (6+5+5+3+2+4+3+3+0) |
| Total engine-detected entries across all 9 files | 31 — exact match |
| Files with a known category-imprecision limitation (documented, not fixed) | 3 (`java/Config.java`, `python/config.py`, `go/config.go`) |
| Files with a known detection gap (documented, not fixed) | 1 (`config/appsettings.json` — `CustomerId`) |
| Files requiring no changes to pass validation | 9 / 9 |
| Engine/rules/dataset files modified to produce this report | 0 |
