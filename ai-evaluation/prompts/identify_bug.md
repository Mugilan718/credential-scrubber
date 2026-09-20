# Task: Identify a bug

**Purpose:** measures whether sanitization changes what the AI flags as
wrong with the code - the most direct test of whether a placeholder gets
mistaken for a real (and differently-shaped) value in a way that changes
the model's judgment.

**Rubric dimensions this task primarily exercises:** correctness,
whether the response misunderstood a sanitized value, consistency
(original vs. sanitized should flag the *same* issues, if any).

**Design note:** the dataset files proposed in `dataset/README.md` were
built for Phase 1 (detection testing), not necessarily seeded with a
deliberate bug. A model may correctly report "I don't see a functional
bug" for some of them - that is a valid, comparable response in both
conditions, not a failed run. Seeding files with an intentional bug is a
reasonable future refinement, not done in this preparation phase.

## Template

```
The following is a {{FILE_EXTENSION}} file. Review it for bugs -
logic errors, incorrect conditions, off-by-one mistakes, resource or
type-handling issues, or anything else that would cause it to behave
incorrectly.

Respond in this format:
- If you find one or more bugs: list each one, with the affected line(s)
  quoted, a one-sentence description of the problem, and a one-sentence
  description of the fix.
- If you do not find a functional bug: say so explicitly, and note
  anything that looks like a code-quality or style concern instead
  (clearly labeled as not a bug).

Code:

{{SOURCE_CODE}}
```

## Notes

- The explicit "if you do not find a bug, say so" branch prevents the
  model from inventing a bug just to have something to report, which
  would make sanitized vs. original responses harder to compare fairly.
