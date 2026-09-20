# Prompt templates — design principles

Six fixed task templates live in this directory, one file each. They are
written now, before any experiment runs, so the wording itself can be
reviewed rather than tuned after seeing how a model responds to it (which
would bias the comparison).

## Rules every template follows

1. **Never reveal the condition.** No template may contain the words
   "sanitized", "redacted", "scrubbed", "anonymized", "masked",
   "placeholder", "fake", "synthetic", "benchmark", or any equivalent -
   in either the original- or sanitized-condition run. The model sees
   only "the following code" or equivalent neutral framing. If a model
   *spontaneously* notices and comments on a placeholder-shaped value,
   that's a real, valuable observation for `results/` to capture - the
   point is not to prompt for it either way.
2. **Identical wording across conditions.** The exact same template text
   is used for the original-condition run and the sanitized-condition
   run of a given file+task. Only the `{{SOURCE_CODE}}` slot differs.
3. **Deterministic, not open-ended.** Each template asks for a specific
   response shape (e.g. "list up to 3 issues, one per line, with a line
   number") rather than free-form commentary, so two responses are
   actually comparable on the rubric rather than differing mainly in
   writing style.
4. **One task per template, no task-mixing.** A single call answers one
   fixed question. This keeps the rubric's "completeness" dimension
   well-defined (completeness *with respect to that one task*).
5. **No file name or path in the prompt.** Only the file's content is
   shown. A real filename like `Config.java` is harmless, but a
   fixture-revealing path like `benchmark/dataset/files/java/Config.java`
   would be exactly the kind of condition leak rule 1 forbids.
6. **Language is inferred by the model from the code, or stated neutrally
   by extension only** (e.g. "The following is a `.java` file:") - never
   phrased in a way that implies anything about where the file came from.

## Template variables

Every template uses exactly one placeholder token, `{{SOURCE_CODE}}`,
substituted with either the original or the sanitized file content
verbatim (no extra annotation, no diff markup, no line-by-line
commentary added around it).

## Recommended model-call settings (to fix at experiment time, not decided here)

- **Temperature: 0** (or the provider's lowest-variance setting) for
  both conditions, so response differences reflect the input difference,
  not sampling noise. If a provider only supports temperature 0 at the
  cost of some other setting, document the tradeoff in `results/` rather
  than silently picking a different value per condition.
- **Same max-token / length limit** for both conditions.
- **No conversation history** - each (file, task, condition) call is a
  single, fresh, independent request. No prior call's output may appear
  in a later call's context.
- **Run each (file, task, condition) pair once for the pilot** (no
  repeated sampling yet) - repeated sampling to measure response
  variance is a reasonable extension, but adds a dimension the pilot
  doesn't need to carry yet.

## The six templates

| File | Task |
|---|---|
| `explain_code.md` | Explain the code |
| `identify_bug.md` | Identify a bug |
| `security_analysis.md` | Perform security analysis |
| `generate_unit_tests.md` | Generate unit tests |
| `suggest_refactoring.md` | Suggest a refactoring |
| `explain_config_relationships.md` | Explain configuration relationships (config files only - see the template for scope) |

Not every template is used for every dataset file - `dataset/README.md`'s
candidate table proposes which task(s) suit which file. A code file
doesn't get the config-relationships task, and a plain `.properties` file
without nested structure doesn't get a particularly interesting run of
it either.
