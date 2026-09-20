"""
syntax_check.py - lightweight, dependency-free syntax/structure validation
for sanitized benchmark output.

Python, JSON, XML (also covers .config), and YAML get a real parse, using
only the standard library. Java/JavaScript/TypeScript/Go/C# have no
standard-library parser and requiring a real compiler toolchain (javac, a
Go install, the .NET SDK, tsc) for a benchmark would be a heavy, easy-to-
break dependency for what this needs - so those get a lightweight
structural heuristic instead: balanced (), {}, [] and an even number of
unescaped quote characters. This catches the failure mode redaction could
actually cause (an unterminated string literal, an unbalanced brace from a
replacement that ate a delimiter) without claiming to be a real compiler.
This is a deliberate scope decision - see BENCHMARK.md "Limitations".
"""
import json
import xml.etree.ElementTree as ET

import yaml

REAL_PARSER_EXTENSIONS = {".py", ".json", ".xml", ".config", ".yaml", ".yml"}
HEURISTIC_EXTENSIONS = {".java", ".js", ".jsx", ".ts", ".tsx", ".go", ".cs"}
NO_SYNTAX_EXTENSIONS = {".properties", ".env", ".ini", ".conf", ".cfg"}


def _check_python(text):
    try:
        compile(text, "<benchmark>", "exec")
        return True, None
    except SyntaxError as e:
        return False, str(e)


def _check_json(text):
    try:
        json.loads(text)
        return True, None
    except json.JSONDecodeError as e:
        return False, str(e)


def _check_xml(text):
    try:
        ET.fromstring(text)
        return True, None
    except ET.ParseError as e:
        return False, str(e)


def _check_yaml(text):
    try:
        yaml.safe_load(text)
        return True, None
    except yaml.YAMLError as e:
        return False, str(e)


def _check_balanced_heuristic(text):
    """Not a real parser: checks bracket/paren/brace balance and an even
    count of unquoted-context quote characters. Sufficient to catch a
    redaction that ate or duplicated a delimiter; not sufficient to prove
    the file is otherwise valid source."""
    pairs = {"(": ")", "{": "}", "[": "]"}
    closers = set(pairs.values())
    stack = []
    in_string = None  # the quote char currently inside, or None
    escaped = False
    for ch in text:
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == in_string:
                in_string = None
            continue
        if ch in ("'", '"', "`"):
            in_string = ch
            continue
        if ch in pairs:
            stack.append(pairs[ch])
        elif ch in closers:
            if not stack or stack.pop() != ch:
                return False, f"unbalanced '{ch}'"
    if stack:
        return False, f"unclosed {stack}"
    if in_string:
        return False, "unterminated string literal"
    return True, None


_REAL_CHECKERS = {
    ".py": _check_python,
    ".json": _check_json,
    ".xml": _check_xml,
    ".config": _check_xml,
    ".yaml": _check_yaml,
    ".yml": _check_yaml,
}


def check_syntax(ext, text):
    """Returns (status, detail):
      status is "valid", "invalid", "heuristic_valid", "heuristic_invalid",
      or "not_applicable" (extensions with no meaningful syntax, e.g.
      .properties/.env - always reported as not_applicable, never counted
      as a failure).
    detail is None or an error message.
    """
    ext = ext.lower()
    if ext in NO_SYNTAX_EXTENSIONS:
        return "not_applicable", None
    if ext in _REAL_CHECKERS:
        ok, detail = _REAL_CHECKERS[ext](text)
        return ("valid" if ok else "invalid"), detail
    if ext in HEURISTIC_EXTENSIONS:
        ok, detail = _check_balanced_heuristic(text)
        return ("heuristic_valid" if ok else "heuristic_invalid"), detail
    return "not_applicable", None
