# Task: Explain configuration relationships

**Purpose:** the task most directly aimed at this project's actual
differentiation claim (per the earlier competitive-landscape audit): can
an AI still reason about how config values *relate to each other*
(which host goes with which credential, which values belong to the same
logical group) when the values themselves are placeholders? This is
where blanket masking (every value becomes the same `***REDACTED***`)
would be expected to fail hardest, and where typed, stable placeholders
are specifically hypothesized to help.

**Scope:** config files only (`.json`, `.yaml`, `.properties`, `.xml`,
`.env`, `.config`) - not run against source-code files.

**Rubric dimensions this task primarily exercises:** correctness,
completeness, whether relationships between values were preserved.

## Template

```
The following is a {{FILE_EXTENSION}} configuration file. Explain how
its settings relate to each other - for example, which values appear to
belong to the same logical group (such as a single service's connection
details), and which values look independent of each other.

Respond as a short list of groups you identify, each with:
- The settings you believe belong together, and why.
- What that group appears to configure.

If a setting doesn't seem to belong to any group, list it separately
rather than forcing it into one.

Configuration:

{{SOURCE_CODE}}
```

## Notes

- The proposed `appsettings.json` candidate (see `dataset/README.md`)
  is the clearest test of this: `Database.Host`, `Database.Username`,
  and `Database.Password` are already nested under one object in the
  original file, so this task is partly about whether that grouping
  survives sanitization structurally (dimension C) *and* whether the
  model still narrates it correctly in prose (this task).
- A response that treats two *different* placeholder values as if they
  were part of the same group when the real values wouldn't be (or vice
  versa) is exactly the "relationships between values" failure mode this
  task and its rubric dimension exist to catch.
