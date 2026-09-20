# Task: Explain the code

**Purpose:** measures whether the AI's understanding of what the code
*does* and *why* survives sanitization - the most basic usefulness check.

**Rubric dimensions this task primarily exercises:** correctness,
completeness, whether the response misunderstood a sanitized value.

## Template

```
The following is a {{FILE_EXTENSION}} file. Explain what this code does,
in plain language, for a developer who has not seen it before.

Structure your answer as:
1. One-sentence summary of the file's overall purpose.
2. A short paragraph per major section or logical block, explaining what
   it does and why (not a line-by-line restatement).
3. Anything about the code's structure or behavior you find unclear or
   would want to ask the original author about.

Code:

{{SOURCE_CODE}}
```

## Notes

- Deliberately asks for structure ("purpose", "per-block explanation",
  "open questions") rather than open-ended commentary, so two responses
  can be compared point-by-point on the rubric.
- Part 3 ("anything unclear") is where a spontaneous "this looks like a
  placeholder value" observation would naturally surface, if the model
  makes one - captured in `results/`, not prompted for.
