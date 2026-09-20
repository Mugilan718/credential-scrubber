# Task: Perform security analysis

**Purpose:** the highest-stakes task for this research question. Checks
two failure directions at once: (a) does sanitization cause the model to
*miss* a real, unrelated security issue because it got distracted by or
confused about a placeholder, and (b) does it cause the model to
*hallucinate* a security issue caused by the placeholder itself (e.g.
flagging `<API_KEY_1>` as "a hardcoded secret" when the point of this
whole project is that the real one has already been removed).

**Rubric dimensions this task primarily exercises:** correctness,
completeness, whether the response misunderstood a sanitized value.

## Template

```
The following is a {{FILE_EXTENSION}} file. Perform a security review of
it, as if you were reviewing a pull request.

List each finding as:
- Severity (Low/Medium/High)
- Location (line or section)
- Description of the issue
- Why it matters
- Suggested fix

If you have no findings, say so explicitly rather than inventing one.

Code:

{{SOURCE_CODE}}
```

## Notes

- A response that flags a placeholder-shaped value (e.g.
  `<DB_PASSWORD_1>`) as itself "a hardcoded secret that should be
  rotated" is an expected, informative outcome to record, not a
  disqualifying one - `results/` has a dedicated failure-mode field for
  exactly this ("treated placeholder as a real secret").
- This task is run on both the original (which may have its own,
  sanitization-unrelated issues to find) and the sanitized version, so a
  genuine, sanitization-*independent* finding should ideally appear in
  both conditions - a finding that appears in the original but silently
  disappears in the sanitized version is the specific failure mode this
  task exists to catch.
