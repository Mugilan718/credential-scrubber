# Pilot 002 results — raw responses only (not scored)

**Status: two raw responses collected. Not scored. No conclusion drawn.**
This file records only execution metadata and procedural facts. It does
not judge, summarize, or compare response quality, and no automated/LLM
scoring or comparison was run.

## Model / version

Claude, model id `claude-sonnet-5` ("Sonnet 5") — the model backing this
Claude Code session. Both conditions were run as a fresh `general-purpose`
Claude Code subagent invocation (via the Agent tool) with no `model`
override specified, so each inherited the parent session's model. This
tool does not return an explicit model-id confirmation string in its
output, so the model identity is recorded as "inherited from the parent
session, not independently re-confirmed per call," consistent with how
Pilot 001's execution record documents the same limitation.

**Model version:** no separate provider-exposed version/snapshot string
was available through this tooling beyond the model id above.

## Fresh, independent subagents

**Confirmed.** Two separate Agent tool invocations, each spawning its own
fresh subagent with no shared memory:

| Condition | Subagent id |
|---|---|
| A — original | `aa45652db9d05fb94` |
| B — sanitized | `a82bc6c96ff5563df` |

Neither call's prompt referenced, or could see, the other condition, the
other source file, or this coordinating session. Both invocations were
launched in the same message as two independent tool calls, not one
conversation reused.

## Repository exploration / tool use

**None occurred.** Both invocations reported `tool_uses: 0` in their
result metadata — each response was generated purely from the prompt
text handed to it, with no file reads, searches, or other tool calls.
This confirms neither subagent inspected the repository, git history,
Pilot 001, Pilot 002's `metadata.json`, or any other evaluation file —
the prompt text (task template + embedded file content) was the only
input either subagent had access to, satisfying the experiment's
isolation requirement structurally, not just by instruction.

## Exact prompt file used

`ai-evaluation/prompts/explain_config_relationships.md`, template used
verbatim, `{{FILE_EXTENSION}}` filled as `.json` in both conditions.

**Confirmation: prompt text was identical between conditions.** Both
invocations received byte-identical template text; the only difference
between the two prompts was the `{{SOURCE_CODE}}` slot's content (the
original vs. sanitized JSON). No file path, condition label, or any
other framing was added to either prompt.

## Confirmation: only the corresponding file was supplied

- Condition A's prompt contained only
  `ai-evaluation/pilot-002/original/config/appsettings.json`'s content
  (the real, unsanitized values) — the sanitized file's content was never
  included.
- Condition B's prompt contained only
  `ai-evaluation/pilot-002/sanitized/config/appsettings.json`'s content
  (the placeholder tokens) — the original file's content was never
  included.
- Neither prompt mentioned the other condition, mentioned that this is an
  experiment, explained what Credential Scrubber is, explained what the
  placeholder tokens mean, or stated that any value had been removed or
  replaced.

## Settings

| Setting | Value |
|---|---|
| Temperature | Not independently controllable via the available tooling (the Agent tool exposes no temperature parameter) — not overridden for either condition, so the platform default applied identically to both. |
| Max output tokens | Not independently controllable via the available tooling; no explicit limit was set for either condition. |
| Conversation history | None — each condition was a single fresh Agent tool invocation with no prior turns and no shared context. |
| Sampling | One call per condition, no repeated sampling. |

## Execution date

2026-09-20T13:44:47Z (UTC) — both conditions launched as two parallel
tool invocations within the same short window.

## Raw response files

| Condition | File |
|---|---|
| A — original | `ai-evaluation/pilot-002/results/original_explain_config_relationships.txt` |
| B — sanitized | `ai-evaluation/pilot-002/results/sanitized_explain_config_relationships.txt` |

Both are the complete, unedited response text returned by each
invocation — no trimming, reformatting, or correction applied.

## Procedural problems / limitations encountered

1. **Same tooling limitation as Pilot 001:** no raw model API access is
   available; the closest available approximation to "a fresh AI-agent
   conversation" is a Claude Code subagent, which carries its own
   agent-type system-level framing in addition to the task prompt. Held
   identical across both conditions (same subagent type, no override), so
   it should not itself differentiate the two responses, but it is not a
   bare, system-prompt-free API call.
2. **Temperature and max-output-tokens are not independently settable**
   through this tooling (see "Settings" above).
3. **Model-id confirmation is inherited, not independently re-verified
   per call** — same limitation as Pilot 001's execution record.
4. No other procedural issues encountered — both calls completed
   successfully, used zero tool calls, and returned complete responses
   in the requested "short list of groups" format.

## What this file deliberately does not contain

No quality assessment, no comparison of which response is "better," no
rubric scores, and no conclusion about whether sanitization helped or
hurt in this case. `human_evaluation.md` for Pilot 002 has not been
created — scoring is a separate, later step.
