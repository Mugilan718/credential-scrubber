# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning
follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

Nothing yet.

## [2.0.0] - 2026-10-03

A major version bump: this release removes an API route a prior version
shipped (`POST /api/projects/<id>/scan`, replaced by the preview/apply
flow below), and several of the security fixes change the exact output a
scan produces for previously-mishandled input. Neither is a drop-in
compatible change for anything built directly against the old route or
depending on the old (incorrect) redaction output, which is why this is
`2.0.0` rather than a minor/patch release.

### Added

- **Preview-before-write scanning.** "Run scan" now computes and shows
  everything a scan would find and write - including which already-
  ignored findings would be written back UNREDACTED - without touching
  the output folder. A separate "Apply to output folder" step writes it,
  and is refused by the server (not just hidden in the UI) if an ignore,
  the folder-filter selection, or the rules changed since that preview
  was computed.
- **Per-project folder-filtering tree.** When adding a project (or later
  via "Edit folders"), an expandable checkbox tree lets you choose which
  subfolders/files are included in every scan of that project. Stored
  with the project, so it survives app restarts.
- **Ignore confirmation + revert.** Ignoring a finding now requires an
  explicit confirmation, since it restores the real value into the next
  scan's output. Already-ignored findings can be restored (re-redacted)
  at any time from the Ignored Findings view.
- **"Re-scan now" labeling.** The scan button relabels itself once a
  project has at least one applied scan on record, making explicit that
  re-scanning always reads fresh from disk (it always did; this just
  stopped leaving that implicit).
- **Deterministic semantic placeholder mode** in the detection engine
  (`PlaceholderRegistry`): an opt-in redaction mode that replaces a
  secret with a typed, numbered placeholder (e.g. `<API_KEY_1>`) instead
  of one shared mask, with the same real value always producing the same
  token within a scan. Evaluated in a new research track (see below);
  not yet exposed through the desktop app's own UI.
- **AI-agent evaluation research track** (`ai-evaluation/`): a documented
  9-file/6-task experiment assessing whether an AI coding agent can still
  do useful work on sanitized (placeholder-mode) source, plus its
  analysis, figures, and methodology notes. Research findings, not a
  product claim - see the README's "What the experiment does NOT
  establish" section for explicit scope limits.
- **Benchmark suite** (`benchmark/`, `run_benchmark.py`, `BENCHMARK.md`):
  a synthetic, ground-truth-labeled detection/sanitization/syntax/
  performance benchmark with a CLI runner.
- **GNU AGPLv3 license**, applied going forward (not retroactively).
- **"Verifying your download" documentation**: explains the expected
  "unrecognized publisher" warning on the unsigned `.exe` release and how
  to verify its SHA-256 checksum against the value published in that
  release's GitHub Releases notes.
- **`CONTRIBUTING.md` and `SECURITY.md`.**

### Changed

- `engine.scan_project()` is now a thin wrapper around a staged
  "compute, then write" pair (`stage_project()` / `apply_staged_project()`)
  - same public signature and immediate-write behavior for existing
    callers, but the underlying implementation now supports previewing
    a scan's result before anything is written.
- Removed the overly broad `username`/`port` key-name patterns from
  `rules_default.yaml` - these were flagging ordinary, non-secret
  configuration values.

### Fixed

Security-relevant fixes from an internal audit (tracked as F1-F4):

- **F1** - JSON/XML/`.config` key extraction missed some real key/value
  pairs due to line-based, not boundary-aware, matching.
- **F2** - A finding whose key and value shared overlapping text could
  have its redaction mask applied to the wrong span, redacting the key
  instead of (or in addition to) the value.
- **F3** - Raw secret values were being persisted into the scan-history
  database. They're now kept only in an in-memory, size-bounded cache,
  never written to disk.
- **F4** - Symlinks were followed/read during a scan rather than being
  skipped, risking reading content from outside the intended project
  tree (e.g. a symlink pointing into `~/.ssh`).
- Redaction could produce invalid YAML for an unquoted scalar value (a
  bare `***REDACTED***` can collide with YAML's alias syntax) or corrupt
  a block-scalar header; redaction is now YAML-safe.

### Removed

- `POST /api/projects/<id>/scan` - replaced by
  `POST /api/projects/<id>/preview` followed by
  `POST /api/projects/<id>/apply` (see "Added" above). Anything calling
  the old route directly needs to switch to the two-step flow.

[Unreleased]: https://github.com/Mugilan718/credential-scrubber/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/Mugilan718/credential-scrubber/compare/v1.0.0...v2.0.0
