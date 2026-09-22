# Research figures

Four research figures generated from the completed, frozen AI-evaluation
experiment's scored data. This file documents what each figure shows,
where its data comes from, and exactly how to regenerate all four.

## Purpose

These are descriptive visualizations of the already-completed human
evaluation and statistical analysis - no new statistic, test, score, or
conclusion is introduced by the figures or by this document. They exist
to make the paired Original-vs-Sanitized comparison (§2 of
`../inferential_results.md`) visually inspectable alongside its numeric
report.

## Source datasets

Both are one directory up from this file (`ai-evaluation/experiment/analysis/`):

- `../evaluation_dataset.csv` - all 96 scored responses (48 Original, 48
  Sanitized), one row per response.
- `../paired_deltas.csv` - the 48 paired (Sanitized − Original) score
  differences derived from `evaluation_dataset.csv`, one row per
  applicable (file, task) pair.

Neither file is modified by figure generation. The generator
independently re-derives the paired deltas from `evaluation_dataset.csv`
and cross-checks them against `paired_deltas.csv` before drawing
anything - see "Reproduction" below.

## Generator

`../generate_figures.py`

## Reproduction

Run from the repository root (the script itself resolves the dataset and
output paths internally, so it also works from any other working
directory on the machine it was written for - see the portability note
below):

```
python ai-evaluation/experiment/analysis/generate_figures.py
```

This single command regenerates all four PNGs listed below, overwriting
them in place. The script performs its own validation before drawing
anything (96/48/48 row counts, independently-recomputed deltas matched
exactly against `paired_deltas.csv`, and failure-mode tag counts
cross-checked against the documented reference counts in
`../descriptive_results.md`/`../inferential_results.md`) and will raise
an error rather than silently proceed if any of those checks fail.

**Portability note:** as written, `generate_figures.py` resolves its
input/output paths from a hardcoded absolute path
(`D:\New-credential-scrubber\credential-scrubber-app`), not from the
script's own location or the current working directory. The command
above works correctly on the machine this experiment was run on,
regardless of which directory you run it from, but the script would need
that constant updated (or converted to a relative/`pathlib`-based path)
before it would run correctly from a different clone location. This is
stated here rather than silently worked around, since the script itself
is one of the frozen research artifacts this cleanup does not modify.

## Figures

### 1. `primary_score_distributions.png`

Original vs. Sanitized score distributions for the four always-scored
rubric dimensions (Correctness, Completeness, Consistency, Usefulness),
N=48 per condition per dimension. Each individual response is drawn as
one dot; dots are laid out in a fixed deterministic grid at each integer
score (1-5) rather than averaged, so the ordinal, heavily-concentrated
nature of the scores stays visible instead of being smoothed away.

### 2. `paired_delta_distributions.png`

The paired (Sanitized − Original) score difference for all 48 pairs, per
dimension. Zero is drawn as a heavy reference line, and the count of
unchanged pairs is stated directly in each dimension's axis label (e.g.
"Usefulness (41/48 pairs unchanged)"), since the large zero-difference
majority is itself part of what this figure needs to communicate
accurately - it is not hidden or trimmed out.

### 3. `task_level_paired_deltas.png`

The same paired differences as figure 2, faceted into one panel per task
(`explain_code`, `identify_bug`, `security_analysis`,
`generate_unit_tests`, `suggest_refactoring`,
`explain_config_relationships`), in the order the experiment manifest
defines them - not sorted or ranked by observed effect. Each panel's
title states its actual N; `explain_config_relationships` is N=3 (only
the 3 configuration-shaped files), and its title states explicitly that
the other 6 (source-code) files are not applicable to that task, rather
than treating their absence as a zero difference.

### 4. `failure_mode_frequency.png`

Observed counts of every failure-mode tag recorded during human
evaluation (`evaluation_dataset.csv`'s `failure_modes` column),
including categories with a count of zero, grouped into
sanitization-related, sanitization-independent, and
environmental/protocol categories. One recorded tag
(`inferred_placeholder_value`) does not correspond to any of the six
named sanitization-related categories the underlying rubric checklist
enumerates and is shown as its own, separately-labeled bar rather than
folded into a similar-sounding category.

## Reproducibility

Recorded from the actual environment the figures were generated in
(confirmed by running `generate_figures.py`, which prints these versions
on every run):

- **Python:** 3.14.7
- **matplotlib:** 3.11.2
- **numpy:** 2.5.3

**Determinism:** no random jitter or randomized positioning is used
anywhere in `generate_figures.py`. Every place multiple observations
would otherwise overlap (repeated integer scores, repeated delta values)
is rendered with a fixed, deterministic dot-grid layout (row/column
position computed directly from an index, not from any random draw) -
see the script's own module docstring. A `RANDOM_SEED = 42` constant is
still defined in the script per this project's general reproducibility
convention, but no code path in `generate_figures.py` actually consumes
it, since none of its rendering needs randomness to begin with. Re-running
the script produces byte-identical PNG output - confirmed by hashing all
four files, re-running, and hashing again.

## Dependencies

`generate_figures.py` requires `matplotlib` and `numpy`. See
`ai-evaluation/requirements-research.txt` at the repository root of this
research track, and install with:

```
pip install -r ai-evaluation/requirements-research.txt
```

These are research-analysis dependencies only - they are intentionally
not part of the main application's `requirements.txt`/`requirements-dev.txt`,
since the desktop scanner app does not use them.
