# Dataset selection — first experiment

No files have been copied or created here yet. This document defines
*how* the first experiment's cases will be selected and prepared, and
proposes a concrete candidate list, so that step is reviewable before any
model is ever called.

## Source of files

All candidate files are drawn from the **existing, already-reviewed**
Phase 1 benchmark dataset at `../../benchmark/dataset/files/` - not new
files. Reusing them means:

- Every value in them is already confirmed synthetic (see the security
  review that followed the GitHub Push Protection incident during Phase
  1 - no real-provider-shaped credentials remain anywhere in that tree).
- Ground truth for *what's sensitive and what isn't* already exists
  (`benchmark/dataset/cases.jsonl`), so this phase doesn't need to
  redo that labeling work, only build a sanitized companion for each
  chosen file.

## Selection criteria

1. **Language/format diversity** - at least one file per supported
   language, plus at least one JSON and one YAML config file, so the
   syntax-preservation check (dimension C) exercises a real parser for
   most of the set (Python, JSON, YAML), not only the heuristic
   bracket-balance check used for Java/JS/TS/Go/C#.
2. **A genuine mix of true positives** - each file must contain at least
   one real (synthetic) sensitive value, so there's something for
   sanitization to actually change and for the AI's response to
   potentially be affected by.
3. **Small enough to read in one prompt without truncation** - every
   candidate below is under 30 lines.
4. **At least one file with a repeated/related value**, to exercise the
   placeholder-consistency property (see the main README's "Placeholder
   requirements") - candidates with a multiline concatenated secret
   qualify, since the same logical secret is split across several
   physical lines and must reassemble to one placeholder, not several.
5. **One negative control**: a file where sanitization changes nothing
   at all (no true positives, only the kind of ordinary config the
   detection engine correctly ignores). Both "conditions" for this file
   are byte-identical. If a human rater's scores differ meaningfully
   between two identical inputs, that's a signal about rater noise, not
   about sanitization - useful for sanity-checking the methodology
   itself before trusting results on the real comparison pairs.

## Candidate list (proposed, not yet executed)

| # | File | Format | Why this one | Best-suited task(s) |
|---|---|---|---|---|
| 1 | `benchmark/dataset/files/java/Config.java` | Java | API key, DB password, client secret, plus a multiline-concatenated auth token (repeated-value case) | Explain the code; generate unit tests |
| 2 | `benchmark/dataset/files/python/config.py` | Python | `os.getenv`-style password, API key, multiline concatenated secret, several false-positive lines alongside real ones (tests the AI isn't confused by the *mix*) | Identify a bug; explain the code |
| 3 | `benchmark/dataset/files/javascript/config.js` | JavaScript | API token, webhook secret, multiline secret | Security analysis |
| 4 | `benchmark/dataset/files/typescript/auth.ts` | TypeScript | Auth token, a typed (`: string`) secret declaration, a `Bearer` header value caught by a value-pattern rather than a key name | Explain the code; suggest a refactoring |
| 5 | `benchmark/dataset/files/go/config.go` | Go | API key, access token, minimal surrounding code | Suggest a refactoring |
| 6 | `benchmark/dataset/files/csharp/Config.cs` | C# | Session token, multiline concatenated client secret | Generate unit tests |
| 7 | `benchmark/dataset/files/config/appsettings.json` | JSON | Nested `Database` object grouping host/username/password together, plus a top-level API key and a customer ID (currently undetected - see Phase 1's documented gap) | Explain configuration relationships |
| 8 | `benchmark/dataset/files/config/settings.yaml` | YAML | Encryption key, session key (redacted despite being on the placeholder allow-list), an internal endpoint URL | Explain configuration relationships; security analysis |
| 9 | `benchmark/dataset/files/edge_cases/false_positives.properties` | Properties | **Negative control** - no true positives; sanitized version is identical to the original | Explain the code (used as the methodology sanity check, not for a sanitization-effect conclusion) |

Nine files, six languages, two config formats, one negative control - within the "approximately 5-10" scope given for the first experiment.

## Producing the "sanitized" condition for this experiment

**Update:** typed, stable, per-value placeholders are now implemented in
`engine.py` as an opt-in mode - `PlaceholderRegistry` and
`scan_project(..., placeholder_mode=True)` - so the plan below no longer
needs hand-authored fixtures. The sanitized condition for these 9 files
is produced by running the real engine:

1. Copy each chosen file unchanged into `dataset/originals/<same path>`
   (still useful as a stable, explicit record of exactly what went into
   the experiment, independent of the live `benchmark/dataset/files/`
   tree possibly changing later).
2. Run `engine.scan_project(dataset/originals, dataset/sanitized,
   rules, placeholder_mode=True)` to produce `dataset/sanitized/<same
   path>` for real - no hand-editing, no manually-maintained mapping.
   The `report_entries` this call returns already record every
   (file, line, key, rule, before, after) mapping, so there's no need to
   separately track or reconstruct it.
3. The one thing worth reviewing before trusting a file for the
   experiment: run it through `run_benchmark.py --placeholder-mode`'s
   underlying checks (leakage, consistency, distinctness, determinism)
   first, the same way the whole `benchmark/dataset/files/` tree already
   is - a file that fails those checks isn't a fair test of the research
   question, it's a bug report.

Neither `dataset/originals/` nor `dataset/sanitized/` exist yet - they
are created when the experiment actually begins, not in this preparation
phase. Desktop-app/API exposure of `placeholder_mode` is still explicitly
out of scope (see the engine-change task that implemented this) - this
experiment calls `engine.scan_project()` directly, the same way
`run_benchmark.py` does.

## What is explicitly not decided by this document

- The exact wording of each file's sanitized version depends on the
  engine's runtime category/ordinal assignment (deterministic per scan,
  but not something to hand-predict here - see engine.py's
  `PlaceholderRegistry`).
- Which model will be used (a control to fix at experiment time, not a
  dataset question).
- Whether 9 is the final count or whether a pilot run trims it - this
  list is a starting proposal, reviewable before it's acted on.
