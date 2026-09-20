"""
dataset_loader.py - loads the benchmark's ground-truth cases from
dataset/cases.jsonl.

Ground truth is intentionally NOT compiled into the detection engine in
any way - it is only ever compared against what engine.py produces.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATASET_DIR = HERE / "dataset"
FILES_DIR = DATASET_DIR / "files"
CASES_PATH = DATASET_DIR / "cases.jsonl"

REQUIRED_FIELDS = ("id", "file", "language", "file_type", "category", "expected_detection")


def load_cases(path=CASES_PATH):
    cases = []
    seen_ids = set()
    with open(path, "r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, start=1):
            raw = raw.strip()
            if not raw or raw.startswith("#"):
                continue
            try:
                case = json.loads(raw)
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{line_no}: invalid JSON - {e}") from e
            missing = [field for field in REQUIRED_FIELDS if field not in case]
            if missing:
                raise ValueError(f"{path}:{line_no}: case {case.get('id', '?')!r} missing fields {missing}")
            if case["id"] in seen_ids:
                raise ValueError(f"{path}:{line_no}: duplicate case id {case['id']!r}")
            seen_ids.add(case["id"])
            case.setdefault("line", None)
            case.setdefault("expected_sanitization", case["expected_detection"])
            case.setdefault("expected_placeholder_category", None)
            case.setdefault("value_group", None)
            case.setdefault("original_value", None)
            case.setdefault("expected_output_line", None)
            case.setdefault("notes", "")
            cases.append(case)
    return cases


def dataset_files():
    """All files under dataset/files, as POSIX-style paths relative to it -
    matching the relative paths engine.scan_project() reports findings
    against."""
    return sorted(
        p.relative_to(FILES_DIR).as_posix()
        for p in FILES_DIR.rglob("*")
        if p.is_file()
    )
