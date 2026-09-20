# Task: Suggest a refactoring

**Purpose:** measures whether sanitization affects code-quality judgment
that has nothing to do with the sensitive values themselves - a good
refactoring suggestion should be essentially identical whether or not the
literal secret values are visible, since refactoring targets structure,
naming, and duplication, not data.

**Rubric dimensions this task primarily exercises:** correctness,
usefulness, consistency (a good refactoring suggestion should not change
based on sanitization alone).

## Template

```
The following is a {{FILE_EXTENSION}} file. Suggest one specific,
concrete refactoring that would improve it (e.g. reducing duplication,
improving naming, separating concerns, or improving error handling).

Respond with:
1. The refactoring you suggest, in one or two sentences.
2. Why it's an improvement.
3. A short before/after code snippet illustrating it.

If you don't see a worthwhile refactoring, say so explicitly.

Code:

{{SOURCE_CODE}}
```

## Notes

- If the *same* refactoring is suggested in both conditions, that's a
  clean, positive result for this dimension - record it as such rather
  than only logging disagreements.
- A refactoring suggestion that specifically targets a placeholder
  variable's *naming* in a way it wouldn't have targeted the real
  variable name is a useful, recordable observation.
