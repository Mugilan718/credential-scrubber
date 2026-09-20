# Task: Generate unit tests

**Purpose:** measures whether generated tests remain *structurally* and
*behaviorally* equivalent after sanitization - do the tests still exercise
the same logic, and do any literal values the model chooses for test
inputs make sense (e.g. does it invent a plausible-looking replacement
value, or does it try to reuse the placeholder text verbatim in a way that
wouldn't actually compile/run)?

**Rubric dimensions this task primarily exercises:** correctness,
completeness, structural preservation (does the test suite's shape match
what a test suite for the original would look like).

## Template

```
The following is a {{FILE_EXTENSION}} file. Write unit tests for the
testable logic in it, using a common testing framework for this
language (state which one you chose).

For each test:
- State what behavior it verifies.
- Provide the test code.

If the file has little or no independently testable logic (e.g. it's
mostly static configuration), say so explicitly instead of inventing
tests that don't meaningfully verify anything.

Code:

{{SOURCE_CODE}}
```

## Notes

- Several of the proposed dataset files (see `dataset/README.md`) are
  mostly variable declarations with little control flow - for those, "say
  so explicitly" is the expected, comparable response in both conditions.
- Watch specifically for the model writing an assertion against the
  *placeholder text itself* (e.g. `assertEquals("<API_KEY_1>", ...)`) -
  that's a concrete, recordable instance of the model treating a
  placeholder as if it were the real, stable value it was told to expect
  in the original - useful evidence either way for the "task usefulness"
  dimension.
