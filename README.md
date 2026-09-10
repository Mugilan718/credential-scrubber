# Credential Scrubber - Local App

A local web app (runs entirely on your own machine) for scanning projects for
hardcoded credentials and secrets, with project management, a visual rule
editor, and scan history. Built on top of the same detection engine as the
original CLI tool, with all the fixes found during testing built in:
multi-line concatenation detection (Python and Java/JS/C# styles), and
key-name matches always redacting regardless of placeholder values.

## Nothing leaves your machine

- The scan engine runs locally against your file system.
- Project list, rules, and scan history are stored in a local SQLite file
  (`data/app.db`).
- The "safe" report (shown by default) never contains raw secret values -
  only file, line, rule, and key name.
- The "sensitive" before/after view is only loaded when you explicitly click
  "Reveal original values," and is clearly marked as sensitive.
- There is no cloud sync, no accounts, no telemetry.

## Install & run

**Windows:**
```
run.bat
```

**Mac/Linux:**
```
chmod +x run.sh
./run.sh
```

Either script installs the two dependencies (`flask`, `pyyaml`) and starts
the app, which opens automatically at `http://127.0.0.1:5057`.

If you'd rather run it manually:
```
pip install -r requirements.txt
python app.py
```

## Using the app

1. **Add a project** - give it a name, the folder to scan, and where to write
   the sanitized copy. The original folder is never modified.
2. **Edit rules** (optional) - adjust key names and placeholder allow-list
   per project without touching any files by hand.
3. **Run scan** - see a live count of files scanned and redactions made.
4. **Review results** - browse what was caught, by file/line/rule. Click
   "Reveal original values" only if you need to double-check a specific
   finding - this shows real secret values, so treat that view as sensitive.
5. **Scan history** - every run is saved per project, so you can track
   redaction counts over time and re-open past reports.

## Architecture

```
app.py        Flask server + REST API
engine.py     Core scanning logic (importable, no CLI dependency)
db.py         Local SQLite storage for projects and scan history
rules_default.yaml   Starting rule set for new projects
templates/    HTML
static/       CSS + JS frontend
data/         SQLite database lives here (gitignored if you add version control)
```

## Extending detection rules

Each project has its own copy of the rules (editable via the UI), starting
from `rules_default.yaml`. The visual editor currently covers key names and
the placeholder allow-list; value-pattern regexes and code-pattern regexes
are preserved from the defaults but not yet editable in the UI - edit
`rules_default.yaml` before creating a project if you need to change those.

## Known limitations

- Regex-based detection, not a full code parser - creatively obfuscated
  secrets can still slip through.
- Multi-line concatenation detection currently covers Python's parenthesized
  style and Java/JS/C#'s `+`-operator style (both "trailing +" and "leading
  +" conventions). Other multi-line patterns (e.g. JS template literals
  spanning multiple lines) are not yet covered.
- This is a single-user local tool, not a multi-tenant product - each person
  runs their own copy against their own machine.
- If a real secret is found, rotate it. Masking it for AI/sharing purposes
  does not undo prior exposure.
