"""
report.py - renders the benchmark results dict (built by run_benchmark.py)
as a human-readable text report. The JSON report is just json.dump()'d
directly by run_benchmark.py - this module only formats the text one.
"""


def _pct(x):
    return "n/a" if x is None else f"{x * 100:.1f}%"


def _fmt_metrics_block(m, indent="  "):
    lines = [
        f"{indent}Precision: {_pct(m['precision'])}",
        f"{indent}Recall: {_pct(m['recall'])}",
        f"{indent}F1: {_pct(m['f1'])}",
        f"{indent}False positive rate: {_pct(m['false_positive_rate'])}",
        f"{indent}TP={m['true_positives']}  FP={m['false_positives']}  "
        f"FN={m['false_negatives']}  TN={m['true_negatives']}",
    ]
    return "\n".join(lines)


def render_text_report(results):
    d = results["dataset"]
    det = results["detection"]
    san = results["sanitization"]
    syn = results["syntax"]
    perf = results["performance"]

    lines = []
    lines.append("Credential Scrubber Benchmark")
    lines.append("=" * 30)
    lines.append("")
    lines.append("Dataset:")
    lines.append(f"  Cases: {d['case_count']}")
    lines.append(f"  Languages: {', '.join(d['languages'])}")
    lines.append(f"  File types: {', '.join(d['file_types'])}")
    lines.append(f"  Files: {d['file_count']}")
    lines.append("")
    lines.append("Detection")
    lines.append("-" * 9)
    lines.append(_fmt_metrics_block(det["overall"]))
    if det["unexpected_findings"]:
        lines.append(f"  Unexpected findings (no ground truth at that file/line): {len(det['unexpected_findings'])}")
        for uf in det["unexpected_findings"][:10]:
            lines.append(f"    - {uf['file']}:{uf['line']} rule={uf['rule']} key={uf['key']}")
    lines.append("")
    lines.append("  By language:")
    for lang, m in det["by_language"].items():
        lines.append(f"    {lang} (n={m['case_count']}): P={_pct(m['precision'])} R={_pct(m['recall'])} F1={_pct(m['f1'])}")
    lines.append("  By file type:")
    for ft, m in det["by_file_type"].items():
        lines.append(f"    {ft} (n={m['case_count']}): P={_pct(m['precision'])} R={_pct(m['recall'])} F1={_pct(m['f1'])}")
    lines.append("  By category:")
    for cat, m in det["by_category"].items():
        lines.append(f"    {cat} (n={m['case_count']}): P={_pct(m['precision'])} R={_pct(m['recall'])} F1={_pct(m['f1'])}")
    lines.append("")
    lines.append("Sanitization")
    lines.append("-" * 12)
    lines.append(f"  Findings checked: {san['findings_checked']}")
    lines.append(f"  Successfully sanitized: {san['successfully_sanitized']}")
    lines.append(f"  Sanitization failures (wrong span/incomplete): {san['sanitization_failures']}")
    lines.append(f"  Original secret leakage (CRITICAL): {san['leakage_failures']}")
    lines.append(f"  Placeholder-consistency failures: {san['placeholder_consistency_failures']}")
    lines.append(f"  Placeholder-distinctness (informational, not a failure - see limitations): "
                 f"{san['placeholder_distinctness_note']}")
    if san["leakage_details"]:
        lines.append("  Leakage details:")
        for ld in san["leakage_details"]:
            lines.append(f"    - {ld['file']}:{ld['line']} rule={ld['rule']}")
    lines.append("")
    lines.append("Syntax")
    lines.append("-" * 6)
    lines.append(f"  Real-parser valid: {syn['real_valid']}")
    lines.append(f"  Real-parser invalid: {syn['real_invalid']}")
    lines.append(f"  Heuristic valid (java/js/ts/go/csharp - see limitations): {syn['heuristic_valid']}")
    lines.append(f"  Heuristic invalid: {syn['heuristic_invalid']}")
    lines.append(f"  Not applicable (.properties/.env/etc.): {syn['not_applicable']}")
    if syn["invalid_details"]:
        lines.append("  Invalid files:")
        for inv in syn["invalid_details"]:
            lines.append(f"    - {inv['file']}: {inv['detail']}")
    lines.append("")
    lines.append("Performance")
    lines.append("-" * 11)
    lines.append(f"  Files: {perf['files_scanned']}")
    lines.append(f"  Bytes: {perf['total_bytes']}")
    lines.append(f"  Time: {perf['total_seconds']:.4f}s")
    lines.append(f"  Files/sec: {perf['files_per_second']:.1f}")
    lines.append(f"  MB/sec: {perf['mb_per_second']:.3f}")
    if perf.get("peak_rss_mb") is not None:
        lines.append(f"  Peak RSS: {perf['peak_rss_mb']:.1f} MB")
    lines.append("")
    return "\n".join(lines)


def render_placeholder_report(results):
    """Renders run_placeholder_benchmark()'s results - additive, separate
    from render_text_report() above; the normal benchmark's report format
    is unchanged by this function's existence."""
    det = results["detection_overall"]
    lines = []
    lines.append("")
    lines.append("Credential Scrubber Benchmark - Placeholder Mode")
    lines.append("=" * 49)
    lines.append("")
    lines.append("Detection (cross-check - expected identical to the normal benchmark,")
    lines.append("since placeholder_mode only changes replacement text, not detection):")
    lines.append(_fmt_metrics_block(det))
    lines.append("")
    lines.append(f"Findings checked: {results['findings_checked']}")
    lines.append("")
    lines.append("Original secret leakage (CRITICAL): " + str(results["leakage_failures"]))
    if results["leakage_details"]:
        for ld in results["leakage_details"]:
            lines.append(f"  - {ld['file']}:{ld['line']} rule={ld['rule']}")
    lines.append("")
    lines.append(f"Placeholder consistency failures (same value_group, different tokens): {results['placeholder_consistency_failures']}")
    for cd in results["placeholder_consistency_details"]:
        lines.append(f"  - value_group={cd['value_group']} tokens={cd['distinct_tokens']}")
    lines.append("")
    lines.append(f"Placeholder distinctness failures (different values sharing one token): {results['placeholder_distinctness_failures']}")
    for dd in results["placeholder_distinctness_details"]:
        lines.append(f"  - category={dd['category']} token={dd['token']} colliding_values={dd['colliding_values']}")
    lines.append("")
    lines.append(f"Syntax failures (placeholder token broke the file's own format): {results['syntax_failures']}")
    lines.append(f"  Real-parser valid: {results['syntax_valid']}  invalid: {results['syntax_invalid']}")
    lines.append(f"  Heuristic valid: {results['syntax_heuristic_valid']}  invalid: {results['syntax_heuristic_invalid']}")
    lines.append(f"  Not applicable: {results['syntax_not_applicable']}")
    for sd in results["syntax_invalid_details"]:
        lines.append(f"  - {sd['file']}: {sd['detail']}")
    lines.append("")
    lines.append(f"Deterministic report entries across repeated scans: {results['deterministic_entries']}")
    lines.append(f"Deterministic output files across repeated scans: {results['deterministic_files']}")
    if results["file_mismatches"]:
        lines.append(f"  Mismatched files: {results['file_mismatches']}")
    lines.append("")
    lines.append(f"Files scanned: {results['files_scanned']}  Time: {results['total_seconds']:.4f}s")
    lines.append("")
    return "\n".join(lines)
