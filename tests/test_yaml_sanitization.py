"""
Regression tests for the YAML-alias-syntax sanitization bug found by the
benchmark: redacting an UNQUOTED YAML scalar with the bare MASK token
("***REDACTED***") produces invalid YAML, because a leading '*' is YAML's
alias-reference syntax. A quoted value was never affected (the mask is
quoted to match), so this only hits unquoted (plain-style) scalars.

All values below are synthetic and clearly fake.
"""
from pathlib import Path

import pytest
import yaml

import engine

_RULES_PATH = Path(engine.__file__).resolve().parent / "rules_default.yaml"


def _rules():
    return engine.load_rules(_RULES_PATH)


def _redact_yaml_line(line, filename="settings.yaml"):
    rules = _rules()
    entries = []
    out = engine.redact_config_line(line, rules, entries, filename, 1)
    return out, entries


# ---------------------------------------------------------------------
# The bug, reproduced directly
# ---------------------------------------------------------------------

def test_unquoted_yaml_scalar_redaction_is_valid_yaml():
    out, entries = _redact_yaml_line("endpoint: https://fake.internal.example.com/api\n")
    assert entries, "expected 'endpoint' (a key_pattern) to be flagged"
    assert "https://fake.internal.example.com/api" not in out
    # This is the actual bug: yaml.safe_load must not raise on the engine's
    # own output.
    yaml.safe_load(out)


def test_unquoted_yaml_password_like_value_is_valid_yaml():
    out, entries = _redact_yaml_line("db_password: fakeSup3rSecret!2024\n")
    assert entries
    assert "fakeSup3rSecret!2024" not in out
    yaml.safe_load(out)


def test_unquoted_yaml_token_like_value_is_valid_yaml():
    out, entries = _redact_yaml_line("api_key: fakeRk4mXtQp8bNw5cVf2sLd9jHo7uGa3z\n")
    assert entries
    assert "fakeRk4mXtQp8bNw5cVf2sLd9jHo7uGa3z" not in out
    yaml.safe_load(out)


# ---------------------------------------------------------------------
# Cases that were never broken - confirm the fix doesn't disturb them
# ---------------------------------------------------------------------

def test_quoted_yaml_value_was_already_valid_and_stays_valid():
    out, entries = _redact_yaml_line('encryption_key: "fake-MFEwEQYHKoZIzj0"\n')
    assert entries
    assert "fake-MFEwEQYHKoZIzj0" not in out
    parsed = yaml.safe_load(out)
    assert parsed["encryption_key"] == "***REDACTED***"


def test_single_quoted_yaml_value_stays_valid():
    out, entries = _redact_yaml_line("password: 'fake-hunter2-longer'\n")
    assert entries
    parsed = yaml.safe_load(out)
    assert parsed["password"] == "***REDACTED***"


def test_normal_non_sensitive_yaml_values_are_left_untouched_and_stay_valid():
    lines = [
        "environment: production\n",
        "port: 8080\n",
        "region: us-east-1\n",
        "name: benchmark-service\n",
    ]
    for line in lines:
        out, entries = _redact_yaml_line(line)
        assert entries == [], f"unexpected finding for {line!r}"
        assert out == line
        yaml.safe_load(out)  # was already valid; must still be


def test_placeholder_allowlisted_value_that_bypasses_via_key_match_is_still_valid_yaml():
    # "dummy" is on the placeholder allow-list, but a key-name match must
    # still redact it (existing, intentional behavior) - and the result
    # must still be valid YAML even though the original value was unquoted.
    out, entries = _redact_yaml_line("session_key: dummy\n")
    assert entries
    yaml.safe_load(out)


# ---------------------------------------------------------------------
# The security invariant, specifically for YAML
# ---------------------------------------------------------------------

def test_yaml_redaction_never_leaks_the_original_value():
    cases = [
        "endpoint: https://fake.internal.example.com/api\n",
        "db_password: fakeSup3rSecret!2024\n",
        'encryption_key: "fake-MFEwEQYHKoZIzj0"\n',
        "session_key: dummy\n",
    ]
    for line in cases:
        out, entries = _redact_yaml_line(line)
        for entry in entries:
            assert entry["before"] not in out, f"leak for {line!r} -> {out!r}"


# ---------------------------------------------------------------------
# A full multi-line YAML document, parsed end-to-end after sanitization
# ---------------------------------------------------------------------

def test_full_yaml_document_is_valid_after_sanitization(tmp_path):
    doc = (
        "service:\n"
        "  name: benchmark-service\n"
        "  environment: production\n"
        "  port: 8080\n"
        "  endpoint: https://fake.internal.example.com/api\n"
        '  encryption_key: "fake-MFEwEQYHKoZIzj0"\n'
        "  session_key: dummy\n"
        "  region: us-east-1\n"
    )
    project = tmp_path / "project"
    project.mkdir()
    (project / "settings.yaml").write_text(doc, encoding="utf-8")
    output_dir = tmp_path / "out"
    engine.scan_project(project, output_dir, _rules())

    sanitized = (output_dir / "settings.yaml").read_text(encoding="utf-8")
    parsed = yaml.safe_load(sanitized)  # must not raise
    assert parsed["service"]["endpoint"] == "***REDACTED***"
    assert "fake.internal.example.com" not in sanitized
    assert parsed["service"]["environment"] == "production"
    assert parsed["service"]["port"] == 8080


# ---------------------------------------------------------------------
# YAML block scalars (multi-line values via "|"/">") - documents current,
# pre-existing behavior honestly rather than asserting it is fully solved.
# This engine has no YAML block-scalar-aware multi-line secret detection
# (multiline handling only exists for source-code concatenation - see
# scan_multiline_python/scan_multiline_plus, never invoked for "config"
# classified files). This test exists to make that gap visible and
# regression-tested, not to claim it's fixed.
# ---------------------------------------------------------------------

def test_yaml_block_scalar_header_is_left_alone_not_corrupted():
    doc = (
        "private_key: |\n"
        "  fake multiline secret body line one\n"
        "  fakeMultilineKeyBodyContentThatWouldBeASecret\n"
        "  fake multiline secret body line three\n"
    )
    rules = _rules()
    entries = []
    out_lines = [
        engine.redact_config_line(l, rules, entries, "settings.yaml", i + 1)
        for i, l in enumerate(doc.splitlines(keepends=True))
    ]
    out = "".join(out_lines)

    # The header line ("private_key: |") is a block-scalar indicator, not
    # a redactable leaf value - redacting just the "|" would strip the
    # block-scalar syntax while leaving its indented body behind with
    # nothing to attach it to, corrupting the document. Leaving it alone
    # leaks nothing (neither "private_key" nor "|" is secret), and the
    # document - unlike before this fix - is unchanged, i.e. exactly as
    # valid or invalid as the original.
    assert out == doc
    assert entries == []
    parsed_before = yaml.safe_load(doc)
    parsed_after = yaml.safe_load(out)
    assert parsed_before == parsed_after

    # KNOWN GAP (not fixed here - see BENCHMARK.md limitations): the real
    # multi-line secret body below the block-scalar header is NOT detected
    # or redacted at all, because redact_config_line only ever looks at
    # one physical line at a time and this content doesn't match any
    # key: value shape. This was already true before this fix.
    assert "fakeMultilineKeyBodyContentThatWouldBeASecret" in out


@pytest.mark.parametrize("indicator", ["|", ">", "|-", "|+", ">-", ">+", "|2", ">-4"])
def test_yaml_block_scalar_indicator_variants_are_left_alone(indicator):
    out, entries = _redact_yaml_line(f"password: {indicator}\n")
    assert entries == []
    assert out == f"password: {indicator}\n"


def test_yaml_value_that_merely_starts_with_pipe_is_not_mistaken_for_a_block_scalar():
    # Must not over-match: only a BARE "|"/">" (block-scalar indicator) is
    # skipped - an actual value that happens to start with one of these
    # characters is still a real, redactable value.
    out, entries = _redact_yaml_line("password: |not-a-block-scalar\n")
    assert entries
    assert "|not-a-block-scalar" not in out


# ---------------------------------------------------------------------
# force_quote is strictly gated by file extension - every other format
# must keep producing exactly the same (unquoted) bare MASK as before.
# ---------------------------------------------------------------------

@pytest.mark.parametrize("filename,line", [
    ("app.properties", "password = fake-Sup3rSecret\n"),
    ("config/.env", "PASSWORD=fake-Sup3rSecret\n"),
    ("settings.ini", "password = fake-Sup3rSecret\n"),
    ("settings.conf", "password = fake-Sup3rSecret\n"),
    ("settings.cfg", "password = fake-Sup3rSecret\n"),
])
def test_non_yaml_formats_still_get_a_bare_unquoted_mask(filename, line):
    rules = _rules()
    entries = []
    out = engine.redact_config_line(line, rules, entries, filename, 1)
    assert entries
    assert '"***REDACTED***"' not in out
    assert "***REDACTED***" in out


def test_json_and_xml_and_dotconfig_unaffected_by_the_yaml_fix():
    rules = _rules()

    entries = []
    out = engine.redact_config_line('  "password": "fake-hunter2",\n', rules, entries, "appsettings.json", 1)
    assert out.strip() == '"password": "***REDACTED***",'

    entries = []
    out = engine.redact_config_line("<password>fake-password</password>\n", rules, entries, "settings.xml", 1)
    assert out.strip() == "<password>***REDACTED***</password>"

    entries = []
    out = engine.redact_config_line('<add key="password" value="fake-password"/>\n', rules, entries, "Web.config", 1)
    assert 'value="***REDACTED***"' in out
