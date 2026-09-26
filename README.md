# Credential Scrubber

Credential Scrubber is a security boundary for sharing source code with AI
coding agents. It detects and sanitizes sensitive values in source code
before that code is shared, while an ongoing research track explores
whether enough semantic information can be preserved for an AI agent to
still perform useful software-engineering tasks on the sanitized version.

It ships today as a local desktop web app for credential detection and
sanitization. A deterministic, typed placeholder mode exists in the
underlying engine and has been evaluated in a research track under
`ai-evaluation/` - see [§2](#2-what-the-project-contains) for exactly
which parts are shipped, which are engine-only, and which are research
findings.

---

## 1. The problem

```text
Developer source
      |
      v
Credential Scrubber
      |
      v
Sanitized source
      |
      v
AI coding agent
      |
      v
AI response / generated code
```

Pasting or handing off source code to an AI coding agent sends whatever
that file contains - including any hardcoded credential - to a third
party's context window, logs, and possibly training pipeline. Credential
Scrubber sits before that step and removes sensitive values first.

The simplest fix - replacing every secret with the same generic mask -
also removes information an AI agent needs to reason correctly about the
code:

```text
password = "***REDACTED***"          # every secret looks identical
apiKey   = "***REDACTED***"          # is this the same value as above, or different?
```

A typed, per-value placeholder preserves more of that structure:

```text
password = <PASSWORD_1>
apiKey   = <API_KEY_1>
```

**This typed-placeholder form ("semantic placeholder mode") is an
engine/research capability, not the desktop app's current default
behavior** - see [§2](#2-what-the-project-contains). The desktop app's
default sanitization is the single shared mask shown above.

This project's research question, investigated in `ai-evaluation/`:

> Can sensitive source-code values be sanitized before providing source
> code to an AI coding agent while preserving enough semantic
> information for the AI to perform useful software-engineering tasks?

## 2. What the project contains

The repository is three distinct things. Keeping them distinct matters -
none of the claims below extend past its own scope.

### Shipped desktop application

A local Python/Flask web app (`app.py`), runnable from source or
packaged as a Windows executable via the included PyInstaller spec
(`CredentialScrubber.spec`). It provides:

- Credential detection and sanitization via `engine.py`.
- Project management - add a project (source folder + output folder),
  each with its own editable copy of the detection rules.
- **Full scan** of a project's files, or a **git changed-files scan**
  (only files git reports as changed/staged/untracked are scanned and
  rewritten - see [§4](#4-detection-and-sanitization) for exactly what
  that means).
- **Scan history** per project, stored locally.
- A **sensitive-value reveal** workflow - the default report never shows
  a raw secret; an explicit "Reveal original values" action loads the
  real before/after values from a bounded, in-memory cache (see
  [§5](#5-privacy-and-security-properties)).
- A native OS folder-browse dialog for picking source/output folders.
- A visual rule editor (key names and the placeholder allow-list; regex
  patterns are edited via `rules_default.yaml`).
- Dark mode and a self-contained local UI - no cloud sync, no accounts,
  no telemetry.

**Normal sanitization from this app uses MASK-mode redaction**
(`***REDACTED***`), not the typed placeholders described next.

### Engine capabilities: deterministic semantic placeholders

`engine.py` also implements an opt-in **placeholder mode**
(`scan_project(..., placeholder_mode=True)`):

- Each detected value is replaced with a typed, numbered placeholder
  (`<API_KEY_1>`, `<PASSWORD_1>`, ...) drawn from a small fixed category
  set (`PASSWORD`, `API_KEY`, `ACCESS_TOKEN`, `CONNECTION_STRING`,
  `URL`, `PRIVATE_KEY`, `GENERIC_SECRET` as the fallback).
- A per-scan `PlaceholderRegistry` guarantees the same real value maps to
  the same placeholder everywhere it repeats within that scan, and two
  different real values never collide on one placeholder - tested
  directly (`tests/test_placeholders.py`).
- Ordering is deterministic (repeated scans of the same input produce
  identical placeholder numbering).
- Placeholder text is XML-escaped where the surrounding line is an XML
  shape, so a token like `<API_KEY_1>` doesn't break `.xml`/`.config`
  output.
- The registry holds real values only in memory for the duration of one
  scan call; it is never persisted, logged, or exported.
- Exercised by `tests/test_placeholders.py` and by
  `run_benchmark.py --placeholder-mode`, which additionally checks
  leakage, placeholder consistency/distinctness, determinism (a second
  run compared byte-for-byte), and syntax preservation.

> **Semantic placeholder mode is currently available through the engine
> and benchmark/research paths; it is not exposed through the desktop
> application's UI or API.** `app.py`'s scan route does not pass
> `placeholder_mode`, so the running app always uses MASK mode today.

### AI evaluation / research

`ai-evaluation/` is a completed research track, not a product feature or
an integration. It measures whether an AI coding agent's task output on
a sanitized (placeholder-mode) file is comparable to its output on the
original file, for a fixed set of files and tasks:

- 9 candidate files across 6 languages/formats.
- 6 software-engineering tasks per applicable file.
- 96 total AI responses: 48 from the original file, 48 from the
  sanitized file, 48 paired (original, sanitized) comparisons.
- Each response came from an **independent Claude Code subagent
  session**, used only as this evaluation's controlled proxy for "an AI
  coding agent reading the file." **Credential Scrubber itself has no
  integration with Claude Code, and does not intercept or wrap any AI
  agent.**
- No LLM judge anywhere - every response was scored by a human rater
  against a frozen rubric.
- Full descriptive and inferential statistical analysis, with
  reproducible figures. See [§7](#7-ai-evaluation).

## 3. Architecture

```text
                    Credential Scrubber
                           |
             +-------------+-------------+
             |                           |
        Detection                    Sanitization
             |                           |
     +-------+--------+          +-------+--------+
     |       |         |         |                |
  Key-name  Pattern  Entropy   Masking      Semantic placeholders
   match     match   (config/   (default,      (opt-in,
                      multiline   shipped)     engine/research
                      only)                      only)
     +-------+--------+          +----------------+
             |
             v
      Sanitized source
             |
             v
       AI coding agent
```

Actual repository layout (only components that exist):

```text
credential-scrubber-app/
├── app.py                  Flask server + REST API
├── engine.py                Core scanning/sanitization engine (importable, no CLI dependency)
├── db.py                    Local SQLite storage: projects, scan history, per-finding ignores
├── rules_default.yaml       Default rule set (key/value/code patterns, placeholder allow-list)
├── rules.json, rules-data.js   Generated mirrors of rules_default.yaml (export_rules.py) -
│                              not currently loaded by the app itself
├── templates/, static/       Frontend (HTML shell + vanilla JS/CSS)
├── benchmark/                 Synthetic detection/sanitization/performance benchmark
├── run_benchmark.py          Benchmark CLI (includes --placeholder-mode)
├── BENCHMARK.md               Benchmark methodology, metrics, and limitations
├── tests/                     pytest regression suite
├── test_fixtures/             Sample input/output pairs used ad hoc during development
├── ai-evaluation/             Completed AI-agent evaluation research track
├── requirements.txt, requirements-dev.txt   App and app-test dependencies
└── run.bat, run.sh            Convenience launch scripts
```

**`data/` is not where the database lives.** The local SQLite file and
the app's writable state live in the OS's per-user application-data
directory (`%APPDATA%\CredentialScrubber` on Windows,
`~/.credential-scrubber` elsewhere - see `db.py`), not in the repository.

## 4. Detection and sanitization

**Detection mechanisms:**

- **Key-name matching** - case-insensitive, boundary-aware matching
  against `key_patterns` (e.g. `password`, `api_key`, `secret`).
  Always redacts, regardless of the placeholder allow-list.
- **Value-pattern matching** - regexes for shapes like IPs, connection
  strings, AWS/GitHub/Slack-style tokens, JWTs, bearer tokens, and PEM
  private-key blocks. Subject to the placeholder allow-list.
- **Entropy detection** - a Shannon-entropy check on candidate values
  (min length 20, min entropy 3.5), used in config-line and multiline
  detection. **It is not used as a generic detector on single-line code
  literals** - that path relies on key-name and value-pattern matching
  only.
- **Multiline concatenation detection** - Python's parenthesized
  multi-string style, and Java/JavaScript/C#'s `+`-operator style (both
  "trailing +" and "leading +"). **Go is not currently covered** by
  multiline detection. JavaScript template literals spanning multiple
  lines are not covered either.

**Supported languages/formats**, from `engine.py`'s extension mapping:

| Language/format | Notes |
|---|---|
| Java, Python, Go, C# | Each its own code-pattern rule set. |
| JavaScript / TypeScript | `.js`, `.jsx`, `.ts`, and `.tsx` are all handled by **the same merged JavaScript rule set** - TypeScript does not have a separate rule set. |
| JSON, XML, `.config` | Line/regex-based key-value matching, **not a full parser** - see below. |
| YAML | Regex-based key-value matching; see the block-scalar limitation below. |
| `.properties`, `.env`, `.ini`, `.conf`, `.cfg` | Config-style key-value matching. |

Any other file extension is copied through unscanned rather than parsed
as text.

**JSON/XML/.config handling is regex/line-based**, matching
`"key": value` / `<add key=".." value=".."/>` / `<Key>value</Key>`
shapes directly rather than parsing the format - this is intentional
(no full-format parser dependency) and is a known limitation, not a bug.

**YAML block-scalar bodies (`key: |`, `key: >-`) are not scanned at
all.** The block header is recognized and left untouched, but the
indented content that follows it is not inspected - a secret pasted as a
YAML block-scalar body would not currently be detected.

## 5. Privacy and security properties

- **Raw secret values are never written to the scan-history database.**
  `app.py` strips sensitive values before calling `db.record_scan()`;
  only the redacted report is persisted.
- **The "Reveal original values" view is in-memory only**, capped at the
  20 most recently viewed scans (LRU-evicted). If a scan has aged out of
  that cache or the app has restarted, the reveal view reports the raw
  data as unavailable rather than reconstructing it from anywhere.
- **Symlinks are skipped during scanning** - neither followed/read nor
  copied through, to avoid a symlink pointing outside the intended
  project tree (e.g. into `~/.ssh`) being scanned.
- **The placeholder registry (placeholder mode) is in-memory only for
  the duration of one scan** and is never persisted, logged, or
  exported - there is no reversible placeholder-to-real-value mapping
  saved anywhere.
- **Per-finding "ignore" is a stored, hash-verified mechanism, not a
  `.gitignore`-style path/pattern feature.** An ignored finding is
  tracked by content hash in the database, so if the underlying value
  later changes, the ignore is invalidated rather than silently masking
  a different secret. There is no separate ignore-file/ignore-pattern
  mechanism, and directory exclusion is a fixed, hardcoded list
  (`.git`, `node_modules`, `__pycache__`, build/venv-style directories).

None of the above is a claim of absolute security. See
[§8](#8-what-the-experiment-does-not-establish) and
[§9](#9-known-limitations).

## 6. Benchmark

`benchmark/` and `run_benchmark.py` implement a synthetic,
labeled-dataset benchmark: 113 ground-truth cases across 16 files. It
measures detection precision/recall/F1, whether a detected secret's
value ever survives sanitization (leakage), replacement correctness,
lightweight syntax preservation, and - in `--placeholder-mode` -
placeholder consistency, distinctness, and determinism. Full methodology
and metric definitions are in [BENCHMARK.md](BENCHMARK.md).

**The repository documents the benchmark's methodology and dataset, not
a committed set of execution results.** No benchmark-run output (pass/
fail counts, precision/recall numbers) is checked into this repository;
running `run_benchmark.py` yourself produces those numbers locally. As
`BENCHMARK.md` states directly: *"What this benchmark does NOT do: prove
the tool is secure."*

Known benchmark limitations (see `BENCHMARK.md` for the full list):

- No git-diff/hunk-level evaluation.
- Syntax checks for Java/JS/TS/Go/C# are heuristic (bracket/quote
  balance), not real parses.
- YAML block-scalar bodies are not exercised (same gap as §4).
- Exact-format provider regexes (AWS/GitHub/Slack-style keys) aren't
  directly exercised by the synthetic dataset's `fake-`-prefixed values.
- No customer/user-identifier detection exists in the engine today.
- The placeholder category mapping is a small, best-effort table, not
  exhaustive.
- 113 cases is not exhaustive coverage of real-world secret shapes.

## 7. AI evaluation

**Dataset:** 9 files - Java, Python, JavaScript, TypeScript, Go, C#,
JSON, YAML, and a `.properties` negative control (zero real secrets, by
design). **Tasks:** explain code, identify bug, security analysis,
generate unit tests, suggest refactoring, and explain configuration
relationships (config-shaped files only).

**Conditions**, per applicable (file, task) pair:

```text
Original source    -> independent Claude Code subagent session -> AI response
Sanitized source    -> independent Claude Code subagent session -> AI response
```

No session saw both conditions, no session was told sanitization was
involved, and no LLM was used to judge the responses - a human rater
scored every one of the 96 responses against a frozen rubric.

**Human scoring dimensions:** Correctness, Completeness, Consistency,
Usefulness (always scored), plus "Misunderstood a sanitized value?" and
"Relationships between values preserved?" - both scored only where the
response/task made them applicable (e.g. relationship-preservation was
scored only for the explain-configuration-relationships task).

**Results** (exact values from
`ai-evaluation/experiment/analysis/inferential_results.csv`; two-sided
Wilcoxon signed-rank test on the 48 paired [Sanitized − Original]
differences, Holm-Bonferroni-corrected across the four dimensions with a
valid test):

| Dimension | Non-zero pairs (of 48) | Raw p | Holm-adjusted p | Distinguishable from zero (α=0.05)? |
|---|---:|---:|---:|---|
| Correctness | 1 | 0.317311 | 0.317311 | No |
| Completeness | 6 | 0.026434 | 0.052869 | No (adjusted p just above 0.05) |
| Consistency | 0 | - | - | No test performed - all 48 pairs unchanged |
| Usefulness | 7 | 0.015764 | 0.047292 | Yes |

The evaluation found a statistically distinguishable paired difference
in Usefulness under the tested conditions, while Correctness and
Completeness did not cross the Holm-adjusted significance threshold;
Consistency did not change in any of the 48 pairs. **This is not proof
that sanitization caused the Usefulness difference.** Only 7 of 48
Usefulness pairs changed, all in the same direction, concentrated in two
tasks (`generate_unit_tests`, `suggest_refactoring`).

A byte-identical negative control (the `.properties` file, where the
sanitized fixture is identical to the original because nothing was
detected) tests for ordinary model/session variability independent of
sanitization: 5 of 6 paired responses were unchanged, but **1 of 6
changed despite receiving identical input in both conditions**. This is
direct evidence that response variability alone - with no sanitization
effect possible - can produce a paired difference of comparable shape,
which is why the Usefulness result above is not attributed to
sanitization outright.

Six of the 96 responses contained an ambient project-directory-name or
filesystem-path reference from the evaluation session's own environment
- **not** a scrubbed-credential leak, and not derived from any file's
content. These were excluded from scoring credit; a sensitivity analysis
excluding all affected pairs (N=43) reproduced the same statistical
conclusions as the full N=48 analysis.

Across all 96 responses, no false merge, false split, reconstructed
secret, unrunnable placeholder reuse, or placeholder-flagged-as-a-
security-issue occurred; two mild placeholder-interpretation cases were
recorded, neither affecting a scored outcome.

Full write-up:
[`ai-evaluation/experiment/analysis/results_and_discussion.md`](ai-evaluation/experiment/analysis/results_and_discussion.md).

## 8. What the experiment does NOT establish

- Absolute AI-agent safety, or safety against prompt injection, tool-use
  side channels, or provider data retention.
- The absence of all information leakage in every possible scenario.
- Guaranteed semantic preservation for files, languages, or secret
  shapes outside the 9 tested files.
- Guaranteed AI coding performance, in general or for any specific task.
- Causal attribution of every observed response difference to
  sanitization - the byte-identical control (§7) shows ordinary
  variability alone can produce a similarly-shaped difference.
- Production readiness across arbitrary, real-world codebases - the
  dataset is small and synthetic.
- Effectiveness against every possible credential format or obfuscation
  technique.
- Superiority over, or a replacement for, existing secret-scanning tools
  (Gitleaks, TruffleHog, detect-secrets, Semgrep, GitHub Secret
  Scanning, etc.) - no such comparison was performed.

## 9. Known limitations

- YAML block-scalar bodies are not currently scanned.
- JSON/XML/.config handling is regex/line-based, not a full parser.
- The semantic placeholder category assigned to a value can diverge
  depending on which detection path caught it (a known, unfixed
  engine behavior).
- No customer/user-identifier detection is implemented.
- Placeholder mode is implemented and tested but not exposed through the
  desktop application's UI/API.
- Git changed-files mode scans complete changed files, not
  patch/diff hunks.
- The benchmark dataset (113 cases, 16 files) is not exhaustive.
- The AI evaluation used one model/tooling environment (Claude Code
  subagent sessions, `claude-sonnet-5`) and a fixed, small set of 9
  files and 6 tasks - not a broad or statistically powered study.
- Six responses in the AI evaluation contained an ambient
  environment/path artifact from the collection tooling (§7) - excluded
  from scoring, documented, not sanitizer leakage.
- The Properties negative control demonstrates that ordinary
  model/session response variability exists in this evaluation setup,
  independent of sanitization.

## 10. Installation

**Windows:**

```text
run.bat
```

**Mac/Linux:**

```text
chmod +x run.sh
./run.sh
```

Either script installs the two runtime dependencies (`flask`, `pyyaml`)
and starts the app at `http://127.0.0.1:5057`.

Manual install:

```text
pip install -r requirements.txt
python app.py
```

**Using the app:** add a project (source folder + output folder, output
is never written into the source folder) → optionally edit rules → run a
full or changed-files-only scan → review results by file/line/rule,
using "Reveal original values" only when you need to double-check a
specific finding → past scans are kept in per-project history.

A PyInstaller spec (`CredentialScrubber.spec`) is included for building a
standalone Windows executable from source; no prebuilt binary is
distributed in this repository - the packaged `.exe` is published only as
a GitHub Release asset.

**Verifying your download**

This software is unsigned - it isn't registered with a code-signing
certificate authority, which costs money and isn't practical for a small
open-source project to maintain. As a result, Windows SmartScreen and
most browsers will show an "unrecognized publisher" or "Windows
protected your PC" warning when you download or run the `.exe`. **This is
expected for new, unsigned open-source software and is not by itself a
sign that anything is wrong** - it just means Microsoft hasn't seen
enough downloads of this specific binary yet to build a reputation for
it, the same warning any new unsigned executable gets regardless of what
it does.

To confirm the file you downloaded is exactly the one actually built
from this repository's source (not corrupted in transit, and not
tampered with), check its SHA-256 checksum against the value published
in the release notes for that version:

```text
SHA-256 (CredentialScrubber.exe):
23b645f355b4db735a8214a746a2313f4e26ac07f5115a57723870f650a9e47a
```

On Windows:

```text
certutil -hashfile CredentialScrubber.exe SHA256
```

On Mac/Linux:

```text
shasum -a 256 CredentialScrubber.exe
```

If the output doesn't match the checksum published for that release, do
not run the file - re-download it, and if it still doesn't match, open
an issue.

Since the full source is public, if you'd rather not run a prebuilt
binary at all, you don't have to - build it yourself directly from
source with the PyInstaller spec above (`pip install -r requirements.txt
pyinstaller` then `pyinstaller CredentialScrubber.spec`), so you never
have to trust a binary you didn't build.

**Tests:**

```text
pip install -r requirements-dev.txt
python -m pytest tests/
```

The test suite pins specific bugs found during a security audit (e.g. a
JSON/XML config key going unredacted, a redaction masking the wrong span
when a key and its value share text) so they can't silently regress.

## 11. Benchmark / research reproduction

```text
# Detection/sanitization/performance benchmark
python run_benchmark.py

# Same benchmark, plus placeholder-mode-specific checks
# (consistency, distinctness, determinism)
python run_benchmark.py --placeholder-mode
```

Reproducing the AI-evaluation statistical analysis and figures requires
a separate, research-only dependency set (kept out of the app's own
`requirements.txt`):

```text
pip install -r ai-evaluation/requirements-research.txt

# Paired Wilcoxon / Holm-Bonferroni / bootstrap-CI analysis
python ai-evaluation/experiment/analysis/run_inferential_analysis.py

# Regenerates the 4 research figures under ai-evaluation/experiment/analysis/figures/
python ai-evaluation/experiment/analysis/generate_figures.py
```

The descriptive statistics in `descriptive_results.md` were produced by
a one-off analysis pass; no script for regenerating that specific
document is committed to this repository.

## 12. Repository structure / research artifacts

`ai-evaluation/` holds the completed AI-evaluation research track as
committed artifacts, not runtime dependencies of the application:

- `experiment/manifest.json` - the frozen experiment design.
- `prompts/` - the fixed task prompt templates.
- `rubric/rubric.md` - the frozen human-scoring rubric.
- `experiment/results/` - raw AI responses and per-file human
  evaluations (96 responses).
- `experiment/analysis/evaluation_dataset.csv` /
  `paired_deltas.csv` - the scored data in structured form.
- `experiment/analysis/descriptive_results.md`,
  `inferential_results.md`, `results_and_discussion.md` - the analysis
  and write-up.
- `experiment/analysis/figures/` - the 4 reproducible research figures.

These are research artifacts for review and reproduction; the desktop
application does not read from or depend on anything under
`ai-evaluation/`.

## 13. Project status

**Status: active research prototype.**

| Component | Status |
|---|---|
| Desktop sanitizer (MASK mode) | Implemented, shipped |
| Semantic placeholder mode | Implemented and tested (engine + benchmark/research only) |
| AI evaluation | Completed for the documented 9-file/6-task experiment |
| Claude Code / AI-agent integration | Not implemented - no such integration exists in this project |

## 14. Future work

- Expose semantic placeholder mode through the desktop app's UI/API.
- Improve placeholder-category consistency across detection paths.
- Parser-backed (not regex-based) structured-format handling for
  JSON/XML/YAML.
- YAML block-scalar body scanning.
- Broader benchmark coverage (more secret shapes, more languages).
- Broader AI-agent/task evaluation - more files, more models, repeated
  sampling per condition to separate variability from effect.
- Patch/hunk-level git scanning, instead of whole-changed-file scanning.
- Customer/user-identifier detection.

## 15. License

Licensed under the [GNU Affero General Public License v3.0](LICENSE)
(AGPLv3). In practical terms: you're free to use, modify, and
redistribute this code, including commercially. The one condition that
differs from plain GPL is what happens if you run a modified version as
a network service (e.g. host it and let others use it over a network,
without distributing the software itself) - AGPL treats that as
distribution too, so you're required to make your modified source
available to those users, not just to people you hand a copy of the
binary to. See the [LICENSE](LICENSE) file for the full legal text.

---

If a real secret is ever found by this tool, rotate it. Masking it for
AI-sharing or review purposes does not undo any prior exposure.
