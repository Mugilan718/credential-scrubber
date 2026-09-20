# Human evaluation rubric

Used to score **one AI response at a time** (either condition). A rater
scores the original-condition response and the sanitized-condition
response for the same (file, task) pair independently, using this same
rubric both times, then compares the two score sets afterward - the
rubric itself never asks "which condition is better."

**No overall/composite score is produced.** Each dimension is reported on
its own. Averaging correctness with usefulness with consistency into one
number would hide exactly the kind of tradeoff (e.g. "fully correct but
missed the point of the task") this evaluation exists to surface.

## Scoring dimensions (1-5 ordinal each)

### 1. Correctness
Is what the response states about the code/config actually true?

| Score | Meaning |
|---|---|
| 5 | Everything stated is accurate; no factual errors about the code's behavior. |
| 4 | Accurate overall; one minor inaccuracy that doesn't affect the main point. |
| 3 | Mostly accurate, but at least one error a developer would need to correct before trusting the response. |
| 2 | Significant inaccuracies alongside some correct content. |
| 1 | Substantially wrong or fabricated (e.g. describes behavior the code doesn't have). |

### 2. Completeness
Relative to the task's request, did the response cover what it was asked
to cover?

| Score | Meaning |
|---|---|
| 5 | Fully addresses every part of the task's requested structure. |
| 4 | Addresses the task; one requested part is thin but present. |
| 3 | Addresses the core of the task but skips or shortchanges a requested part. |
| 2 | Only partially addresses the task. |
| 1 | Does not meaningfully address the task as asked. |

### 3. Consistency
Compare this response only to *itself* (internal consistency) - does it
contradict itself, or does its stated confidence match what it actually
demonstrates?

| Score | Meaning |
|---|---|
| 5 | Fully internally consistent. |
| 4 | Consistent; one small stylistic wobble. |
| 3 | One noticeable internal contradiction or hedge that undercuts an earlier claim. |
| 2 | Multiple inconsistencies. |
| 1 | Substantially self-contradictory. |

*(Original-vs-sanitized consistency - do the two conditions agree with
each other - is not scored per-response here; it's derived afterward by
comparing the two independently-collected score sheets and, where
useful, the raw responses. See `results/README.md`.)*

### 4. Usefulness
Would a developer's actual workflow be meaningfully advanced by this
response, for this task?

| Score | Meaning |
|---|---|
| 5 | Directly actionable; a developer could act on it with no further digging. |
| 4 | Useful; minor follow-up needed. |
| 3 | Somewhat useful but requires significant additional work to act on. |
| 2 | Marginally useful - mostly restates the obvious or is too generic. |
| 1 | Not useful. |

### 5. Misunderstood a sanitized value?
Specific to responses on the **sanitized condition** (mark "N/A" for
original-condition responses). Did the response treat a placeholder as
something it isn't - e.g. as a real, functioning value; as itself a
vulnerability distinct from the fact that a value was replaced; as a
literal string to reuse in generated code; or otherwise reason about it
in a way that doesn't fit "this stands in for a value of this type"?

| Score | Meaning |
|---|---|
| 5 (best) | No sign of misunderstanding - placeholder(s) treated exactly as type-stand-ins, or not remarked on at all where that's appropriate. |
| 4 | A very minor, inconsequential mis-handling (e.g. slightly odd phrasing) with no effect on the response's substance. |
| 3 | A misunderstanding that's noticeable but doesn't change the response's main conclusions. |
| 2 | A misunderstanding that materially affects part of the response. |
| 1 (worst) | The response's core conclusion depends on a misunderstanding of a placeholder. |

### 6. Relationships between values preserved?
Specific to files/tasks involving more than one sensitive value (mark
"N/A" otherwise). Did the response correctly treat repeated real values
as the same entity, and distinct real values as different entities -
inferred from the sanitized response's placeholders, or directly
observable in the original-condition response?

| Score | Meaning |
|---|---|
| 5 (best) | All same/different relationships correctly reflected. |
| 4 | Correct on the relationships that mattered to the task; a minor, task-irrelevant one is ambiguous. |
| 3 | At least one relationship is ambiguous or unaddressed, but nothing is stated incorrectly. |
| 2 | At least one relationship is stated incorrectly (a false merge or false split - see the main README). |
| 1 | Relationships are substantially wrong throughout. |

## Failure-mode checklist

Tick any that apply (not mutually exclusive with the scores above - this
is for pattern-spotting across many recorded results, not for scoring):

- [ ] Treated a placeholder as a real, working value
- [ ] Flagged a placeholder itself as a security issue (see
  `prompts/security_analysis.md`'s notes)
- [ ] Reused placeholder text literally in generated code in a way that
  wouldn't run/compile
- [ ] False merge - treated two different real values as the same
- [ ] False split - treated the same real value as two different ones
- [ ] Missed a real, sanitization-independent issue in the sanitized
  condition that was correctly found in the original condition
- [ ] Response reveals it inferred (correctly or not) what a placeholder
  probably stood for
- [ ] Other (describe in notes)

## How to use this rubric

1. Read the response once, fully, before scoring anything.
2. Score dimensions 1-4 for every response.
3. Score dimensions 5-6 only where applicable (mark N/A otherwise) - do
   not force a numeric score onto a dimension the response gives no
   basis to judge.
4. Tick any applicable failure-mode boxes.
5. Write freeform notes for anything the fixed scores don't capture -
   the notes field is not optional filler; some of the most useful
   findings from a rubric like this are qualitative, not numeric.
6. Record everything in `results/` (see its README for the exact
   schema) before comparing the sanitized score sheet to the original
   one for that (file, task) pair.
