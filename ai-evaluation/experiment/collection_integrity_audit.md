# Collection Integrity Audit

**Scope:** `ai-evaluation/experiment/` — the frozen 9-file × applicable-task × 2-condition AI evaluation collection (Batches 1–9). Read-only audit; this report is the only file created or modified during this task.

## Status

**PASS WITH DOCUMENTED DEVIATIONS**

All 96 expected responses exist, are non-empty, map to the correct task/condition, and use distinct session identifiers. No engine, rules, dataset, prompt, rubric, manifest, or fixture file was modified during collection. All previously-documented protocol deviations are confirmed present and correctly recorded. Two additional low-confidence, likely-generic observations were found during this audit's keyword sweep and are reported below as **Previously undocumented observations** (not counted as confirmed leakage). One known, already-documented engine behavior (CRLF conversion) explains the only hash mismatch found; it does not affect content.

## Response coverage

| Candidate | Expected | Actual | Status |
|---|---:|---:|---|
| Java | 10 | 10 | PASS |
| Python | 10 | 10 | PASS |
| JavaScript | 10 | 10 | PASS |
| TypeScript | 10 | 10 | PASS |
| Go | 10 | 10 | PASS |
| C# | 10 | 10 | PASS |
| config/appsettings.json | 12 | 12 | PASS |
| config/settings.yaml | 12 | 12 | PASS |
| edge_cases/false_positives.properties | 12 | 12 | PASS |
| **Total** | **96** | **96** | **PASS** |

Verification method: for every candidate × applicable task × condition, confirmed `original.txt`/`sanitized.txt` exists, is non-empty (min size 745 bytes, max 5,217 bytes, mean ≈2,101 bytes — no file near-zero or suspiciously truncated), and sits under the correct `results/<candidate>/<task>/` path. No unexpected files (extra task directories, stray files, or non-`.txt` artifacts) were found anywhere under `ai-evaluation/experiment/results/`.

## Manifest applicability

Read directly from `ai-evaluation/experiment/manifest.json` (`task_applicability_matrix`), unmodified throughout collection:

| Task | java | python | javascript | typescript | go | csharp | config/appsettings.json | config/settings.yaml | edge_cases/false_positives.properties |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| explain_code | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| identify_bug | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| security_analysis | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| generate_unit_tests | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| suggest_refactoring | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| explain_config_relationships | N/A | N/A | N/A | N/A | N/A | N/A | ✓ | ✓ | ✓ |

N/A reason (verbatim from manifest, all 6 source-code files): *"out of the template's documented scope (source code, not a config file)"*.

**Calculation:** 9 files × 6 tasks × 2 conditions = 108 nominal cells. `explain_config_relationships` is `not_applicable` for the 6 source-code files → 6 file/task cells × 2 conditions = 12 excluded. **108 − 12 = 96**, matching `manifest.json`'s own `applicable_response_count.applicable_cells: 96` field exactly.

## Batch metadata

| Batch | Model recorded | Execution date recorded | Session IDs recorded | Deviations section present | Explicit "Expected response count" heading |
|---|:---:|:---:|:---:|:---:|:---:|
| Java | ✓ | ✓ | ✓ (10) | ✓ | Absent (stated only in the completion-report chat turn, not as its own heading in `batch_record.md`) |
| Python | ✓ | ✓ | ✓ (10) | ✓ | Absent (same as above) |
| JavaScript | ✓ | ✓ | ✓ (10) | ✓ | Absent (same as above) |
| TypeScript | ✓ | ✓ | ✓ (10) | ✓ | Absent (same as above) |
| Go | ✓ | ✓ | ✓ (10) | ✓ | Absent (same as above) |
| C# | ✓ | ✓ | ✓ (10) | ✓ | Absent (same as above) |
| config/appsettings.json | ✓ | ✓ | ✓ (12) | ✓ | Absent as a heading, but expected/actual counts (12) stated in prose under "Methodological problem..." section |
| config/settings.yaml | ✓ | ✓ | ✓ (12) | ✓ | Present (`## Expected response count`) |
| edge_cases/false_positives.properties | ✓ | ✓ | ✓ (12) | ✓ | Present (`## Expected response count`) |

**Missing metadata fields found:** none of the 9 batch records omit model identifier, execution date, session IDs, per-response task/condition/status, result paths, or a deviations section — all are present in every batch record. The one consistent gap: batches 1–6 (java through csharp) do not carry a dedicated `## Expected response count` heading inside `batch_record.md` itself (the count is only in the conversation turn's completion report, not persisted in the file); batches 7–9 do, once the manifest-verification-first protocol was introduced. This is a minor, cosmetic completeness gap, not a data-integrity issue — actual vs. expected counts are independently verifiable either way via the Responses table row count.

## Protocol deviations

### Confirmed / high-confidence environmental leakage

| # | Batch | Task/Condition | Quote (verbatim) | Confidence |
|---|---|---|---|---|
| 1 | Python (Batch 2) | `explain_code` / original | "...matching the working directory name `New-credential-scrubber`..." | High — exact project-directory-name match |
| 2 | Go (Batch 5) | `explain_code` / original | "...matching the 'New-credential-scrubber' project this lives in..." | High — exact match |
| 3 | YAML (Batch 8) | `explain_code` / original | "...and its context (directory `New-credential-scrubber`)..." | High — exact match |
| 4 | Properties (Batch 9) | `generate_unit_tests` / original | "...its context (directory `New-credential-scrubber`) strongly suggest..." | High — exact match |
| 5 | Properties (Batch 9) | `generate_unit_tests` / sanitized | "...given the 'New-credential-scrubber' project context..." **and** "...the directory it lives in under `D:\New-credential-scrubber`" | High — exact project name **and** full absolute path (most severe instance in the collection) |

All 5 are verified present verbatim in both the raw response `.txt` files and their respective `batch_record.md` entries; none were edited or the responses re-run. This audit's independent keyword sweep of all 96 raw responses found no additional instance of the literal strings `New-credential-scrubber` or `D:\New-credential-scrubber` beyond these 5.

### Ambiguous observation (previously documented)

| # | Batch | Task/Condition | Quote | Assessment |
|---|---|---|---|---|
| 6 | TypeScript (Batch 4) | `security_analysis` / original | "...if this file is part of a `website` project..." | Ambiguous — plausible generic security-review phrasing; this session's actual working directory ends in `\website`, but the word alone is not distinctive enough to confirm leakage. Documented as ambiguous in Batch 4's own record; this audit does not upgrade or downgrade that assessment. |

### Previously undocumented observations (found during this audit's keyword sweep — low confidence, not counted as confirmed leakage)

| # | Batch | Task/Condition | Quote | Assessment |
|---|---|---|---|---|
| 7 | C# (Batch 6) | `explain_code` / sanitized | "...testing a secret scanner or credential-scrubber tool" | Not previously flagged in Batch 6's `batch_record.md` (which stated "no deviations detected"). Lowercase, generic compound phrase ("credential-scrubber tool") describing a *category* of tool, not the proper-noun project name "Credential Scrubber" or the directory name "New-credential-scrubber". Directly explicable from the file's own content (fake credentials + "benchmark fixture" comment) without any environment awareness. Assessed as **likely generic/coincidental, not confirmed leakage** — reported for completeness per this audit's instructions, not reinterpreted or removed from the response. |
| 8 | Properties (Batch 9) | `explain_code` / sanitized | "...a synthetic fixture for benchmarking a secret/credential scrubber" | Same pattern as #7 — lowercase, generic, content-grounded phrasing. Not previously flagged in Batch 9's record (which documented two *different* deviations in `generate_unit_tests`, not this one in `explain_code`). Assessed as **likely generic/coincidental, not confirmed leakage**. |

No other instance of the audit's keyword list (`sanitiz*`, `placeholder`, `working director*`, `the experiment`, `original condition`, `sanitized condition`, `other condition`) surfaced content beyond what prior batch records already characterized as expected, content-grounded reasoning (e.g., models correctly identifying `<CATEGORY_N>`-shaped tokens as placeholders/redacted values from the visible text alone — anticipated and explicitly not treated as a deviation per each batch's own instructions).

**Both raw responses in items 7 and 8 remain unedited**; this audit did not modify them or their batch records.

## Frozen input hashes

### Original candidates (`benchmark/dataset/files/`)

| File | SHA-256 |
|---|---|
| java/Config.java | `da98b0e281af40fc98a3d7158e6fba01e4b81fcd43f547136c32adcabd4f74bc` |
| python/config.py | `1b26c8a090997033592820dd84df529ca961a83a97d102b25026eaac3dd8c711` |
| javascript/config.js | `2a6adc0648ff8731d9fa4ed3bcd7d106fc6b9c49f85e94b1a85aef3fbfd2dfd3` |
| typescript/auth.ts | `2c464ff1814f75c0f698d9945d72c95783fa852f9a12f31c2c22e1a4ced7a27c` |
| go/config.go | `f85606c83e2f6679e2a722d99e7809837c639a7651e81df88a4382e59b359f20` |
| csharp/Config.cs | `09c33e045bf36eba36f253dd897726eb72f543cd137078c7ad6fc54cb93a6fc6` |
| config/appsettings.json | `265a85ee89ecfe3bd9ae8e699eb88bc95c1420028fd4ff3289f7ce662c803aff` |
| config/settings.yaml | `fda6042eea582ab6166e64a3d35e451bee0634043d9426fd1d99037b5c19bb81` |
| edge_cases/false_positives.properties | `134dc4ff010319a5d5c3d5160761bc90d11a750d6802bbbd8faaee9daaa475d1` |

### Sanitized candidates (`ai-evaluation/experiment/sanitized/`)

| File | SHA-256 |
|---|---|
| java/Config.java | `6df846a97ec52d11aa2d0e33461ca381cae7d2e853159f24377319f040d57524` |
| python/config.py | `3e90fbbd4df7c5986156236c0ede297d1fb81a2473f6080482bb89aae29a2915` |
| javascript/config.js | `90b6539bf72619a856fc0b7818c330c6c422fa83d2831395d3bfe6e51ede425b` |
| typescript/auth.ts | `166361a343f50cbd2ebe0accc4c9c27967a7046bc86918add63328d9ae34e9db` |
| go/config.go | `9a7c7ddab29148f45235ae41d90a58966eeb2ad3a0072e522146953490a7feba` |
| csharp/Config.cs | `733112b479b1b9d94b345bef285780b437050b2a26d0e0d6fe8391af63acfc9e` |
| config/appsettings.json | `ce773c9210768781234ac1ec4cf6d8b5a6505a6edf881b995fecd504bc4c2335` |
| config/settings.yaml | `a6c36245787a2b8cda94a0424c292fdc060c768b0f52b24f62f9dbe7e8d8aad7` |
| edge_cases/false_positives.properties | `1b80502fc81287365e420dd30f1c1d3db921e8f2c5a2a680efb837db6cda5b67` |

### Methodology inputs

| Input | SHA-256 |
|---|---|
| ai-evaluation/experiment/manifest.json | `28d0730acc5cff4df8d94ce109d6aa89aa3de35a3d6ccc86ea91432e63fad754` |
| ai-evaluation/rubric/rubric.md | `6041deb2aa48daae9b1972fcdbd32b18dcad24d908141d9cf1699c7438cd7ec9` |
| ai-evaluation/prompts/explain_code.md | `8efa5784619c4ff77b15f0983bf88588c090506afe71e0293b7e4bb220b72271` |
| ai-evaluation/prompts/identify_bug.md | `3a7e7be2d4c6a0af776acc1f9a507a562014c61b45b2cbb788c9203d8e9ec601` |
| ai-evaluation/prompts/security_analysis.md | `87cf437fe668c439835909f8105cc284f297e80fe1a5532520323d499549c643` |
| ai-evaluation/prompts/generate_unit_tests.md | `eb61c40bb00a4ca3c4290088b176a463cce7ac7b1682cfaf44f531fd1258f52f` |
| ai-evaluation/prompts/suggest_refactoring.md | `4ce2a60dae5b15760613144b205156b014282c8809ee8bc1ee02ea1146b106e9` |
| ai-evaluation/prompts/explain_config_relationships.md | `76446ba73863d093215baef0674635dca05d5a2eb9188a12c2400fc0b1749328` |
| ai-evaluation/prompts/README.md (reference; not a scored task prompt) | `e2cfb513a0c8a67c2ff250737b6332cb26a781452c4fbd1152f189e3fff56e59` |

No modification to any of the above was made during this audit (verified via `git diff --stat` against the tracked copies — see Repository integrity below).

## Negative-control verification

`benchmark/dataset/files/edge_cases/false_positives.properties` (494 bytes) vs. `ai-evaluation/experiment/sanitized/edge_cases/false_positives.properties` (508 bytes):

- **Not byte-identical** — hashes differ (see table above).
- **Content-identical**, confirmed via `diff --strip-trailing-cr`: all 14 lines match exactly once line-ending convention is normalized.
- **Root cause: the already-documented CRLF behavior**, not a new finding. The 14-byte difference (508 − 494) equals exactly one extra byte per line (14 lines), consistent with `engine.py`'s Windows text-mode file write converting the original's LF line endings to CRLF on output — the same behavior explicitly documented as a known, unfixed limitation during fixture preparation (and which this task's instructions also say not to fix). No placeholder was inserted, no content was altered, and no detected value differs between the two files — the negative control's substantive property (zero redactions on a file with zero true positives) holds.
- This was accurately described during fixture preparation as "content is identical to the original line-for-line" (not "byte-identical"), so this audit's finding is consistent with, not contradictory to, what was previously established.

## Repository integrity

`git status --short`:
```
?? ai-evaluation/experiment/
?? ai-evaluation/pilot-002/
?? ai-evaluation/pilot/
```

`git diff --stat` against `engine.py`, `rules_default.yaml`, `benchmark/dataset/`, `ai-evaluation/prompts/`, `ai-evaluation/rubric/`, `ai-evaluation/experiment/manifest.json`, and `ai-evaluation/experiment/sanitized/`: **empty (no output)** — confirms zero modification to any tracked source file across all 9 collection batches. Status is limited to exactly the three expected untracked trees; nothing else appears. No staging, commit, reset, or checkout was performed by this audit.

## Pilot separation

- Pilot 001 confirmed intact under `ai-evaluation/pilot/` (`original/java/`, `sanitized/java/`, `results/` including its own `human_evaluation.md`).
- Pilot 002 confirmed intact under `ai-evaluation/pilot-002/` (`original/config/`, `sanitized/config/`, `results/` including its own `human_evaluation.md`).
- No file under `ai-evaluation/pilot/` or `ai-evaluation/pilot-002/` appears anywhere under `ai-evaluation/experiment/results/` (searched by filename pattern; none found).
- The 96-response count is composed entirely of files under `ai-evaluation/experiment/results/` — Pilot 001's and Pilot 002's own two responses each are not, and were never, part of this count.

**Result: clean separation confirmed.**

## Scoring contamination

Searched `ai-evaluation/experiment/` (recursively) for `*human_evaluation*`, `*score*`, `*summary*`, and `*.csv` — **no matches**. The main experiment currently contains only raw `.txt` responses and procedural `batch_record.md` files. No `human_evaluation.md`, no human or LLM-judge scores, and no summary statistics exist anywhere under `ai-evaluation/experiment/`.

Pilot scoring (`ai-evaluation/pilot/results/human_evaluation.md`, `ai-evaluation/pilot-002/results/human_evaluation.md`) exists, as expected, and remains correctly outside the main experiment tree.

**Result: main experiment is free of scoring artifacts.**

## Raw-response integrity observations

Mechanical findings only — no judgment about response quality:

- **Sizes:** 96/96 files present and non-empty. Smallest: `go/identify_bug/original.txt` (745 bytes). Largest: `config/security_analysis/sanitized.txt` (5,217 bytes). Mean ≈2,101 bytes. No file is anomalously small (e.g., near-zero) relative to this spread.
- **Exact-duplicate content across files:** none found — every one of the 96 files has a unique SHA-256 hash.
- **Identical original/sanitized pairs within the same task:** none found for any of the 8 non-negative-control candidates. `edge_cases/false_positives.properties`'s pairs were **not** checked for this (its two conditions receive identical *input* by design, per the negative-control methodology, so identical *output* is possible but not automatic — and in fact none of its 6 response pairs came back byte-identical either, since each is an independent model generation over the same prompt, not a deterministic function of it).
- **Timestamps:** file modification times run in a single, unbroken ascending sequence from the first Java response through the last edge_cases response, consistent with the batches having been generated sequentially in the order reported (Batch 1 → 9). No out-of-order or backdated timestamps observed.
- **Missing final newline:** not evaluated as an error per this audit's own instruction.

No response was flagged as tampered; no finding here rises above an observation.

## Audit conclusion

The collection is **structurally ready for human evaluation**: all 96 expected responses exist, are complete, are correctly organized by candidate/task/condition, carry consistent and (mostly) complete procedural metadata, and show no evidence of modification to any frozen input (engine, rules, dataset, prompts, rubric, manifest, or sanitized fixtures) during collection. Seven confirmed or ambiguous protocol deviations (6 previously documented, 2 newly surfaced by this audit as low-confidence/likely-generic) are catalogued above for the human rater's awareness when scoring the affected responses; none of them prevented a response from being collected, and none required any file to be altered.

This report makes no claim, and should not be read as implying any claim, about whether sanitization improves, harms, or has no effect on AI task performance — that determination is explicitly out of scope for this audit and belongs to the (not-yet-performed) scoring phase.
