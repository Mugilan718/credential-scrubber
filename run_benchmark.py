#!/usr/bin/env python3
"""
run_benchmark.py - Credential Scrubber detection/sanitization benchmark.

Runs the current engine.py against the synthetic dataset in
benchmark/dataset/, compares its findings against the hand-authored
ground truth in benchmark/dataset/cases.jsonl, and reports detection
metrics, sanitization correctness (including the critical "did the
original secret leak" check), lightweight syntax preservation, and
performance - all computed from an actual run, never hand-entered.

Usage:
    python run_benchmark.py [--output-dir DIR] [--json-out FILE] [--quiet]

See BENCHMARK.md for the dataset format, what each metric means, and this
benchmark's known limitations.
"""
import argparse
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import engine
from benchmark import metrics, report
from benchmark.dataset_loader import CASES_PATH, FILES_DIR, load_cases
from benchmark.memory import get_peak_rss_mb
from benchmark.syntax_check import check_syntax

RULES_PATH = Path(__file__).resolve().parent / "rules_default.yaml"


def _norm(path_str):
    return path_str.replace("\\", "/")


def run(output_dir=None, json_out=None, quiet=False):
    cases = load_cases(CASES_PATH)
    rules = engine.load_rules(RULES_PATH)

    cleanup_output = output_dir is None
    output_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="cs_benchmark_out_"))

    total_bytes = sum(p.stat().st_size for p in FILES_DIR.rglob("*") if p.is_file())

    start = time.perf_counter()
    report_entries, files_scanned, files_skipped = engine.scan_project(FILES_DIR, output_dir, rules)
    elapsed = time.perf_counter() - start
    peak_rss_mb = get_peak_rss_mb()

    entries_by_key = {}
    for e in report_entries:
        key = (_norm(e["file"]), e["line"])
        entries_by_key.setdefault(key, []).append(e)
    detected_keys = set(entries_by_key.keys())

    # ---- detection metrics ----
    for case in cases:
        case["file"] = _norm(case["file"])
    counts = metrics.confusion_counts(cases, detected_keys)
    overall = metrics.precision_recall_f1(counts)

    known_case_keys = {(c["file"], c["line"]) for c in cases}
    unexpected_findings = [
        {"file": f, "line": l, "rule": e["rule"], "key": e.get("key")}
        for (f, l), es in entries_by_key.items() if (f, l) not in known_case_keys
        for e in es
    ]

    detection = {
        "overall": overall,
        "by_language": metrics.metrics_by_group(cases, "language"),
        "by_file_type": metrics.metrics_by_group(cases, "file_type"),
        "by_category": metrics.metrics_by_group(cases, "category"),
        "unexpected_findings": unexpected_findings,
    }

    # ---- sanitization correctness ----
    findings_checked = 0
    successfully_sanitized = 0
    sanitization_failures = 0
    leakage_failures = 0
    leakage_details = []
    placeholder_consistency_failures = 0

    sanitized_text_cache = {}

    def _sanitized_text(rel_file):
        if rel_file not in sanitized_text_cache:
            out_path = output_dir / rel_file
            sanitized_text_cache[rel_file] = out_path.read_text(encoding="utf-8") if out_path.exists() else None
        return sanitized_text_cache[rel_file]

    for case in cases:
        if not case["expected_detection"] or case["outcome"] != "TP":
            continue
        findings_checked += 1
        key = (case["file"], case["line"])
        matched_entries = entries_by_key.get(key, [])
        text = _sanitized_text(case["file"])
        ok = False
        if text is not None:
            out_lines = text.split("\n")
            out_line = out_lines[case["line"] - 1] if 0 < case["line"] <= len(out_lines) else ""
            if case["expected_output_line"] is not None:
                ok = out_line.strip("\r") == case["expected_output_line"]
            else:
                before_texts = [e["before"] for e in matched_entries]
                ok = all(bt not in out_line for bt in before_texts)
            # Whole-file leak check for distinctive (long) original values,
            # independent of the expected_output_line check above - catches
            # a leak that landed on an unexpected line/file. Excludes this
            # case's own line when expected_output_line already verified it
            # byte-for-byte, since a coincidental match there (e.g. the
            # value's text also appearing in its own key name, as in the
            # same-substring edge cases) is not a leak - only a value
            # appearing somewhere it precisely was NOT expected is.
            if case["original_value"] and len(case["original_value"]) >= 8:
                if case["expected_output_line"] is not None and out_line.strip("\r") == case["expected_output_line"]:
                    search_space = "\n".join(l for i, l in enumerate(out_lines, start=1) if i != case["line"])
                else:
                    search_space = text
                if case["original_value"] in search_space:
                    ok = False
                    leakage_failures += 1
                    leakage_details.append({"file": case["file"], "line": case["line"], "rule": matched_entries[0]["rule"] if matched_entries else "?"})
        if ok:
            successfully_sanitized += 1
        else:
            sanitization_failures += 1

    # Placeholder consistency: same value_group -> same "after" token today.
    groups = {}
    for case in cases:
        if not case["value_group"] or case["outcome"] != "TP":
            continue
        groups.setdefault(case["value_group"], []).append(case)
    distinct_after_tokens = set()
    for group_id, group_cases in groups.items():
        afters = set()
        for c in group_cases:
            for e in entries_by_key.get((c["file"], c["line"]), []):
                afters.add(e["after"])
        distinct_after_tokens.add(frozenset(afters))
        if len(afters) > 1:
            placeholder_consistency_failures += 1

    sanitization = {
        "findings_checked": findings_checked,
        "successfully_sanitized": successfully_sanitized,
        "sanitization_failures": sanitization_failures,
        "leakage_failures": leakage_failures,
        "leakage_details": leakage_details,
        "placeholder_consistency_failures": placeholder_consistency_failures,
        "placeholder_distinctness_note": (
            "current engine uses one shared mask for every finding - distinct "
            "value_groups are not expected to get distinct tokens yet (typed/"
            "stable placeholders are a later phase, see BENCHMARK.md)"
        ),
    }

    # ---- syntax preservation on the sanitized output ----
    syntax_counts = {"valid": 0, "invalid": 0, "heuristic_valid": 0, "heuristic_invalid": 0, "not_applicable": 0}
    invalid_details = []
    for src in FILES_DIR.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(FILES_DIR).as_posix()
        out_path = output_dir / rel
        if not out_path.exists():
            continue
        text = out_path.read_text(encoding="utf-8")
        status, detail = check_syntax(src.suffix, text)
        syntax_counts[status] += 1
        if status in ("invalid", "heuristic_invalid"):
            invalid_details.append({"file": rel, "detail": detail})

    syntax = {
        "real_valid": syntax_counts["valid"],
        "real_invalid": syntax_counts["invalid"],
        "heuristic_valid": syntax_counts["heuristic_valid"],
        "heuristic_invalid": syntax_counts["heuristic_invalid"],
        "not_applicable": syntax_counts["not_applicable"],
        "invalid_details": invalid_details,
    }

    # ---- performance ----
    performance = {
        "files_scanned": files_scanned,
        "files_skipped": len(files_skipped),
        "total_bytes": total_bytes,
        "total_seconds": elapsed,
        "files_per_second": (files_scanned / elapsed) if elapsed > 0 else float("inf"),
        "mb_per_second": (total_bytes / (1024 * 1024) / elapsed) if elapsed > 0 else float("inf"),
        "peak_rss_mb": peak_rss_mb,
    }

    dataset = {
        "case_count": len(cases),
        "file_count": sum(1 for p in FILES_DIR.rglob("*") if p.is_file()),
        "languages": sorted({c["language"] for c in cases}),
        "file_types": sorted({c["file_type"] for c in cases}),
    }

    results = {
        "dataset": dataset,
        "detection": detection,
        "sanitization": sanitization,
        "syntax": syntax,
        "performance": performance,
        "cases": cases,
    }

    if cleanup_output:
        shutil.rmtree(output_dir, ignore_errors=True)

    if json_out:
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

    text_report = report.render_text_report(results)
    if not quiet:
        print(text_report)

    return results, text_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", help="Where to write the sanitized dataset copy (default: a temp dir, cleaned up after).")
    parser.add_argument("--json-out", help="Write the full machine-readable results as JSON to this path.")
    parser.add_argument("--quiet", action="store_true", help="Suppress the human-readable report on stdout.")
    args = parser.parse_args()

    results, _ = run(output_dir=args.output_dir, json_out=args.json_out, quiet=args.quiet)

    critical = results["sanitization"]["leakage_failures"]
    if critical:
        print(f"\nCRITICAL: {critical} original secret(s) leaked into sanitized output.", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
