"""
metrics.py - precision/recall/F1/false-positive-rate computation from a
confusion count, plus grouping helpers. No numbers here are hardcoded;
everything is derived from whatever counts the caller passes in, which in
turn come only from actually running the engine (see run_benchmark.py).
"""
from collections import defaultdict


def confusion_counts(cases, detected_keys):
    """cases: list of ground-truth case dicts, each with a resolved
    ("file", "line") location and expected_detection.
    detected_keys: set of (file, line) tuples the engine actually flagged.

    Returns per-case outcome ("TP"/"FP"/"FN"/"TN") added under case["outcome"],
    and the aggregate counts dict.
    """
    counts = defaultdict(int)
    for case in cases:
        key = (case["file"], case["line"])
        detected = key in detected_keys
        if case["expected_detection"] and detected:
            outcome = "TP"
        elif case["expected_detection"] and not detected:
            outcome = "FN"
        elif not case["expected_detection"] and detected:
            outcome = "FP"
        else:
            outcome = "TN"
        case["outcome"] = outcome
        counts[outcome] += 1
    return dict(counts)


def precision_recall_f1(counts):
    tp = counts.get("TP", 0)
    fp = counts.get("FP", 0)
    fn = counts.get("FN", 0)
    tn = counts.get("TN", 0)
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    f1 = (2 * precision * recall / (precision + recall)) if (precision and recall and (precision + recall) > 0) else None
    fpr = fp / (fp + tn) if (fp + tn) else None
    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": fpr,
    }


def group_by(cases, field):
    groups = defaultdict(list)
    for case in cases:
        groups[case.get(field) or "(unspecified)"].append(case)
    return dict(groups)


def metrics_by_group(cases, field):
    """Requires confusion_counts() to have already run once over the full
    case list (so every case already has an "outcome"); this just
    re-aggregates those existing per-case outcomes by `field`, rather than
    re-matching anything against the engine."""
    result = {}
    for key, group_cases in sorted(group_by(cases, field).items()):
        agg = defaultdict(int)
        for c in group_cases:
            agg[c["outcome"]] += 1
        result[key] = precision_recall_f1(agg)
        result[key]["case_count"] = len(group_cases)
    return result
