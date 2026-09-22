# Pilot 001 results — raw responses only (not scored)

**Status: two raw responses collected. Not scored. No conclusion drawn.**
This file records only the execution metadata and procedural facts required
to score these responses later with `rubric/rubric.md`. It does not judge,
summarize, or compare response quality, and no automated/LLM scoring was
run.

## Model / version

Claude, model id `claude-sonnet-5` ("Sonnet 5") — the model backing this
Claude Code session. Both conditions were run as a fresh `general-purpose`
Claude Code subagent invocation (via the Agent tool) with no `model`
override specified, so each inherited the parent session's model. This
tool does not return an explicit model-id confirmation string in its
output, so the model identity is recorded as "inherited from the parent
session, not independently re-confirmed per call" rather than as a
directly-observed value for each individual call — see "Procedural
problems / limitations" below.

**Model version:** no separate provider-exposed version/snapshot string
was available through this tooling beyond the model id above.

## Settings

| Setting | Value |
|---|---|
| Temperature | Not independently controllable via the available tooling (the Agent tool exposes no temperature parameter). Not overridden for either condition, so whatever the platform's default is was applied identically to both — held constant across conditions, but not confirmed to be a specific numeric value or forced to `0` as `prompts/README.md` recommends. |
| Max output tokens | Not independently controllable via the available tooling; no explicit limit was set for either condition. |
| Conversation history | None — each condition was a single fresh Agent tool invocation with no prior turns and no shared context. |
| Sampling | One call per condition, no repeated sampling, per `prompts/README.md`. |

## Prompt used

`ai-evaluation/prompts/explain_code.md`, template used verbatim. Both
conditions received byte-identical prompt text except for the
`{{SOURCE_CODE}}` slot; `{{FILE_EXTENSION}}` was filled as `.java` in
both.

## Source files

| Condition | File | 
|---|---|
| A — original | `ai-evaluation/pilot/original/java/Config.java` |
| B — sanitized | `ai-evaluation/pilot/sanitized/java/Config.java` |

Neither file was modified to run this pilot. Content was inserted into
the prompt template verbatim, with no file path included (per
`prompts/README.md` rule 5) and no additional annotation, diff markup, or
commentary added around it.

## Execution date

2026-09-20T12:55:37Z (UTC) — both conditions run within the same short
session, condition A and condition B launched as two separate, parallel
tool invocations.

## Confirmation: independent conversations

**Confirmed.** Condition A and Condition B were separate Agent tool
invocations, each spawning its own fresh subagent with no memory of the
other and no memory of this outer conversation. Their distinct internal
identifiers (`a98685db58d77d158` for condition A, `acec54c4ede75ab69` for
condition B) confirm they are two independent execution contexts, not one
conversation reused. Neither call's prompt referenced, or could see, the
other condition, the other source file, or this coordinating session.
Both used zero tool calls (confirmed from each invocation's own reported
`tool_uses: 0`) — each response was generated purely from the prompt
text, with no file exploration, search, or other tool use that could have
revealed the benchmark's directory structure, the other condition, or
this project's broader context.

## Confirmation: no additional context provided

**Confirmed**, with one caveat pre-existing in the source file itself
(not introduced by this run):

- Neither condition's prompt mentioned that this is an experiment, that
  the source had been sanitized, that a comparison against another
  version exists, or what the placeholder tokens mean. The prompt was
  the `explain_code.md` template filled with only `{{FILE_EXTENSION}}`
  and `{{SOURCE_CODE}}`, exactly as `prompts/README.md` requires.
- **Caveat (already documented in `ai-evaluation/pilot/README.md` before
  this run, not new):** the source file's own header comment —
  `// Synthetic benchmark fixture - every value below is fake and was
  invented for this benchmark. None of it is a real credential.` — is
  present verbatim in *both* conditions, since it is part of the
  original dataset fixture, not something sanitization added or this run
  introduced. Both responses correctly picked up on this and described
  the file as a "benchmark fixture" — that inference came from the
  source text itself, present identically in both conditions, not from
  anything I told either agent. It does not tell the model which
  condition (original vs. sanitized) it is looking at, so it is not a
  condition leak between A and B, but it does mean neither response
  reflects how a model would react to an unlabeled, ordinary developer
  file. Worth choosing a less self-describing file, or stripping such
  headers before building the prompt, for the full 9-file experiment.
- The sanitized-condition response independently noticed and correctly
  described the `<GENERIC_SECRET_1>`/`<PASSWORD_1>`/`<GENERIC_SECRET_2>`/
  `<ACCESS_TOKEN_1>` tokens as "placeholder tokens" / "clearly templated
  stand-ins rather than actual string literals." This was the model's own
  observation from the visible syntax, not something explained to it in
  the prompt — expected and, per `prompts/README.md`, exactly the kind of
  spontaneous observation this methodology exists to capture, not
  something to suppress.

## Raw response files

| Condition | File |
|---|---|
| A — original | `ai-evaluation/pilot/results/original_explain_code.txt` |
| B — sanitized | `ai-evaluation/pilot/results/sanitized_explain_code.txt` |

Both are the complete, unedited response text returned by each
invocation - no trimming, reformatting, or correction applied.

## Procedural problems / limitations encountered

1. **No raw model API access available.** This tooling has no "call the
   provider API directly" primitive exposed to it; the closest available
   approximation to "a fresh AI-agent conversation" is the Agent tool's
   subagent spawn, which carries its own agent-type system-level framing
   (a `general-purpose` agent's role description) in addition to the
   task prompt. This is a real difference from a bare, system-prompt-free
   API call and should be disclosed when interpreting these two
   responses or reusing this procedure for the full experiment - it is
   held identical across both conditions (both used the same subagent
   type with no override), so it should not itself differentiate the two
   responses, but it is not the "no conversation history, just the raw
   prompt" ideal described in `prompts/README.md`.
2. **Temperature and max-output-tokens are not independently settable**
   through this tooling (see "Settings" above) - recorded as "not
   controllable, held constant by omission" rather than as the
   recommended explicit `temperature=0`.
3. **Model-id confirmation is inherited, not independently re-verified
   per call** - the Agent tool does not echo back which exact model
   served a given invocation; this is recorded as "inherited from the
   parent session" based on the tool's documented default behavior, not
   independently confirmed output from each individual call.
4. No other procedural issues encountered - both calls completed
   successfully, used zero tool calls, and returned complete, well-formed
   responses matching the prompt's requested three-part structure.

## What this file deliberately does not contain

No quality assessment, no rubric scores, no comparison of which response
is "better," and no conclusion about whether sanitization helped or hurt
in this case. `results_template.csv` (the top-level `ai-evaluation/results/`
schema) has not been filled in - scoring is a separate, later step, to be
done by a human rater reading `original_explain_code.txt` and
`sanitized_explain_code.txt` against `rubric/rubric.md`.
