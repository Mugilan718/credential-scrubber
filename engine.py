"""
engine.py - Core credential-scanning engine.

Refactored from the original scrub.py CLI tool into an importable module,
with all fixes discovered during testing incorporated:
  - key_patterns always redact regardless of placeholder allow-list
  - placeholder allow-list only suppresses value_pattern/entropy matches
  - multi-line Python parenthesized string concatenation
  - multi-line Java/JS/C# "+"-operator string concatenation

Design principle unchanged: never modifies original files. Always writes
to a separate output directory.
"""

import json
import math
import os
import re
import shutil
from pathlib import Path

import yaml

MASK = "***REDACTED***"

CONFIG_EXTENSIONS = {".properties", ".yml", ".yaml", ".json", ".xml", ".ini", ".conf", ".cfg"}
CODE_EXTENSIONS = {
    ".java": "java", ".py": "python",
    ".js": "javascript", ".jsx": "javascript", ".ts": "javascript", ".tsx": "javascript",
    ".go": "go", ".cs": "csharp",
}
CONFIG_FILENAMES = {".env"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "target", "dist", "build", ".idea", ".vscode"}

PLUS_CONCAT_LANGS = {"java", "javascript", "csharp"}


def classify_file(path: Path):
    if path.name in CONFIG_FILENAMES or path.name.startswith(".env."):
        return "config"
    ext = path.suffix.lower()
    if ext in CONFIG_EXTENSIONS:
        return "config"
    if ext in CODE_EXTENSIONS:
        return f"code:{CODE_EXTENSIONS[ext]}"
    return None


def load_rules(rules_path):
    with open(rules_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return {
        "key_patterns": [re.compile(p, re.IGNORECASE) for p in raw.get("key_patterns", [])],
        "value_patterns": [(vp["name"], re.compile(vp["regex"], re.IGNORECASE)) for vp in raw.get("value_patterns", [])],
        "code_patterns": {lang: [re.compile(p) for p in pats] for lang, pats in raw.get("code_patterns", {}).items()},
        "placeholder_allowlist": {s.lower() for s in raw.get("placeholder_allowlist", [])},
    }


def is_placeholder(value, allowlist):
    v = value.strip().strip('"').strip("'").lower()
    return v in allowlist


def shannon_entropy(s):
    if not s:
        return 0.0
    freq = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    length = len(s)
    return -sum((c / length) * math.log2(c / length) for c in freq.values())


def looks_high_entropy(value, min_length=20, min_entropy=3.5):
    v = value.strip().strip('"').strip("'")
    if len(v) < min_length:
        return False
    if re.fullmatch(r"[A-Za-z\s]+", v):
        return False
    return shannon_entropy(v) >= min_entropy


def find_key_value(line):
    m = re.match(r'^\s*([A-Za-z0-9_.\-\[\]]+)\s*[:=]\s*(.*)$', line)
    if not m:
        return None, None
    return m.group(1), m.group(2)


def quoted_mask(value):
    """Mask a config value, preserving its surrounding quote character (if any).

    `value` is the raw text captured after 'key:'/'key=', which still includes
    any quotes the author wrote (e.g. `"secret"`). Replacing that whole span
    with the bare MASK would silently strip the quotes; wrapping the MASK in
    the same quote char keeps the redacted line's quoting style unchanged.
    """
    v = value.rstrip()
    if len(v) >= 2 and v[0] in ('"', "'") and v[-1] == v[0]:
        return v[0] + MASK + v[0]
    return MASK


def redact_config_line(line, rules, report_entries, filename, line_no):
    key, value = find_key_value(line)
    if key is None:
        return redact_value_patterns_only(line, rules, report_entries, filename, line_no)

    if value.strip() == "":
        return line

    key_matched = any(p.search(key) for p in rules["key_patterns"])

    # Key-name match ALWAYS redacts, placeholder allow-list does not apply here.
    if key_matched:
        replacement = quoted_mask(value)
        report_entries.append({"file": filename, "line": line_no, "key": key, "rule": "key_name_match",
                                "before": value, "after": replacement})
        new_line = line.replace(value, replacement, 1) if value in line else f"{key}={replacement}"
        return new_line

    if is_placeholder(value, rules["placeholder_allowlist"]):
        return line

    value_matched_name = None
    for name, pattern in rules["value_patterns"]:
        if pattern.search(value):
            value_matched_name = name
            break
    entropy_flag = looks_high_entropy(value)

    if value_matched_name or entropy_flag:
        reason = value_matched_name or "high_entropy"
        replacement = quoted_mask(value)
        report_entries.append({"file": filename, "line": line_no, "key": key, "rule": reason,
                                "before": value, "after": replacement})
        new_line = line.replace(value, replacement, 1) if value in line else f"{key}={replacement}"
        return new_line

    return line


def redact_value_patterns_only(line, rules, report_entries, filename, line_no):
    modified = line
    for name, pattern in rules["value_patterns"]:
        m = pattern.search(modified)
        if m:
            if is_placeholder(m.group(0), rules["placeholder_allowlist"]):
                continue
            before_val = m.group(0)
            modified = pattern.sub(MASK, modified)
            report_entries.append({"file": filename, "line": line_no, "key": None, "rule": name,
                                    "before": before_val, "after": MASK})
    return modified


def redact_code_line(line, lang, rules, report_entries, filename, line_no):
    modified = line
    patterns = rules["code_patterns"].get(lang, [])

    for pattern in patterns:
        match = pattern.search(modified)
        if match and match.group(1):
            literal_value = match.group(1)
            if literal_value.strip() == "":
                continue
            # variable/key name matched a suspicious pattern already (that's why this
            # code_pattern fired) -> always redact, placeholder allow-list doesn't apply
            modified = modified[:match.start(1)] + MASK + modified[match.end(1):]
            report_entries.append({"file": filename, "line": line_no, "key": "code_literal",
                                    "rule": "code_variable_pattern", "before": literal_value, "after": MASK})

    for name, pattern in rules["value_patterns"]:
        m = pattern.search(modified)
        if m and MASK not in m.group(0):
            if is_placeholder(m.group(0), rules["placeholder_allowlist"]):
                continue
            before_val = m.group(0)
            modified = pattern.sub(MASK, modified)
            report_entries.append({"file": filename, "line": line_no, "key": None, "rule": name,
                                    "before": before_val, "after": MASK})

    return modified


# ---- Multi-line concatenation handling ----

_PY_ASSIGN_OPEN = re.compile(r'^\s*([A-Za-z_]\w*)\s*=\s*\(\s*$')
_PY_FRAGMENT = re.compile(r'^\s*["\']([^"\']*)["\']\s*$')
_PY_CLOSE = re.compile(r'^\s*\)\s*$')

# Matches the FIRST line of a concatenation: `... var = "frag"` with an
# OPTIONAL trailing `+` (covers both the "trailing +" and "leading +" styles).
_PLUS_ASSIGN_START = re.compile(
    r'^(?:\s*(?:private|public|protected|static|final|readonly|const|let|var)\s+)*'
    r'[\w<>\[\],\s]*?(\w+)\s*=\s*["\']([^"\']*)["\']\s*(\+\s*)?$'
)
# Continuation, "leading +" style:      + "frag"      or      + "frag";
_PLUS_CONT_LEADING = re.compile(r'^\s*\+\s*["\']([^"\']*)["\']\s*(;)?\s*$')
# Continuation, "trailing +" style:      "frag" +      or      "frag";
_PLUS_CONT_TRAILING = re.compile(r'^\s*["\']([^"\']*)["\']\s*(\+)?\s*(;)?\s*$')


def find_key_matches(name, rules):
    return any(p.search(name) for p in rules["key_patterns"])


def scan_multiline_python(lines, rules, report_entries, filename):
    """Detect and redact `var = (\n "frag" \n "frag" \n)` across physical lines."""
    i = 0
    n = len(lines)
    while i < n:
        m = _PY_ASSIGN_OPEN.match(lines[i])
        if m:
            var_name = m.group(1)
            frag_indices = []
            j = i + 1
            fragments = []
            while j < n and _PY_FRAGMENT.match(lines[j]):
                fragments.append(_PY_FRAGMENT.match(lines[j]).group(1))
                frag_indices.append(j)
                j += 1
            if j < n and _PY_CLOSE.match(lines[j]) and fragments:
                joined = "".join(fragments)
                key_hit = find_key_matches(var_name, rules)
                value_hit = None
                for name, pattern in rules["value_patterns"]:
                    if pattern.search(joined):
                        value_hit = name
                        break
                entropy_hit = looks_high_entropy(joined)
                if key_hit or value_hit or entropy_hit:
                    if key_hit or not is_placeholder(joined, rules["placeholder_allowlist"]):
                        reason = "key_name_match" if key_hit else (value_hit or "high_entropy")
                        for idx, frag in zip(frag_indices, fragments):
                            lines[idx] = re.sub(r'(["\'])[^"\']*\1', lambda mm: mm.group(1) + MASK + mm.group(1), lines[idx], count=1)
                            report_entries.append({"file": filename, "line": idx + 1, "key": var_name,
                                                    "rule": f"multiline_concat_{reason}", "before": frag, "after": MASK})
        i += 1
    return lines


def scan_multiline_plus(lines, rules, report_entries, filename):
    """
    Detect and redact string concatenation spanning multiple physical lines,
    in either style:
        var = "frag" +          var = "frag"
            "frag" +                + "frag"
            "frag";                 + "frag";
    Only redacts if the chain is properly terminated with ';' - a chain that
    trails off without a terminator is left untouched rather than guessed at.
    """
    i = 0
    n = len(lines)
    while i < n:
        m = _PLUS_ASSIGN_START.match(lines[i])
        if m:
            var_name = m.group(1)
            first_frag = m.group(2)
            had_trailing_plus = bool(m.group(3))
            fragments = [first_frag]
            frag_indices = [i]
            j = i + 1
            terminated = False

            if had_trailing_plus:
                # "trailing +" style: continuation lines are plain fragments,
                # each optionally followed by another '+' or a terminating ';'.
                while j < n:
                    cont = _PLUS_CONT_TRAILING.match(lines[j])
                    if not cont:
                        break
                    fragments.append(cont.group(1))
                    frag_indices.append(j)
                    j += 1
                    if cont.group(3):  # ';' found - chain complete
                        terminated = True
                        break
                    if not cont.group(2):  # no trailing '+' and no ';' - malformed, stop
                        break
            elif j < n and _PLUS_CONT_LEADING.match(lines[j]):
                # "leading +" style: continuation lines each start with '+',
                # chain ends when a line terminates with ';'.
                while j < n:
                    cont = _PLUS_CONT_LEADING.match(lines[j])
                    if not cont:
                        break
                    fragments.append(cont.group(1))
                    frag_indices.append(j)
                    j += 1
                    if cont.group(2):  # ';' found - chain complete
                        terminated = True
                        break
            if len(fragments) > 1 and terminated:
                joined = "".join(fragments)
                key_hit = find_key_matches(var_name, rules)
                value_hit = None
                for name, pattern in rules["value_patterns"]:
                    if pattern.search(joined):
                        value_hit = name
                        break
                entropy_hit = looks_high_entropy(joined)
                if key_hit or value_hit or entropy_hit:
                    if key_hit or not is_placeholder(joined, rules["placeholder_allowlist"]):
                        reason = "key_name_match" if key_hit else (value_hit or "high_entropy")
                        for idx, frag in zip(frag_indices, fragments):
                            lines[idx] = re.sub(r'(["\'])[^"\']*\1', lambda mm: mm.group(1) + MASK + mm.group(1), lines[idx], count=1)
                            report_entries.append({"file": filename, "line": idx + 1, "key": var_name,
                                                    "rule": f"multiline_concat_{reason}", "before": frag, "after": MASK})
        i += 1
    return lines


def process_file(src_path, rel_path, rules, report_entries, classification):
    try:
        with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        return None, f"Could not read file: {e}"

    ext = src_path.suffix.lower()

    if classification == "config":
        output_lines = [redact_config_line(l, rules, report_entries, str(rel_path), i + 1) for i, l in enumerate(lines)]
        return "".join(output_lines), None

    if classification.startswith("code:"):
        lang = classification.split(":", 1)[1]

        if ext == ".py":
            lines = scan_multiline_python(lines, rules, report_entries, str(rel_path))
        if lang in PLUS_CONCAT_LANGS:
            lines = scan_multiline_plus(lines, rules, report_entries, str(rel_path))

        output_lines = []
        for i, l in enumerate(lines):
            if MASK in l:
                output_lines.append(l)  # already redacted by multiline handler, don't double-process
            else:
                output_lines.append(redact_code_line(l, lang, rules, report_entries, str(rel_path), i + 1))
        return "".join(output_lines), None

    output_lines = [redact_value_patterns_only(l, rules, report_entries, str(rel_path), i + 1) for i, l in enumerate(lines)]
    return "".join(output_lines), None


def scan_project(input_dir, output_dir, rules):
    input_dir = Path(input_dir).resolve()
    output_dir = Path(output_dir).resolve()

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    report_entries = []
    files_scanned = 0
    files_skipped = []

    for root, dirs, files in os.walk(input_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            src_path = Path(root) / fname
            rel_path = src_path.relative_to(input_dir)
            dest_path = output_dir / rel_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            classification = classify_file(src_path)
            if classification is not None:
                content, error = process_file(src_path, rel_path, rules, report_entries, classification)
                if error:
                    files_skipped.append(str(rel_path))
                    shutil.copy2(src_path, dest_path)
                    continue
                with open(dest_path, "w", encoding="utf-8") as f:
                    f.write(content)
                files_scanned += 1
            else:
                shutil.copy2(src_path, dest_path)

    return report_entries, files_scanned, files_skipped
