# Pilot case 001 — java/Config.java × explain_code

**Status: responses collected and scored (provisional, single-pilot).**
This directory validated the Phase 2 experimental procedure end-to-end on
one `(file, task)` pair before the full 9-file × 6-task experiment ran.
Its (file, task) cell is part of the full frozen experiment's grid, not
separate from it - see `../experiment/manifest.json`'s `prior_pilots`
note - but this pilot's own response was not reused or copied into the
full experiment's results; the full experiment independently collected
and scored that same cell under its own isolation rules. See
`metadata.json` for the complete machine-readable record; this file is
the human-readable summary. For the completed full experiment, see
`../experiment/`.

## Source file

`benchmark/dataset/files/java/Config.java` — candidate #1 from
`ai-evaluation/dataset/README.md`'s candidate list.

**Why this file:** the smallest suitable Java candidate that still has
real code structure (a class, two methods, both a field-adjacent block of
local-variable secrets and a separate method) rather than a flat script.
It contains three single-line detected values (`api_key`, `password`,
`client_secret` in the benchmark's ground truth) plus one Java
`+`-operator multiline-concatenated value, so this one 24-line file
exercises both the ordinary and multiline placeholder paths without
needing a larger file. Matches the task brief's explicit preference for a
small Java example with useful surrounding code structure.

## Directory structure

```
ai-evaluation/pilot/
├── README.md            This file.
├── metadata.json         Full machine-readable record of everything below.
├── original/
│   └── java/Config.java  Verbatim copy of the dataset source file - never
│                          passed through the engine. This is the
│                          "original" condition.
└── sanitized/
    └── java/Config.java  engine.scan_project(..., placeholder_mode=True)
                           output, copied byte-for-byte from the engine's
                           actual output directory. This is the
                           "sanitized" condition.
```

No file under `benchmark/dataset/` was modified. `original/` is a copy,
not a move or edit.

## How the sanitized condition was produced

1. `benchmark/dataset/files/java/Config.java` copied into an isolated,
   throwaway single-file input directory (scoped to exactly this one
   file, independent of anything else in `benchmark/dataset/files/java/`).
2. `engine.scan_project(input_dir, output_dir, rules, placeholder_mode=False)`
   run first, as a baseline/cross-check — confirms the engine's default
   (MASK) behavior detects the same findings at the same lines as
   placeholder mode does, before trusting the placeholder-mode run (same
   cross-check principle `run_benchmark.py --placeholder-mode` already
   uses). This run's output was **not** used as the "original" condition —
   see the caveat below.
3. `engine.scan_project(input_dir, output_dir, rules, placeholder_mode=True)`
   run against the same isolated input copy.
4. `sanitized/java/Config.java` is the exact byte content of that run's
   output file — copied directly from the engine's output directory, not
   retyped or hand-edited.

**No hand-authored sanitized fixture was used anywhere in this pilot.**

## Exact placeholders generated

```java
String apiKey = "<GENERIC_SECRET_1>";
String dbPassword = "<PASSWORD_1>";
String clientSecret = "<GENERIC_SECRET_2>";
...
String authToken = "<ACCESS_TOKEN_1>" +
        "" +
        "";
```

| Line | Variable | Category assigned | Token |
|---|---|---|---|
| 12 | `apiKey` | `GENERIC_SECRET` | `<GENERIC_SECRET_1>` |
| 13 | `dbPassword` | `PASSWORD` | `<PASSWORD_1>` |
| 14 | `clientSecret` | `GENERIC_SECRET` | `<GENERIC_SECRET_2>` |
| 19–21 | `authToken` (3-fragment concatenation) | `ACCESS_TOKEN` | `<ACCESS_TOKEN_1>` on line 19, fragments on lines 20–21 emptied |

**Observed, not fixed:** `apiKey` and `clientSecret` resolve to the
generic `GENERIC_SECRET` category rather than the more descriptive
`API_KEY`. This is a real behavior of the already-committed engine (not
something introduced by preparing this pilot, and not modified here per
this task's "do not modify the engine" instruction) — it's the
code-identifier detection path's suspicious-keyword regex backtracking
onto the generic `key` alternative before the more specific `apikey` one
for these particular identifier spellings. This is a new, concrete
instance of the category-resolution limitation already documented in
`BENCHMARK.md`'s Limitations section (the connection-string/URL
divergence). It does **not** affect detection, redaction, leak-freedom,
correlation, or distinctness — `apiKey` and `clientSecret` still
correctly receive two *different* tokens, since they are two different
real values. It only means the category *label* the AI sees is less
specific than ideal for these two values, which is directly relevant to
the research question and worth watching for under the rubric's
"misunderstood a sanitized value" dimension when this pilot is actually
scored.

## Verification performed

- [x] Original source contains the expected detected values, matching
      `benchmark/dataset/cases.jsonl` case ids `java_004_api_key`,
      `java_005_db_password`, `java_006_client_secret`,
      `java_007/008/009_multiline_frag1/2/3` exactly (same lines, same
      categories in ground truth).
- [x] Sanitized source contains a deterministic placeholder for every one
      of those findings.
- [x] MASK-mode and placeholder-mode detection shape (same `(line, key,
      rule, before)` tuples) are identical — confirms placeholder mode
      didn't change *what* is detected, only the replacement text.
- [x] No original sensitive value (`fake-Rk8mNpQ2xWvT5hLj9cBs3fYg7uAe1`,
      `fake-Sup3rSecretPass!2024`, `fake-zP9x2Qn8Lw3kFh7Tj1VbYc5RmA0uEsGd`,
      `fakeAB12`, `CD34secretEF56`, `GH78token90`) appears anywhere in the
      sanitized output.
- [x] Line count preserved (24 → 24).
- [x] Syntax check: `heuristic_valid` for both original and sanitized
      (Java has no stdlib parser available to this project — see
      `BENCHMARK.md`'s documented limitation on heuristic-only syntax
      checks for Java/JS/TS/Go/C#; this is the same check
      `run_benchmark.py` uses).
- [x] Determinism: placeholder-mode scan run twice against the same
      isolated input; sanitized output byte-for-byte identical both times.
- [x] No hand-authored sanitized fixture used at any point.

## Evaluation task

**Prompt template:** `ai-evaluation/prompts/explain_code.md`, used
verbatim and unmodified.

**Why this prompt for the first pilot:** explicitly recommended by the
task brief — "explain the code" is the least dependent on whether the
file happens to contain an actual bug (unlike `identify_bug.md`), so it
tests basic comprehension survival rather than a task this particular
file may not be well-suited for.

The template's `{{SOURCE_CODE}}` slot is filled with `original/java/Config.java`'s
content verbatim for the original-condition call, and
`sanitized/java/Config.java`'s content verbatim for the sanitized-condition
call — no file path included in either (per `prompts/README.md` rule 5),
and no wording differs between the two calls except that one slot.

## Model to be evaluated

**Not yet selected.** No model has been called, no response generated, no
score recorded. Settings to fix at run time (per `prompts/README.md`):
temperature 0, same max-token limit for both conditions, no conversation
history, one call per condition for this pilot.

## Experimental conditions held identical

Per `ai-evaluation/README.md`'s "Experimental controls" and
`prompts/README.md`, the two conditions in this pilot differ **only** in
source representation:

- Same prompt template (`explain_code.md`, verbatim)
- Same source file (two representations of the one file)
- Same task
- Same model / model version (once selected)
- Same model settings
- Same evaluation procedure (same rubric, same rater, blind where
  practical per `results/README.md`)

**The only variable is presence vs. absence of sanitization.**

## Evaluation dimensions (from `rubric/rubric.md`)

1. Correctness (1–5)
2. Completeness (1–5)
3. Consistency — internal (1–5)
4. Usefulness (1–5)
5. Misunderstood a sanitized value? (1–5 or N/A — sanitized condition only)
6. Relationships between values preserved? (1–5 or N/A — relevant here:
   `apiKey`/`dbPassword`/`clientSecret` are three distinct real values,
   and the multiline `authToken` is a fourth; all four must remain
   distinguishable from one another in the sanitized-condition response)

No composite/overall score — each dimension reported on its own, per the
rubric's own instruction.

## Known caveat specific to this pilot file

The source file's own header comment ("Synthetic benchmark fixture -
every value below is fake...") and the literal `fake-` prefix on each
secret value are present **identically in both conditions** — they
predate this pilot and are part of the benchmark dataset's own
synthetic-value labeling convention, not something sanitization added or
removed. This is not a condition leak (both conditions carry the same
text, so it doesn't tell the model which condition it's looking at), but
it does mean this specific file would not read to a model the way an
unlabeled real developer file would — worth keeping in mind when
interpreting this pilot's results, and worth considering a less
self-describing file (or stripping such headers before the prompt is
built) for the full 9-file experiment.

## Results

**None exist.** No model has been called, no LLM judge has been run, no
score has been assigned automatically or otherwise. `ai-evaluation/results/`
is untouched by this preparation — it remains exactly `README.md` and an
empty `results_template.csv`, as already committed.

## Readiness for manual AI evaluation

This one `(file, task)` pair is ready for a human to manually run both
prompt calls and score the two responses with `rubric/rubric.md`, once a
model is selected and the settings above are fixed. See the top-level
report for the full readiness assessment and open questions.
