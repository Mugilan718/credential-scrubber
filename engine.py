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

import hashlib
import json
import math
import os
import re
import shutil
import subprocess
from pathlib import Path

import yaml

MASK = "***REDACTED***"

# ---------------------------------------------------------------------
# Deterministic typed placeholders (opt-in - see scan_project's
# `placeholder_mode` parameter). Disabled by default: every existing
# caller that doesn't pass a placeholder_registry gets exactly today's
# bare/quoted MASK behavior, unchanged.
# ---------------------------------------------------------------------

# Small, fixed set of categories reachable by the *current* rule set only.
# Deliberately generic - provider-specific rule names (aws_access_key_id,
# github_token, ...) collapse into these rather than being preserved, so
# a placeholder never discloses which specific vendor/service a secret
# belongs to. CUSTOMER_ID is intentionally not included: no current rule
# detects customer/user identifiers, so there is nothing that could ever
# resolve to it - adding detection for it is separate, future work.
PLACEHOLDER_CATEGORIES = frozenset({
    "PASSWORD", "API_KEY", "ACCESS_TOKEN", "CONNECTION_STRING",
    "URL", "PRIVATE_KEY", "GENERIC_SECRET",
})
DEFAULT_CATEGORY = "GENERIC_SECRET"

# Keyed by the exact raw key_pattern string as it appears in
# rules_default.yaml (key_patterns are compiled with no wrapping, so a
# compiled pattern's own .pattern attribute is that exact string - see
# category_for_key_pattern()). Any key_pattern not listed here (e.g. a
# custom one added through the rules editor) falls back to
# DEFAULT_CATEGORY rather than raising - this table is an aid, not a
# schema, and never blocks detection.
KEY_PATTERN_CATEGORY = {
    "password": "PASSWORD",
    "passwd": "PASSWORD",
    "pwd": "PASSWORD",
    "secret": "GENERIC_SECRET",
    "token": "ACCESS_TOKEN",
    "api[_-]?key": "API_KEY",
    "apikey": "API_KEY",
    "access[_-]?key": "API_KEY",
    "private[_-]?key": "PRIVATE_KEY",
    "client[_-]?secret": "API_KEY",
    "auth": "ACCESS_TOKEN",
    "credential": "GENERIC_SECRET",
    "connection[_-]?string": "CONNECTION_STRING",
    "conn[_-]?str": "CONNECTION_STRING",
    "jdbc": "CONNECTION_STRING",
    "datasource\\.url": "URL",
    "db\\.url": "URL",
    "db\\.host": "URL",
    "db\\.password": "PASSWORD",
    "db\\.username": "GENERIC_SECRET",
    "host": "URL",
    "hostname": "URL",
    "ip[_-]?address": "URL",
    "endpoint": "URL",
    "url": "URL",
    "uri": "URL",
    "ssn": "GENERIC_SECRET",
    "encryption[_-]?key": "PRIVATE_KEY",
    "signing[_-]?key": "PRIVATE_KEY",
    "session[_-]?key": "GENERIC_SECRET",
    "cert": "GENERIC_SECRET",
    "keystore": "GENERIC_SECRET",
    "truststore": "GENERIC_SECRET",
}

# Keyed by value_pattern `name` (from rules_default.yaml) - "high_entropy"
# is not a value_pattern but the synthetic reason string used when only
# the entropy heuristic fired, included here for the same lookup.
VALUE_PATTERN_CATEGORY = {
    "ipv4_address": "URL",
    "ipv6_address": "URL",
    "url_with_credentials": "URL",
    "generic_url": "URL",
    "aws_access_key_id": "API_KEY",
    "aws_secret_key_assignment": "API_KEY",
    "github_token": "ACCESS_TOKEN",
    "slack_token": "ACCESS_TOKEN",
    "jwt_token": "ACCESS_TOKEN",
    "bearer_token": "ACCESS_TOKEN",
    "private_key_block": "PRIVATE_KEY",
    "email_address": "GENERIC_SECRET",
    "high_entropy": "GENERIC_SECRET",
}

# Keyed by the suspicious keyword text captured by a code_pattern's named
# "kw" group (see _bound_code_pattern) - the same word list every
# code_pattern in rules_default.yaml currently shares. Looked up
# case-insensitively.
CODE_KEYWORD_CATEGORY = {
    "password": "PASSWORD",
    "secret": "GENERIC_SECRET",
    "token": "ACCESS_TOKEN",
    "apikey": "API_KEY",
    "api_key": "API_KEY",
    "key": "GENERIC_SECRET",
    "credential": "GENERIC_SECRET",
    "auth": "ACCESS_TOKEN",
}


def category_for_key_pattern(pattern):
    """`pattern` is a compiled key_patterns regex; its .pattern attribute
    is the exact raw string from rules_default.yaml (key_patterns are
    compiled with no wrapping applied)."""
    return KEY_PATTERN_CATEGORY.get(pattern.pattern, DEFAULT_CATEGORY)


def category_for_value_pattern(name):
    return VALUE_PATTERN_CATEGORY.get(name, DEFAULT_CATEGORY)


def category_for_code_keyword(keyword):
    if not keyword:
        return DEFAULT_CATEGORY
    return CODE_KEYWORD_CATEGORY.get(keyword.lower(), DEFAULT_CATEGORY)


def _most_specific_category(categories):
    """Some keys match more than one key_pattern (e.g. "client_secret"
    matches both the bare "secret" pattern and the more specific
    "client[_-]?secret" one) - prefer whichever matched pattern maps to a
    named category over one that only falls back to DEFAULT_CATEGORY, so
    a generic pattern appearing earlier in rules_default.yaml doesn't
    shadow a more specific one appearing later. Never changes *whether*
    something is detected - only which category label a placeholder uses."""
    fallback = DEFAULT_CATEGORY
    for c in categories:
        if c != DEFAULT_CATEGORY:
            return c
        fallback = c
    return fallback


class PlaceholderRegistry:
    """Deterministic, typed placeholder assignment for exactly one
    scan_project() call.

    Maps (category, exact_value) -> a stable "<CATEGORY_N>" token, with a
    separate ordinal counter per category. Two different real values in
    the same category never collide on one placeholder; the same real
    value under a different key/variable name (or in a different file
    within the same scan) always gets the same one - see
    category_for_key_pattern() and friends for how "category" is decided,
    and scan_project()'s sorted os.walk traversal for why numbering is
    reproducible across repeated scans of unchanged input.

    Security: this map is exactly as sensitive as the secrets it indexes.
    It is never persisted to disk or a database, never logged, and never
    included in any report entry or sensitive-value storage - it exists
    only in memory for the lifetime of the scan_project() call that
    created it, then is discarded with it. The placeholder text itself is
    built only from a fixed category name and an integer - never from any
    character of the original value - so it cannot leak the secret's
    content, length, prefix, suffix, or provider even if the placeholder
    text itself were ever exposed.
    """

    def __init__(self):
        self._map = {}
        self._counters = {}

    def get_or_create(self, category, value):
        key = (category, value)
        placeholder = self._map.get(key)
        if placeholder is None:
            n = self._counters.get(category, 0) + 1
            self._counters[category] = n
            placeholder = f"<{category}_{n}>"
            self._map[key] = placeholder
        return placeholder


def _normalize_value_for_identity(value):
    """Strip one matching pair of surrounding quote characters, if any, so
    the same underlying value is recognized as identical for placeholder
    correlation regardless of which quote style (or none) it happens to
    be written with (e.g. "PF001" and 'PF001' must correlate)."""
    v = value.rstrip()
    if len(v) >= 2 and v[0] in ('"', "'") and v[-1] == v[0]:
        return v[1:-1]
    return v


def _quote_wrap(value, replacement_text, force_quote=False):
    """Wrap `replacement_text` (MASK or a typed placeholder) to match
    `value`'s original quoting style. Shared by quoted_mask() (MASK) and
    the placeholder-mode path, so both stay byte-for-byte consistent
    about quoting - see quoted_mask()'s docstring for `force_quote`."""
    v = value.rstrip()
    if len(v) >= 2 and v[0] in ('"', "'") and v[-1] == v[0]:
        return v[0] + replacement_text + v[0]
    if force_quote:
        return '"' + replacement_text + '"'
    return replacement_text


def _xml_escape_placeholder(token):
    """Escape the two characters ('<', '>') that make a typed placeholder
    token (e.g. "<PASSWORD_1>") invalid when written into XML element text
    or an XML attribute value, where they're reserved metacharacters -
    MASK ("***REDACTED***") contains neither, so MASK-mode output has
    never needed this. Only ever applied to a token this module itself
    just generated (never to `value` or the rest of the line), so there is
    no existing XML content here to double-escape. The registry's own
    stored token, and every non-XML caller, stay exactly "<CATEGORY_N>" -
    this is a display-only transform at the same layer as _quote_wrap's
    quoting, not a change to placeholder identity."""
    return token.replace("<", "&lt;").replace(">", "&gt;")


def _placeholder_or_mask(value, category, placeholder_registry, force_quote=False, xml_escape=False):
    """The text to substitute for a detected *config-line* value (one
    whose captured span may include surrounding quotes), at its original
    quoting style: the shared MASK when `placeholder_registry` is None
    (placeholder_mode off - today's exact, unchanged default), or a
    deterministic typed placeholder token when one is supplied.

    `xml_escape`: True when this value's line was recognized as an XML
    element-text or XML-attribute-value shape (see redact_config_line) -
    escapes the placeholder token's '<'/'>' before it's written into that
    XML context. Never applied to MASK (which contains neither character
    and whose behavior must stay unchanged)."""
    if placeholder_registry is None:
        return _quote_wrap(value, MASK, force_quote=force_quote)
    identity_value = _normalize_value_for_identity(value)
    token = placeholder_registry.get_or_create(category, identity_value)
    replacement_text = _xml_escape_placeholder(token) if xml_escape else token
    return _quote_wrap(value, replacement_text, force_quote=force_quote)


class NotAGitRepoError(Exception):
    """Raised when changed_files_only scanning is requested but input_dir
    isn't a git repository, so there's no changed-files list to scan."""
    pass

CONFIG_EXTENSIONS = {".properties", ".yml", ".yaml", ".json", ".xml", ".ini", ".conf", ".cfg", ".config"}
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


# Matches the "\w*(?:kw1|kw2|...)\w*" shape used by most code_patterns to let
# a suspicious keyword appear anywhere inside a larger variable name.
_CODE_IDENT_WRAP_WORD = re.compile(r'\\w\*\(\?:([^)]*)\)\\w\*')
# Matches the "[^"']*(?:kw1|kw2|...)[^"']*" shape used by the getenv-style
# pattern to let a keyword appear anywhere inside a quoted string literal
# (e.g. an env var name).
_CODE_IDENT_WRAP_QUOTED = re.compile(r"\[\^\"'\]\*\(\?:([^)]*)\)\[\^\"'\]\*")


def _bound_code_pattern(raw):
    """Wrap the suspicious-keyword alternation (and the \\w*/[^"']* run
    around it) in named groups 'ident'/'kw'. This doesn't change what the
    pattern matches, but lets _passes_identifier_boundary() below check
    afterwards that the keyword is a real segment of the identifier/env-var
    name - the whole thing, a snake_case piece, or a camelCase piece - and
    not just a substring of an unrelated longer word (e.g. "auth" inside
    "author", "key" inside "monkey")."""
    def sub(wrapper):
        def _do(m):
            return "(?P<ident>{0}(?P<kw>{1}){0})".format(wrapper, m.group(1))
        return _do

    new, n = _CODE_IDENT_WRAP_WORD.subn(sub(r"\w*"), raw, count=1)
    if n:
        return new
    new, n = _CODE_IDENT_WRAP_QUOTED.subn(sub(r"[^\"']*"), raw, count=1)
    return new


def load_rules(rules_path):
    with open(rules_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return {
        "key_patterns": [re.compile(p, re.IGNORECASE) for p in raw.get("key_patterns", [])],
        "value_patterns": [(vp["name"], re.compile(vp["regex"], re.IGNORECASE)) for vp in raw.get("value_patterns", [])],
        "code_patterns": {lang: [re.compile(_bound_code_pattern(p)) for p in pats] for lang, pats in raw.get("code_patterns", {}).items()},
        "placeholder_allowlist": {s.lower() for s in raw.get("placeholder_allowlist", [])},
    }


def _char_boundary_ok(adjacent_char, keyword_char):
    """One side of a camelCase-aware identifier-boundary check: `adjacent_char`
    (the char just outside the matched keyword, or None at the edge of the
    identifier) is a valid boundary if there's no adjacent char, if it isn't a
    letter (digit/underscore/etc. all count as separators), or if it's a
    letter whose case differs from `keyword_char` (a camelCase transition,
    e.g. the "i"/"K" join in "apiKey")."""
    if adjacent_char is None:
        return True
    if not adjacent_char.isalpha():
        return True
    return adjacent_char.islower() != keyword_char.islower()


def _strict_boundary_ok(adjacent_char):
    """One side of a strict (config-key-style) boundary check: only a
    non-alphanumeric char (or no char at all) counts as a separator - no
    camelCase allowance, since config/env keys are conventionally
    snake_case/dot/kebab-case, not camelCase (e.g. "db_port"/"db.port"
    should match a "port" rule but "support" should not)."""
    return adjacent_char is None or not adjacent_char.isalnum()


def key_pattern_matches(pattern, text, camel_aware):
    """Check whether `pattern` matches a genuine bounded segment of `text`
    (a whole word, or one set off by underscore/dot/hyphen/digit, and -when
    `camel_aware`- one set off by a camelCase transition) rather than merely
    appearing as a substring of an unrelated longer word (e.g. "auth" inside
    "author", "key" inside "monkey").

    `camel_aware=False` is used for config-file keys (snake_case/dot/kebab
    convention); `camel_aware=True` is used for source-code identifiers
    (which are commonly camelCase, e.g. "secretKey", "dbPassword")."""
    for m in pattern.finditer(text):
        start, end = m.span()
        if camel_aware:
            prev_char = text[start - 1] if start > 0 else None
            next_char = text[end] if end < len(text) else None
            if _char_boundary_ok(prev_char, text[start]) and _char_boundary_ok(next_char, text[end - 1]):
                return True
        else:
            prev_char = text[start - 1] if start > 0 else None
            next_char = text[end] if end < len(text) else None
            if _strict_boundary_ok(prev_char) and _strict_boundary_ok(next_char):
                return True
    return False


def _passes_identifier_boundary(match):
    """Reject a code_pattern match whose suspicious keyword ('kw') is merely
    a substring of an unrelated, longer identifier/env-var name ('ident')
    rather than a genuine whole word, snake_case segment, or camelCase
    segment of it. Patterns without the ident/kw wrapper (e.g. a custom
    value_pattern-only rule) are always accepted."""
    groupindex = match.re.groupindex
    if "ident" not in groupindex or "kw" not in groupindex:
        return True
    ident_start, ident_end = match.span("ident")
    kw_start, kw_end = match.span("kw")
    text = match.string
    prev_char = text[kw_start - 1] if kw_start > ident_start else None
    next_char = text[kw_end] if kw_end < ident_end else None
    return (_char_boundary_ok(prev_char, text[kw_start])
            and _char_boundary_ok(next_char, text[kw_end - 1]))


def _find_valid_code_match(pattern, text):
    """Like pattern.search(text), but skips over any match rejected by
    _passes_identifier_boundary()."""
    for m in pattern.finditer(text):
        if _passes_identifier_boundary(m):
            return m
    return None


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
    # Words joined by common identifier/reference separators (snake_case,
    # kebab-case, docker image refs like "repo/name:tag", dotted names) read
    # as natural language, not randomness - skip them like pure-letter
    # strings already are. Raising min_entropy instead isn't safe: a genuinely
    # random hex secret tops out at log2(16) = 4.0 entropy, which already
    # overlaps values like "community_platform_dev" (~3.97).
    if re.fullmatch(r"[A-Za-z\s_\-/:.]+", v):
        return False
    return shannon_entropy(v) >= min_entropy


def hash_value(value):
    """One-way hash of a value being ignored, so ignored_findings never has
    to store (or let anyone recover) the real secret it's suppressing."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def check_ignore(ignore_map, filename, key, rule, value):
    """Check whether a (file, key, rule) finding is currently ignored.

    `ignore_map` is {(file, key, rule): value_hash_or_None}. Returns
    (suppress, previously_ignored_but_changed):
      - not ignored at all                          -> (False, False)
      - ignored AND value's hash matches              -> (True,  False)  suppress
      - ignored BUT value's hash differs (or was never
        recorded, e.g. an older ignore)               -> (False, True)   don't
        suppress - the value changed since it was marked safe, so redact and
        report it as usual, just flagged for review instead of looking like
        a brand-new finding with no context.
    """
    triple = (filename, key, rule)
    if triple not in ignore_map:
        return False, False
    stored_hash = ignore_map[triple]
    if stored_hash is not None and stored_hash == hash_value(value):
        return True, False
    return False, True


# Config lines come in more shapes than "key: value"/"key=value" - JSON
# quoted keys, XML elements, and .config-style <add key=".." value=".."/>
# pairs all hold a key and a value too, just with different surrounding
# syntax. Each of these is tried in turn (most structurally specific first;
# order barely matters in practice since they're mutually exclusive by
# leading character - "<", '"', or a bareword char). Every pattern captures
# a named "value" group so callers can redact by its exact span instead of
# re-searching the line for the value's text (see redact_config_line) -
# searching by text can hit an earlier, unrelated occurrence of the same
# text (e.g. "secret_key=secret" - searching for "secret" finds the key
# first).
_KV_XML_ATTR_PAIR = re.compile(
    r'^(?P<prefix>\s*<[\w:.\-]+\s+[^>]*?\bkey\s*=\s*["\'])(?P<key>[^"\']+)'
    r'(?P<mid>["\'][^>]*?\bvalue\s*=\s*["\'])(?P<value>[^"\']*)(?P<suffix>["\'].*)$',
    re.IGNORECASE,
)
_KV_XML_ELEMENT = re.compile(
    r'^(?P<prefix>\s*<(?P<key>[A-Za-z_][\w.\-]*)(?:\s[^>]*)?>)(?P<value>[^<]*)(?P<suffix></(?P=key)>\s*)$'
)
_KV_JSON_KEY = re.compile(r'^(?P<prefix>\s*"(?P<key>[^"]+)"\s*:\s*)(?P<value>.*?)(?P<suffix>,?\s*)$')
_KV_BAREWORD = re.compile(r'^(?P<prefix>\s*(?P<key>[A-Za-z0-9_.\-\[\]]+)\s*[:=]\s*)(?P<value>.*)$')

_KV_PATTERNS = (_KV_XML_ATTR_PAIR, _KV_XML_ELEMENT, _KV_JSON_KEY, _KV_BAREWORD)


# A bare YAML block-scalar indicator ("|", ">", with an optional chomping
# "+"/"-" and/or explicit indentation digit, e.g. "|-", ">+4") - like a
# JSON "{"/"[" opener, this isn't a redactable leaf value; the real
# content is the indented lines that follow, which find_key_value never
# sees as this key's value at all (see the block-scalar guard below).
_YAML_BLOCK_SCALAR = re.compile(r'^[|>][+-]?\d*$')


def find_key_value(line):
    """Extract (key, value, value_start, value_end) from a config line, or
    (None, None, None, None) if it doesn't look like any recognized shape
    (redact_value_patterns_only is used instead in that case).

    value_start/value_end are the value's exact character offsets within
    `line`, enabling span-based redaction.
    """
    for pattern in _KV_PATTERNS:
        m = pattern.match(line)
        if m:
            value = m.group("value")
            stripped = value.strip()
            if stripped in ("{", "["):
                # A JSON object/array that continues on later lines, not a
                # redactable leaf - treating "{" as the whole value would
                # corrupt the file (its matching close appears lines later).
                continue
            if _YAML_BLOCK_SCALAR.match(stripped):
                # A multi-line YAML block scalar header (e.g. "key: |") -
                # redacting just the indicator would strip the block-scalar
                # syntax while leaving its now-orphaned indented body
                # behind, corrupting the document; leaving the header
                # alone leaks nothing by itself, since neither the key
                # name nor "|"/">" is a secret. The body itself is not
                # scanned - see BENCHMARK.md limitations.
                continue
            return m.group("key"), value, m.start("value"), m.end("value")
    return None, None, None, None


YAML_EXTENSIONS = {".yaml", ".yml"}

# Files where a value can sit inside XML element text or an XML attribute
# value - see _xml_escape_placeholder(). Only used to decide whether the
# redact_value_patterns_only() fallback path (which has no structural shape
# to test, unlike redact_config_line's _KV_XML_* patterns) should XML-escape
# a placeholder token; not used to change detection or MASK-mode behavior.
XML_EXTENSIONS = {".xml", ".config"}


def quoted_mask(value, force_quote=False):
    """Mask a config value, preserving its surrounding quote character (if any).

    `value` is the raw text captured after 'key:'/'key=', which still includes
    any quotes the author wrote (e.g. `"secret"`). Replacing that whole span
    with the bare MASK would silently strip the quotes; wrapping the MASK in
    the same quote char keeps the redacted line's quoting style unchanged.

    `force_quote` covers formats (currently: YAML) where an unquoted plain
    scalar can't safely start with certain characters - MASK's leading '*'
    is YAML's alias-reference indicator, so a bare MASK on a line that was
    never quoted to begin with (e.g. `endpoint: https://...`) produces a
    line that fails to parse as YAML at all (`endpoint: ***REDACTED***`).
    When set, and the value wasn't already quoted, the replacement is
    double-quoted instead of left bare - always safe, since MASK contains
    no characters that need escaping inside a double-quoted YAML scalar.
    """
    return _quote_wrap(value, MASK, force_quote=force_quote)


def redact_config_line(line, rules, report_entries, filename, line_no, ignore_map={}, placeholder_registry=None):
    key, value, value_start, value_end = find_key_value(line)
    if key is None:
        return redact_value_patterns_only(line, rules, report_entries, filename, line_no, ignore_map, placeholder_registry)

    if value.strip() == "":
        return line

    # Only YAML's plain-scalar syntax treats a bare MASK's leading '*' as
    # meaningful (an alias reference) - see quoted_mask()'s docstring. Every
    # other format handled here (.properties/.env/JSON/XML/.config/etc.)
    # is unaffected either way, so this is gated strictly by extension.
    # Typed placeholders never start with '*' either way, but force_quote
    # is applied uniformly regardless of mode for one less thing to reason
    # about.
    is_yaml = Path(filename).suffix.lower() in YAML_EXTENSIONS
    # True only when this line's value was captured via one of the two
    # XML-tag-shaped patterns (element text or an attribute's value=".."),
    # not merely because the file extension is .xml/.config - a bareword
    # or JSON-shaped line in a .config file (e.g. INI-style) has no
    # surrounding tag to corrupt and must not be escaped. See
    # _xml_escape_placeholder().
    is_xml_shape = bool(_KV_XML_ATTR_PAIR.match(line)) or bool(_KV_XML_ELEMENT.match(line))

    matched_key_patterns = [p for p in rules["key_patterns"] if key_pattern_matches(p, key, camel_aware=False)]

    # Key-name match ALWAYS redacts, placeholder allow-list does not apply here.
    if matched_key_patterns:
        suppress, changed = check_ignore(ignore_map, filename, key, "key_name_match", value)
        if suppress:
            return line
        category = _most_specific_category(category_for_key_pattern(p) for p in matched_key_patterns)
        replacement = _placeholder_or_mask(value, category, placeholder_registry, force_quote=is_yaml, xml_escape=is_xml_shape)
        entry = {"file": filename, "line": line_no, "key": key, "rule": "key_name_match",
                  "before": value, "after": replacement}
        if changed:
            entry["previously_ignored_value_changed"] = True
        report_entries.append(entry)
        return line[:value_start] + replacement + line[value_end:]

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
        suppress, changed = check_ignore(ignore_map, filename, key, reason, value)
        if suppress:
            return line
        category = category_for_value_pattern(reason)
        replacement = _placeholder_or_mask(value, category, placeholder_registry, force_quote=is_yaml, xml_escape=is_xml_shape)
        entry = {"file": filename, "line": line_no, "key": key, "rule": reason,
                  "before": value, "after": replacement}
        if changed:
            entry["previously_ignored_value_changed"] = True
        report_entries.append(entry)
        return line[:value_start] + replacement + line[value_end:]

    return line


def redact_value_patterns_only(line, rules, report_entries, filename, line_no, ignore_map={}, placeholder_registry=None):
    modified = line
    # No structural shape to test here (unlike redact_config_line's
    # _KV_XML_* patterns) - a value_pattern match can land anywhere in the
    # line, so this falls back to the file extension. Only affects
    # placeholder-mode escaping of the substituted token; detection and
    # MASK-mode output are unaffected either way.
    is_xml = Path(filename).suffix.lower() in XML_EXTENSIONS
    for name, pattern in rules["value_patterns"]:
        m = pattern.search(modified)
        if m:
            if is_placeholder(m.group(0), rules["placeholder_allowlist"]):
                continue
            before_val = m.group(0)
            suppress, changed = check_ignore(ignore_map, filename, None, name, before_val)
            if suppress:
                continue
            if placeholder_registry is not None:
                category = category_for_value_pattern(name)
                token = placeholder_registry.get_or_create(category, before_val)
                after_val = _xml_escape_placeholder(token) if is_xml else token
                # A function (not a fixed string) so every distinct match on
                # this line - if the pattern matches more than once -
                # resolves its own identity, same as pattern.sub(MASK, ...)
                # already replaced every match with a fixed string before.
                def _repl(mm, _category=category):
                    tok = placeholder_registry.get_or_create(_category, mm.group(0))
                    return _xml_escape_placeholder(tok) if is_xml else tok
                modified = pattern.sub(_repl, modified)
            else:
                after_val = MASK
                modified = pattern.sub(MASK, modified)
            entry = {"file": filename, "line": line_no, "key": None, "rule": name,
                      "before": before_val, "after": after_val}
            if changed:
                entry["previously_ignored_value_changed"] = True
            report_entries.append(entry)
    return modified


_PLACEHOLDER_SHAPE = re.compile(r"<[A-Z_]+_\d+>")


def _already_redacted(text, placeholder_registry):
    """True if `text` contains a marker a previous pass in this same line
    already inserted - MASK always, plus (only when placeholder mode is
    active) anything shaped like a typed placeholder token - so the
    second (value_patterns) pass below doesn't try to re-redact text the
    first (code_patterns) pass already replaced."""
    if MASK in text:
        return True
    if placeholder_registry is not None and _PLACEHOLDER_SHAPE.search(text):
        return True
    return False


def redact_code_line(line, lang, rules, report_entries, filename, line_no, ignore_map={}, placeholder_registry=None):
    modified = line
    patterns = rules["code_patterns"].get(lang, [])

    for pattern in patterns:
        match = _find_valid_code_match(pattern, modified)
        # The literal string value is always the last capture group, whether
        # or not _bound_code_pattern() prefixed it with its ident/kw groups.
        if match and match.group(match.re.groups):
            literal_value = match.group(match.re.groups)
            if literal_value.strip() == "":
                continue
            suppress, changed = check_ignore(ignore_map, filename, "code_literal", "code_variable_pattern", literal_value)
            if suppress:
                continue
            # variable/key name matched a suspicious pattern already (that's why this
            # code_pattern fired) -> always redact, placeholder allow-list doesn't apply
            lit_group = match.re.groups
            if placeholder_registry is not None:
                kw_text = match.group("kw") if "kw" in match.re.groupindex else None
                category = category_for_code_keyword(kw_text)
                replacement = placeholder_registry.get_or_create(category, literal_value)
            else:
                replacement = MASK
            modified = modified[:match.start(lit_group)] + replacement + modified[match.end(lit_group):]
            entry = {"file": filename, "line": line_no, "key": "code_literal",
                      "rule": "code_variable_pattern", "before": literal_value, "after": replacement}
            if changed:
                entry["previously_ignored_value_changed"] = True
            report_entries.append(entry)

    for name, pattern in rules["value_patterns"]:
        m = pattern.search(modified)
        if m and not _already_redacted(m.group(0), placeholder_registry):
            if is_placeholder(m.group(0), rules["placeholder_allowlist"]):
                continue
            before_val = m.group(0)
            suppress, changed = check_ignore(ignore_map, filename, None, name, before_val)
            if suppress:
                continue
            if placeholder_registry is not None:
                category = category_for_value_pattern(name)
                after_val = placeholder_registry.get_or_create(category, before_val)
                modified = pattern.sub(lambda mm: placeholder_registry.get_or_create(category, mm.group(0)), modified)
            else:
                after_val = MASK
                modified = pattern.sub(MASK, modified)
            entry = {"file": filename, "line": line_no, "key": None, "rule": name,
                      "before": before_val, "after": after_val}
            if changed:
                entry["previously_ignored_value_changed"] = True
            report_entries.append(entry)

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
    # camel_aware=True: `name` here is a source-code variable name (used by
    # the multiline-concatenation scanners below), which is conventionally
    # camelCase (e.g. "secretKey", "dbPassword"), unlike config-file keys.
    #
    # Returns the list of every matching pattern (possibly empty), not
    # just a bool - every existing caller only ever used this in a boolean
    # context (an empty list is falsy, same as the old False), so this is
    # backward-compatible; the patterns are what let callers resolve a
    # placeholder category via category_for_key_pattern(), preferring the
    # most specific match when more than one pattern matches (see
    # _most_specific_category()).
    return [p for p in rules["key_patterns"] if key_pattern_matches(p, name, camel_aware=True)]


def _multiline_category(key_hit, value_hit):
    if key_hit:
        return _most_specific_category(category_for_key_pattern(p) for p in key_hit)
    return category_for_value_pattern(value_hit or "high_entropy")


def _multiline_replacements(placeholder_registry, category, joined, fragment_count):
    """One replacement string per fragment, in order.

    MASK mode (placeholder_registry is None - today's exact, unchanged
    default): every fragment individually gets MASK, exactly as before
    this feature existed.

    Placeholder mode: the whole reconstructed value is one entity, so it
    gets exactly one placeholder - assigned to the FIRST fragment's quoted
    span - with every later fragment's span emptied, rather than each
    fragment getting its own (misleadingly implying separate secrets).
    """
    if placeholder_registry is not None:
        full_placeholder = placeholder_registry.get_or_create(category, joined)
        return [full_placeholder] + [""] * (fragment_count - 1)
    return [MASK] * fragment_count


def _redact_multiline_fragments(lines, frag_indices, fragments, replacements):
    """Rewrite each physical fragment line in place using `replacements`
    (one entry per fragment, from _multiline_replacements()). Line count
    and structure are unchanged - only the quoted content on each line
    changes - so the file's shape stays exactly as it was, and the
    original secret survives nowhere in the multi-line result.

    Yields (line_index, fragment_text, replacement_text) per fragment, for
    the caller to build report entries from.
    """
    for idx, frag, replacement in zip(frag_indices, fragments, replacements):
        lines[idx] = re.sub(r'(["\'])[^"\']*\1', lambda mm, r=replacement: mm.group(1) + r + mm.group(1), lines[idx], count=1)
        yield idx, frag, replacement


def scan_multiline_python(lines, rules, report_entries, filename, ignore_map={}, placeholder_registry=None):
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
                        rule = f"multiline_concat_{reason}"
                        suppress, changed = check_ignore(ignore_map, filename, var_name, rule, joined)
                        if not suppress:
                            category = _multiline_category(key_hit, value_hit) if placeholder_registry is not None else None
                            replacements = _multiline_replacements(placeholder_registry, category, joined, len(fragments))
                            for idx, frag, frag_replacement in _redact_multiline_fragments(lines, frag_indices, fragments, replacements):
                                entry = {"file": filename, "line": idx + 1, "key": var_name,
                                          "rule": rule, "before": frag, "after": frag_replacement}
                                if changed:
                                    entry["previously_ignored_value_changed"] = True
                                report_entries.append(entry)
        i += 1
    return lines


def scan_multiline_plus(lines, rules, report_entries, filename, ignore_map={}, placeholder_registry=None):
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
                        rule = f"multiline_concat_{reason}"
                        suppress, changed = check_ignore(ignore_map, filename, var_name, rule, joined)
                        if not suppress:
                            category = _multiline_category(key_hit, value_hit) if placeholder_registry is not None else None
                            replacements = _multiline_replacements(placeholder_registry, category, joined, len(fragments))
                            for idx, frag, frag_replacement in _redact_multiline_fragments(lines, frag_indices, fragments, replacements):
                                entry = {"file": filename, "line": idx + 1, "key": var_name,
                                          "rule": rule, "before": frag, "after": frag_replacement}
                                if changed:
                                    entry["previously_ignored_value_changed"] = True
                                report_entries.append(entry)
        i += 1
    return lines


def process_file(src_path, rel_path, rules, report_entries, classification, ignore_map={}, placeholder_registry=None):
    try:
        with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        return None, f"Could not read file: {e}"

    ext = src_path.suffix.lower()

    if classification == "config":
        output_lines = [
            redact_config_line(l, rules, report_entries, str(rel_path), i + 1, ignore_map, placeholder_registry)
            for i, l in enumerate(lines)
        ]
        return "".join(output_lines), None

    if classification.startswith("code:"):
        lang = classification.split(":", 1)[1]

        if ext == ".py":
            lines = scan_multiline_python(lines, rules, report_entries, str(rel_path), ignore_map, placeholder_registry)
        if lang in PLUS_CONCAT_LANGS:
            lines = scan_multiline_plus(lines, rules, report_entries, str(rel_path), ignore_map, placeholder_registry)

        output_lines = []
        for i, l in enumerate(lines):
            if _already_redacted(l, placeholder_registry):
                output_lines.append(l)  # already redacted by multiline handler, don't double-process
            else:
                output_lines.append(redact_code_line(l, lang, rules, report_entries, str(rel_path), i + 1, ignore_map, placeholder_registry))
        return "".join(output_lines), None

    output_lines = [
        redact_value_patterns_only(l, rules, report_entries, str(rel_path), i + 1, ignore_map, placeholder_registry)
        for i, l in enumerate(lines)
    ]
    return "".join(output_lines), None


def get_git_changed_files(input_dir):
    """Return the set of file paths (POSIX-style, relative to input_dir) that
    are staged, unstaged, or untracked in the git repo at input_dir.

    Returns None if input_dir isn't a git repository (or git isn't
    available) - deliberately distinct from an empty set, which would mean
    "it's a repo, but nothing has changed" rather than "can't tell".

    Assumes input_dir is itself the repo's top level; if it's a subdirectory
    of a larger repo, git's paths are relative to the repo root instead and
    won't line up with this function's callers.
    """
    commands = [
        ["git", "diff", "--name-only", "--cached"],
        ["git", "diff", "--name-only"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]
    changed = set()
    for cmd in commands:
        try:
            result = subprocess.run(
                cmd, cwd=str(input_dir), capture_output=True, text=True, check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            return None
        for line in result.stdout.splitlines():
            line = line.strip()
            if line:
                changed.add(line)
    return changed


def scan_project(input_dir, output_dir, rules, ignore_map={}, changed_files_only=False, placeholder_mode=False):
    """
    `placeholder_mode`: opt-in, defaults to False. False (the default)
    preserves today's behavior exactly - every finding is masked with the
    single shared MASK constant, byte-for-byte identical to before this
    parameter existed. True redacts with deterministic, typed
    placeholders instead (see PlaceholderRegistry) - the same real value,
    detected as the same category, always gets the same "<CATEGORY_N>"
    token anywhere in this one scan; different values never collide on
    one token.
    """
    input_dir = Path(input_dir).resolve()
    output_dir = Path(output_dir).resolve()

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    changed_files = None
    if changed_files_only:
        changed_files = get_git_changed_files(input_dir)
        if changed_files is None:
            raise NotAGitRepoError(
                f"{input_dir} is not a git repository - full scan required"
            )

    output_dir.mkdir(parents=True, exist_ok=True)

    report_entries = []
    files_scanned = 0
    files_skipped = []

    # One registry for this whole call, never returned or persisted - see
    # PlaceholderRegistry's docstring. None when placeholder_mode is off,
    # so every function this is threaded into falls back to its existing
    # MASK-based behavior with no other code path change.
    placeholder_registry = PlaceholderRegistry() if placeholder_mode else None

    for root, dirs, files in os.walk(input_dir):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        # Sorted so file/placeholder-numbering order is reproducible
        # across repeated scans of unchanged input - os.walk's own
        # per-directory order is not a documented guarantee.
        for fname in sorted(files):
            src_path = Path(root) / fname
            rel_path = src_path.relative_to(input_dir)

            if src_path.is_symlink():
                # A symlink can point anywhere on disk the OS user can read
                # (e.g. into a home directory's SSH keys) - os.walk lists it
                # as an ordinary file, so without this check it would be
                # read/copied like one. Skip it entirely rather than
                # following it or copying it through.
                files_skipped.append(str(rel_path))
                continue

            if changed_files is not None and rel_path.as_posix() not in changed_files:
                # Changed-files-only mode: skip entirely rather than copying
                # it through unredacted. The output folder in this mode is a
                # PARTIAL result (only the files that were actually scanned),
                # never a full mirrored copy - copying unchanged files
                # through unredacted would make an incomplete output folder
                # look like a complete, safe-to-share sanitized copy when it
                # silently isn't (real secrets in untouched files would sit
                # there in plaintext).
                continue

            dest_path = output_dir / rel_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            classification = classify_file(src_path)
            if classification is not None:
                content, error = process_file(src_path, rel_path, rules, report_entries, classification, ignore_map, placeholder_registry)
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
