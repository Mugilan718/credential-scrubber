# Pilot 002 — config/appsettings.json × explain_config_relationships

**Status: responses collected and scored (provisional, single-pilot).**
This directory prepared and ran the second `(file, task)` pair for the
Phase 2 evaluation procedure, following the same "real engine output,
never hand-authored" methodology as Pilot 001. Its (file, task) cell is
part of the full frozen experiment's grid, not separate from it - see
`../experiment/manifest.json`'s `prior_pilots` note - but this pilot's
own response was not reused or copied into the full experiment's
results; the full experiment independently collected and scored that
same cell under its own isolation rules. For the completed full
experiment, see `../experiment/`.

## Source file

`benchmark/dataset/files/config/appsettings.json` — candidate #7 from
`ai-evaluation/dataset/README.md`'s candidate list.

## Why this file was selected

Selected after a dedicated candidate-selection audit comparing all 9
files in `ai-evaluation/dataset/README.md`'s list. The deciding factors:

- **Category diversity, without Pilot 001's category-collapse issue.**
  Pilot 001 (`java/Config.java`) had `apiKey` and `clientSecret` both
  resolve to the generic `GENERIC_SECRET` category, due to a
  code-identifier regex-backtracking quirk in the engine's source-code
  detection path. This file's three sensitive values are all caught via
  the config-key path instead (`redact_config_line`), which already
  reconciles multiple matching key patterns correctly — confirmed by
  actually running the engine for this pilot: `Database.Host` →
  `<URL_1>`, `Database.Password` → `<PASSWORD_1>`, `ApiKey` →
  `<API_KEY_1>` — three distinct, specific categories, no collapse.
- **A genuine nested-grouping relationship to test.** `Database.Host` and
  `Database.Password` are already grouped under one `Database` object in
  the original file (alongside the correctly-unflagged
  `Database.Username`). This is exactly the shape
  `explain_config_relationships.md`'s own notes call out as "the clearest
  test" of whether a value grouping survives sanitization both
  structurally and in how a model narrates it.
- **Structurally unlike Java.** A nested JSON object, not source code — no
  classes, methods, or control flow.
- **No self-describing disclosure comment.** JSON has no comment syntax,
  so this is the only one of the 9 candidates without a `// Synthetic
  benchmark fixture...`-style header — see "Residual synthetic signals"
  below for what *does* still leak the fixture's nature.

## Why `explain_config_relationships` instead of `explain_code`

`explain_config_relationships.md` explicitly scopes itself to config
files only (`.json`, `.yaml`, `.properties`, `.xml`, `.env`, `.config` —
"not run against source-code files") and names this exact file as its
clearest test case in its own notes:

> "The proposed `appsettings.json` candidate... is the clearest test of
> this: `Database.Host`, `Database.Username`, and `Database.Password` are
> already nested under one object in the original file, so this task is
> partly about whether that grouping survives sanitization structurally
> ... *and* whether the model still narrates it correctly in prose (this
> task)."

`ai-evaluation/dataset/README.md` likewise lists this file's best-suited
task as "Explain configuration relationships," not `explain_code`.
`explain_code.md`'s generic "explain what this code does" framing is a
looser fit for a config document than for source code, and would not
specifically probe the relationship-preservation property this file was
chosen to test — the entire reason this file was selected over an
equally-multi-value source-code candidate was to exercise that property,
so using the task built for it is the more methodologically sound choice.

## Difference from Pilot 001

| | Pilot 001 | Pilot 002 |
|---|---|---|
| File | `java/Config.java` | `config/appsettings.json` |
| Format | Java source code | JSON config (nested object) |
| Task | `explain_code` | `explain_config_relationships` |
| Detected values | 4 (3 single-line + 1 multiline-reconstructed) | 3 (all single-line) |
| Categories reached | `PASSWORD`, `GENERIC_SECRET` ×2, `ACCESS_TOKEN` (2 of 4 collapsed to the generic category) | `URL`, `PASSWORD`, `API_KEY` (all three distinct) |
| Relationship shape tested | One value reconstructed across 3 physical lines (same-value correlation) | Two values grouped under one nested object, alongside a third, unrelated value (grouping / false-merge avoidance) |
| Disclosure comment | Present (`// Synthetic benchmark fixture...`) | Absent (JSON has no comment syntax) |
| Known engine gap present | No | Yes — `CustomerId` (see below) |

Together the two pilots exercise two different kinds of "relationships
between values preserved?" (rubric dimension 6): same-value correlation
(Pilot 001) and correct grouping/non-merging of distinct-but-related
values (Pilot 002).

## Residual synthetic signals

This file has no disclosure *comment*, but it is not free of synthetic
signals:

- `"AppName": "BenchmarkDemo"` — the value itself names "Benchmark"
  explicitly, a real (if less blatant) self-describing signal.
- Every secret value carries a `fake-` prefix (`fake-db.internal.example`,
  `fake-hunter2`, `fake-Rk8mNpQ2xWvT5hLj9cBs3fYg7uAe1`) — present in the
  *original* condition only; these prefixes are removed along with the
  rest of the secret text in the sanitized condition, so they do not leak
  into that condition, but a model reading the original-condition file
  can plausibly infer synthetic/test data from them.

Both signals are pre-existing properties of the dataset fixture, not
introduced by this pilot's preparation.

## CustomerId is intentionally left unsanitized

`"CustomerId": "PF001"` (line 14) is **unchanged in both conditions** —
confirmed byte-for-byte identical between `original/config/appsettings.json`
and `sanitized/config/appsettings.json`. This is not a leak or an
oversight: no customer/user-identifier detection rule exists in the
engine today (a documented, pre-existing gap — see `BENCHMARK.md`
Limitations and `cases.jsonl`'s `json_011_customer_id_gap` case,
`expected_detection: false`). This pilot does not add such a rule (per
this task's explicit instruction not to modify detection rules) and does
not work around the gap — `CustomerId` simply passes through untouched,
exactly as the existing engine already behaves on every other file.

## Directory structure

```
ai-evaluation/pilot-002/
├── README.md              This file.
├── metadata.json           Full machine-readable record.
├── original/
│   └── config/
│       └── appsettings.json   Verbatim copy of the dataset source file.
└── sanitized/
    └── config/
        └── appsettings.json   engine.scan_project(..., placeholder_mode=True)
                                 output, copied byte-for-byte from the
                                 engine's actual output directory.
```

No file under `benchmark/dataset/` was modified. `original/` is a copy,
not a move or edit.

## How the sanitized condition was produced

1. `benchmark/dataset/files/config/appsettings.json` copied into an
   isolated, throwaway single-file input directory (`config/appsettings.json`
   only — not the rest of `benchmark/dataset/files/config/`, so the scan
   is unambiguously scoped to this one file).
2. `engine.scan_project(input_dir, output_dir, rules, placeholder_mode=False)`
   run first, as a baseline/cross-check — confirms the same findings are
   detected at the same lines in both modes before trusting the
   placeholder-mode run.
3. `engine.scan_project(input_dir, output_dir, rules, placeholder_mode=True)`
   run against the same isolated input copy.
4. `sanitized/config/appsettings.json` is the exact byte content of that
   run's output file — copied directly from the engine's output
   directory, not retyped or hand-edited.

**No hand-authored sanitized fixture was used anywhere in this pilot.**

## What has NOT been done

No AI model has been called. No response has been collected for either
condition. Nothing has been scored. This is preparation only — the same
stage Pilot 001 was in before its `results/` directory existed.
