# Credential Scrubber Benchmark

A synthetic, ground-truth-labeled benchmark for the detection engine
(`engine.py`), built to turn "does this catch secrets" from a feeling into
a number you can re-run after every change.

**What this benchmark does NOT do:** prove the tool is secure. It measures
detection accuracy, sanitization correctness, lightweight syntax
preservation, and performance against one synthetic dataset. A tool can
score perfectly here and still miss secret shapes, languages, or config
formats the dataset doesn't cover - see [Limitations](#limitations).

## Issues this benchmark has found and fixed

- **YAML alias-syntax corruption (fixed).** Redacting an *unquoted* YAML
  value produced a bare `***REDACTED***` token - invalid YAML, since a
  leading `*` is YAML's alias-reference syntax. `quoted_mask()` now
  double-quotes the replacement specifically for `.yaml`/`.yml` files
  when the original value wasn't already quoted (every other format is
  unaffected - the mask stays bare exactly as before). While fixing this,
  a related structural case was also closed: a bare YAML block-scalar
  header (`key: |`) is no longer redacted as if it were a leaf value,
  which used to strip the block-scalar syntax and corrupt the document
  around its own (never-scanned) indented body. See
  `tests/test_yaml_sanitization.py` for the full regression suite and
  [Limitations](#limitations) for what's still not covered (the block
  body itself).

## Running it

```
python run_benchmark.py
```

Prints a human-readable report to stdout and exits non-zero (status 2) if
any original secret value leaked into the sanitized output - the one
failure mode this benchmark treats as critical rather than a score to
optimize.

Useful flags:

```
python run_benchmark.py --json-out results.json   # full machine-readable results
python run_benchmark.py --output-dir out/          # keep the sanitized copy instead of a temp dir
python run_benchmark.py --quiet                    # suppress the text report (e.g. with --json-out)
```

No GUI dependency - it imports `engine.py` directly and calls
`engine.scan_project()`, the same function the desktop app's Flask API
calls.

## Dataset structure

```
benchmark/
  dataset/
    cases.jsonl          <- ground truth, one JSON object per line
    files/
      java/, python/, javascript/, typescript/, go/, csharp/
      config/             <- .json, .xml, .config, .yaml, .properties, .env
      edge_cases/         <- same-substring, repeated-secret, quoting, false positives
  dataset_loader.py
  metrics.py
  syntax_check.py
  memory.py
  report.py
run_benchmark.py
```

Every value in every dataset file is synthetic - clearly fake, invented
for this benchmark, and never a real credential. Files carry a header
comment saying so.

## Ground truth format (`cases.jsonl`)

One JSON object per line. Required fields:

| Field | Meaning |
|---|---|
| `id` | Unique case id |
| `file` | Path relative to `benchmark/dataset/files/` |
| `line` | 1-indexed line number the finding (or non-finding) is at |
| `language` | `java`/`python`/`javascript`/`typescript`/`go`/`csharp`/`config` |
| `file_type` | The file extension, e.g. `.json` |
| `category` | Secret category (`api_key`, `password`, `connection_string`, ..., or `false_positive`) |
| `expected_detection` | `true`/`false` - should the engine flag this line at all |

Optional fields:

| Field | Meaning |
|---|---|
| `original_value` | The exact fake secret text - used for the leak check |
| `expected_output_line` | Exact expected sanitized line, when a substring check would be ambiguous (see below) |
| `value_group` | Links cases that share the same original value, for the placeholder-consistency check |
| `expected_placeholder_category` | A forward-looking label (`DB_PASSWORD`, `API_KEY`, ...) for a **future** typed-placeholder engine - not enforced by today's engine, which uses one shared mask for everything. Recorded now so it doesn't need to be re-derived later. |
| `notes` | Free text - why this case exists, what regression it pins |

Ground truth is data, never code the engine can see - `run_benchmark.py`
only ever compares the engine's actual output against it.

### Why `expected_output_line` exists

Some edge cases (`edge_cases/same_substring.properties`, e.g. `secret_key
= "secret"`) are specifically testing that the key name and the value can
share the same text without redaction masking the wrong span. In that
case a plain "does the original value still appear in the file" check
would misfire: the word "secret" legitimately still appears in the *key
name* `secret_key`, which is not a leak. For these cases, ground truth
instead states the exact expected sanitized line and the benchmark does a
byte-for-byte comparison.

## What each metric means

**Detection** - standard confusion-matrix metrics over `(file, line)`
pairs:

- **True Positive**: a case with `expected_detection: true` that the
  engine flagged at that line.
- **False Positive**: a case with `expected_detection: false` that the
  engine flagged anyway.
- **False Negative**: a case with `expected_detection: true` that the
  engine missed.
- **True Negative**: a case with `expected_detection: false` that the
  engine correctly left alone.
- **Precision** = TP / (TP + FP); **Recall** = TP / (TP + FN); **F1** =
  harmonic mean of the two; **False Positive Rate** = FP / (FP + TN).

Reported overall and broken down by language, file type, and category.
Any engine finding at a `(file, line)` **not** present in ground truth at
all is reported separately as an "unexpected finding" rather than
silently ignored - it usually means the dataset needs a new ground-truth
line, not that the engine is wrong.

**Sanitization correctness** - for every ground-truth case the engine
correctly detected (a TP), checked in this order of severity:

1. **Original secret leakage (critical)** - does the exact original value
   still appear anywhere in the sanitized file, other than the specific
   text a case's key name legitimately shares with it? This is the
   invariant the security audit's F2 finding violated. Any leak here is
   the one thing this benchmark treats as a hard failure, not a score.
2. **Sanitization failure** - the finding was detected, but the output
   line doesn't match what was expected (wrong span, partial redaction,
   or a mismatch against `expected_output_line`), without the original
   value literally surviving.
3. **Placeholder-consistency failure** - two cases sharing a
   `value_group` (the same original secret appearing twice) got
   *different* replacement tokens. This would be a real bug **if** it
   happened; today's engine uses one shared mask for every finding, so
   this should always read zero.

**Placeholder distinctness** is reported as an **informational** note,
not a failure: today's engine cannot give two *different* secrets two
*different* placeholders (`<CUSTOMER_ID_1>` vs `<CUSTOMER_ID_2>`) - that's
explicitly future work (see the audit's AI-agent-security phase), not a
regression. `expected_placeholder_category` in the ground truth exists so
that future work has labels ready to check against.

**Syntax preservation** - after sanitization, is the file still valid in
its own format? Python, JSON, XML/.config, and YAML get parsed for real
with the standard library (`compile()`, `json.loads`, `ElementTree`,
`pyyaml`). Java/JavaScript/TypeScript/Go/C# have no standard-library
parser, and requiring a real compiler toolchain (`javac`, a Go
installation, the .NET SDK, `tsc`) would be a heavy dependency for a
benchmark - see [Limitations](#limitations) - so those get a **heuristic**
check instead (balanced brackets/braces/parens, no unterminated string
literal), clearly labeled `heuristic_valid`/`heuristic_invalid` rather
than `valid`/`invalid` in the report so it's never confused with a real
parse. `.properties`/`.env`/`.ini`/`.conf`/`.cfg` have no real syntax to
violate and are reported as `not_applicable`.

**Performance** - wall-clock time, files scanned, total bytes,
files/second, MB/second, and (best-effort, no new dependency) peak
process memory, all measured from one actual run - a baseline to compare
future runs against, not a target to chase.

## How sanitization correctness relates to detection

These are deliberately kept separate, per the task that created this
benchmark:

```
Detection performance   -> did the engine find the right lines?
Sanitization correctness -> for the lines it found, did the fix actually work?
Performance              -> how fast/heavy was the run?
```

A tool can have perfect detection and still leak secrets through bad
sanitization (this is exactly what the audit's F2 finding was), or vice
versa - detect too little but sanitize whatever it does find flawlessly.
Collapsing these into one score would hide that distinction.

## Limitations

Be honest about what this benchmark does **not** test:

- **No git history / git-diff mode.** The `changed_files_only` scan path
  has its own unit tests (`tests/test_ignore_and_scan.py`) but isn't part
  of this benchmark's dataset.
- **No browser-scanner coverage.** This benchmark only runs the desktop
  Python engine (`engine.py`). The browser scanner (`scanner-engine.js`)
  has its own, smaller feature set (no multiline concatenation) and isn't
  benchmarked here yet - see the audit's roadmap for closing that parity
  gap first.
- **Java/JS/TS/Go/C# "syntax" checks are heuristic, not real parses.**
  They catch a redaction that broke bracket/quote balance, not every way
  a file could become invalid source.
- **YAML block-scalar bodies (`key: |` / `key: >` multi-line values) are
  not scanned at all.** The header line is now left untouched rather than
  corrupted (see "Issues this benchmark has found and fixed" above), but
  the indented content below it - e.g. a PEM-formatted private key pasted
  as a YAML block scalar - is real, undetected, unredacted secret content
  if it's ever a genuine leak. `redact_config_line` only ever looks at one
  physical line at a time; recognizing a block scalar's body would need
  the kind of multi-line, indentation-aware state machine
  `scan_multiline_python`/`scan_multiline_plus` use for code, extended to
  YAML - a real engine change, not something folded into this fix. Tracked
  in `tests/test_yaml_sanitization.py::test_yaml_block_scalar_header_is_left_alone_not_corrupted`.
- **The exact-format value-pattern regexes (`aws_access_key_id`,
  `github_token`, `slack_token`) aren't directly exercised.** Dataset
  values were deliberately given a `fake-`/extra-character prefix so
  nothing in this repository resembles a real secret closely enough to
  trip a credential scanner elsewhere - which incidentally also breaks
  their exact-length match. Detection for those lines happens via
  key-name matching instead (which fires first anyway), so this doesn't
  produce a false result, but it means those specific regexes have no
  dedicated ground-truth case yet. Good next addition.
- **No customer/user-identifier detection exists in the engine at all
  today** (`category: "customer_id"` cases are intentionally marked
  `expected_detection: false` - see `benchmark/dataset/cases.jsonl`).
  This is a real, current gap, recorded honestly rather than worked
  around.
- **113 cases is not exhaustive.** It's enough to pin every regression
  found during the security audit and give real per-language/per-format
  numbers, not enough to claim comprehensive coverage of every secret
  shape in the wild.
- **No AI-task-usefulness measurement yet.** This is Phase 1
  (detection/sanitization) only - the "sanitized vs. original code through
  an AI agent" comparison is intentionally not implemented here.

## Adding a new benchmark case

1. Add or edit a file under `benchmark/dataset/files/<language-or-config>/`.
   Keep every value obviously synthetic (a `fake-`/clearly-invented prefix,
   a header comment saying so).
2. Note the exact 1-indexed line number(s) - read the file back with line
   numbers rather than counting by hand; it's cheap to get wrong.
3. Append one JSON line per case to `benchmark/dataset/cases.jsonl` (never
   edit case IDs already in use - other tooling/history may reference
   them).
4. If the case is testing "the key and value share text" or another
   scenario where a plain substring check would misfire, set
   `expected_output_line` to the exact expected sanitized line instead of
   relying on `original_value`.
5. Run `python run_benchmark.py` and confirm the new case resolves the way
   you intended - if it doesn't, that's either a ground-truth mistake
   (fix the case) or a real engine gap (report it, don't quietly relabel
   the case to make the number look better).
6. Run `python -m pytest tests/` too - the benchmark and the regression
   test suite are complementary, not a replacement for each other (see
   `tests/`'s own docstrings for why a given regression is pinned there
   instead of only in the benchmark).
