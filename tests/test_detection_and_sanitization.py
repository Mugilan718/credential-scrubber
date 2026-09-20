"""
Broader detection/sanitization behavior tests: false positives, quoting
styles, repeated secrets, multiline concatenation, and the one invariant
that matters most for a tool like this - a value the engine reports as
redacted must never survive anywhere in its own output.

All values below are synthetic and clearly fake.
"""
from pathlib import Path

import engine

_RULES_PATH = Path(engine.__file__).resolve().parent / "rules_default.yaml"


def _rules():
    return engine.load_rules(_RULES_PATH)


# ---------------------------------------------------------------------
# False positives - ordinary config that must NOT be touched merely for
# containing a word like "user"/"admin", or a generic setting like a port
# number or environment name.
# ---------------------------------------------------------------------

FALSE_POSITIVE_LINES = [
    "timeout = 5000",
    "port = 8080",
    'environment = "production"',
    'country = "India"',
    'username = "admin"',
    'database = "testdb"',
    'app.name=DemoService',
    "retries=3",
    'region = "us-east-1"',
]


def test_ordinary_config_values_are_left_untouched():
    rules = _rules()
    for line in FALSE_POSITIVE_LINES:
        entries = []
        out = engine.redact_config_line(line + "\n", rules, entries, "app.properties", 1)
        assert out == line + "\n", f"false positive: {line!r} -> {out!r}"
        assert entries == [], f"unexpected finding for {line!r}: {entries}"


def test_username_alone_is_not_a_key_pattern():
    # "username" was briefly added as a bare key_pattern for parity with the
    # browser scanner; removed because it flags every ordinary username
    # field (the case above) with no security value - "db.username" (a
    # narrower, original pattern) is unaffected and still matches.
    rules = _rules()
    assert not any(engine.key_pattern_matches(p, "username", camel_aware=False) for p in rules["key_patterns"])
    assert any(engine.key_pattern_matches(p, "db.username", camel_aware=False) for p in rules["key_patterns"])


def test_port_alone_is_not_a_key_pattern():
    rules = _rules()
    assert not any(engine.key_pattern_matches(p, "port", camel_aware=False) for p in rules["key_patterns"])


# ---------------------------------------------------------------------
# Quoting styles
# ---------------------------------------------------------------------

def test_double_quoted_value():
    rules = _rules()
    entries = []
    out = engine.redact_config_line('password="fake-password"\n', rules, entries, "f.env", 1)
    assert out.strip() == 'password="***REDACTED***"'


def test_single_quoted_value():
    rules = _rules()
    entries = []
    out = engine.redact_config_line("password = 'fake-password'\n", rules, entries, "f.properties", 1)
    assert out.strip() == "password = '***REDACTED***'"


def test_unquoted_value():
    rules = _rules()
    entries = []
    out = engine.redact_config_line("password = fake-password\n", rules, entries, "f.properties", 1)
    assert "fake-password" not in out
    assert "***REDACTED***" in out


# ---------------------------------------------------------------------
# Repeated secrets - every occurrence must be masked; today's engine uses
# one shared MASK token for all findings (typed/stable per-value
# placeholders are a later phase - see BENCHMARK.md), so "consistency"
# today means "same token everywhere", not "same secret gets its own
# distinguishable token".
# ---------------------------------------------------------------------

def test_repeated_secret_is_masked_at_every_occurrence():
    rules = _rules()
    lines = [
        'api_key = "fake-key-123"\n',
        'backup_api_key = "fake-key-123"\n',
    ]
    entries = []
    outputs = [engine.redact_config_line(l, rules, entries, "f.properties", i + 1) for i, l in enumerate(lines)]
    for out in outputs:
        assert "fake-key-123" not in out
    # Both findings recorded, and both replacements are the same token today.
    assert len(entries) == 2
    assert entries[0]["after"] == entries[1]["after"]


# ---------------------------------------------------------------------
# Multiline concatenation (existing supported forms)
# ---------------------------------------------------------------------

def test_python_parenthesized_concatenation_masks_every_fragment():
    rules = _rules()
    lines = [
        "API_SECRET = (\n",
        '    "fake"\n',
        '    "secret"\n',
        ")\n",
    ]
    entries = []
    out_lines = engine.scan_multiline_python(list(lines), rules, entries, "f.py")
    joined = "".join(out_lines)
    assert "fakesecret" not in joined
    assert "fake" not in joined and "secret" not in joined
    assert len(entries) == 2  # one per fragment line


def test_java_plus_concatenation_masks_every_fragment():
    rules = _rules()
    lines = [
        'String authToken = "fake1234" +\n',
        '    "5678secret";\n',
    ]
    entries = []
    out_lines = engine.scan_multiline_plus(list(lines), rules, entries, "f.java")
    joined = "".join(out_lines)
    assert "fake1234" not in joined
    assert "5678secret" not in joined


# ---------------------------------------------------------------------
# The core security invariant: if the engine reports a finding as
# redacted, the original value must not remain anywhere in ITS OWN output
# line - exact text, quoted, or as a substring of something else on the
# same line.
# ---------------------------------------------------------------------

SANITIZATION_INVARIANT_CASES = [
    'password = "fake-Sup3rSecret!"',
    '"password": "fake-supersecret123",',
    '<password>fake-password</password>',
    '<add key="password" value="fake-password"/>',
    'api_key = "fake-key-Xyz789Abc"',
]


def test_sanitized_line_never_contains_the_original_value():
    # Checks the RAW captured value (quotes included, exactly as
    # check_ignore/hash_value see it) rather than a manually-dequoted short
    # word - dequoting a short value before comparing risks false alarms
    # when that bare word coincidentally also appears in the key name
    # itself (e.g. "secret_key"), which is not a leak of the value. The
    # values chosen here are also distinct enough not to coincidentally
    # collide with their own key text either way.
    rules = _rules()
    for line in SANITIZATION_INVARIANT_CASES:
        entries = []
        out = engine.redact_config_line(line + "\n", rules, entries, "f.cfg", 1)
        for entry in entries:
            assert entry["before"] not in out, (
                f"SECURITY INVARIANT VIOLATED: {entry['before']!r} survived in output "
                f"for input {line!r} -> {out!r}"
            )


def test_code_line_sanitized_output_never_contains_the_original_value():
    rules = _rules()
    cases = [
        ('String apiKey = "fakeRk4mXtQp8bNw5cVf2sLd9jHo7uGa3z";', "java"),
        ('const authToken = "fakeNq4Wz8Xr2Vt6Ym1Lp9Bk3Sd7";', "javascript"),
        ('apiKey := "fakeQw8Er2Ty5Ui9Op3As6Df1Gh4"', "go"),
        ('string sessionToken = "fakeP9xN3vLk7QsWz1RtYd5Fj8Hm";', "csharp"),
    ]
    for line, lang in cases:
        entries = []
        out = engine.redact_code_line(line, lang, rules, entries, "f", 1)
        for entry in entries:
            assert entry["before"] not in out, f"leak for {line!r} ({lang}) -> {out!r}"
