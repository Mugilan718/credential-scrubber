"""
Dart (.dart) support: the three code_patterns under `dart:` in
rules_default.yaml (declaration/assignment, named argument, quoted map
key) plus '+' concatenation across lines via scan_multiline_plus.

All values below are synthetic and clearly fake.
"""
from pathlib import Path

import pytest

import engine

_RULES_PATH = Path(engine.__file__).resolve().parent / "rules_default.yaml"


def _rules():
    return engine.load_rules(_RULES_PATH)


def _redact(line, placeholder_registry=None):
    entries = []
    out = engine.redact_code_line(line, "dart", _rules(), entries, "f.dart", 1,
                                  placeholder_registry=placeholder_registry)
    return out, entries


def test_dart_extension_is_classified_as_code():
    assert engine.classify_file(Path("lib/main.dart")) == "code:dart"


# (line, fake secret that must not survive)
MUST_MASK = [
    # 1. declaration / assignment
    ("const String apiKey = 'fakeDartKey-A1b2';", "fakeDartKey-A1b2"),
    ('final dbPassword = "fakeDbPw-C3d4";', "fakeDbPw-C3d4"),
    ("String? clientSecret = 'fakeClientSecret-E5f6';", "fakeClientSecret-E5f6"),
    ('late final String refreshToken = "fakeRefresh-G7h8";', "fakeRefresh-G7h8"),
    ("static const authToken = r'fakeRaw$Token-I9j0';", "fakeRaw$Token-I9j0"),
    ("var sessionToken = 'fakeVar-K1l2';", "fakeVar-K1l2"),
    ("this.accessToken = 'fakeField-M3n4';", "fakeField-M3n4"),
    ('final dbToken = "it\'s fakeMixed-O5p6";', "it's fakeMixed-O5p6"),
    # 2. named argument
    ("FirebaseOptions(apiKey: 'fakeFirebase-Q7r8', appId: 'demo-app')", "fakeFirebase-Q7r8"),
    ('    apiKey: "fakeOwnLine-S9t0",', "fakeOwnLine-S9t0"),
    ("Client(timeout: 5, password: r'fakeRawArg-U1v2')", "fakeRawArg-U1v2"),
    # 3. map entry with a quoted key
    ("final m = {'apiKey': 'fakeMapKey-W3x4'};", "fakeMapKey-W3x4"),
    ('  "client_secret": "fakeMapSecret-Y5z6",', "fakeMapSecret-Y5z6"),
]


@pytest.mark.parametrize("line,secret", MUST_MASK)
def test_dart_secret_is_masked(line, secret):
    out, entries = _redact(line)
    assert secret not in out
    assert any(e["before"] == secret for e in entries)


MUST_NOT_MASK = [
    "String password;",                          # no value
    "late final String apiToken;",               # no value
    "final apiKey = '';",                        # empty
    'final apiKey = "";',                        # empty
    "final token = '$token';",                   # interpolation only
    "final token = '${token}';",                 # interpolation only
    'final authToken = "${prefix}$suffix";',     # interpolation only
    "final keyboardType = 'text';",              # 'key' not a word segment
    "final author = 'Jane';",                    # 'auth' not a word segment
    "final monkey = 'banana';",
    "final title = 'Hello';",                    # not a secret-looking name
    "Text('Hello', style: bold)",
    "if (token == 'abc') {}",                    # comparison, not assignment
    "final t = loggedIn ? token : 'guest';",     # ternary, not a named arg
    "final token = await getToken();",           # not a literal
    "final apiKey = '''fakeTriple''';",          # triple-quoted: not covered
]


@pytest.mark.parametrize("line", MUST_NOT_MASK)
def test_dart_near_miss_is_left_untouched(line):
    out, entries = _redact(line)
    assert out == line
    assert entries == []


def test_dart_placeholder_category_comes_from_keyword():
    registry = engine.PlaceholderRegistry()
    out, _ = _redact('final dbPassword = "fakeDbPw-C3d4";', registry)
    assert out == 'final dbPassword = "<PASSWORD_1>";'
    out, _ = _redact("FirebaseOptions(authToken: 'fakeTok-A1')", registry)
    assert out == "FirebaseOptions(authToken: '<ACCESS_TOKEN_1>')"


def test_dart_plus_concatenation_trailing_masks_every_fragment():
    rules = _rules()
    lines = [
        "const String apiSecret = 'fakeDart-A1b2' +\n",
        "    'C3d4-secret';\n",
    ]
    entries = []
    joined = "".join(engine.scan_multiline_plus(list(lines), rules, entries, "f.dart", lang="dart"))
    assert "fakeDart-A1b2" not in joined
    assert "C3d4-secret" not in joined
    assert len(entries) == 2


def test_dart_plus_concatenation_leading_masks_every_fragment():
    rules = _rules()
    lines = [
        'final authToken = "fakeTok-E5f6"\n',
        '    + "G7h8-end";\n',
    ]
    entries = []
    joined = "".join(engine.scan_multiline_plus(list(lines), rules, entries, "f.dart", lang="dart"))
    assert "fakeTok-E5f6" not in joined
    assert "G7h8-end" not in joined
    assert len(entries) == 2


def test_dart_plus_concatenation_requires_semicolon():
    # Dart is semicolon-terminated: unlike Go, an unterminated chain is not
    # guessed at by the multiline pass.
    rules = _rules()
    lines = [
        "final authToken = 'fakeTok-I9j0' +\n",
        "    'K1l2-end'\n",
    ]
    entries = []
    engine.scan_multiline_plus(list(lines), rules, entries, "f.dart", lang="dart")
    assert entries == []
