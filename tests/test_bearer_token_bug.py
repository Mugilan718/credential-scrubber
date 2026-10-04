"""
bearer_token regression tests (see rules_default.yaml's comment on the
pattern): previously, "(?i)bearer\\s+[A-Za-z0-9\\-._~+/]+=*" matched ordinary
prose ("a bearer token in the header") because any single word after
"bearer" satisfied it, and the placeholder allow-list was checked against
the WHOLE match ("Bearer YOUR_TOKEN_HERE") instead of just the token
portion, so a documented placeholder was never recognized as one. Fixed by
(1) a {20,} minimum length on the token, and (2) capturing the token in a
group so is_placeholder() can check it in isolation (see
_value_pattern_placeholder_check_text()).

All values below are synthetic and clearly fake.
"""
from pathlib import Path

import engine

_RULES_PATH = Path(engine.__file__).resolve().parent / "rules_default.yaml"


def _rules():
    return engine.load_rules(_RULES_PATH)


def _scan_single_file(tmp_path, filename, content):
    project = tmp_path / "project"
    project.mkdir()
    (project / filename).write_text(content, encoding="utf-8")
    output_dir = tmp_path / "out"
    entries, files_scanned, files_skipped = engine.scan_project(project, output_dir, _rules())
    written = (output_dir / filename).read_text(encoding="utf-8")
    return entries, files_scanned, files_skipped, written


def test_bearer_prose_is_not_flagged(tmp_path):
    entries, scanned, _, written = _scan_single_file(
        tmp_path, "AUTH.rst", "Send requests with a bearer token in the Authorization header.\n"
    )
    assert entries == []
    assert "bearer token" in written


def test_bearer_placeholder_is_not_flagged(tmp_path):
    entries, scanned, _, written = _scan_single_file(
        tmp_path, "AUTH.rst", "Authorization: Bearer YOUR_BEARER_TOKEN_HERE\n"
    )
    assert entries == []
    assert "YOUR_BEARER_TOKEN_HERE" in written


def test_realistic_bearer_token_is_still_redacted(tmp_path):
    # bearer_token isn't in the unrecognized-file fallback's high-confidence
    # subset (see FALLBACK_VALUE_PATTERN_NAMES) - use a recognized config
    # file so this exercises the full value_patterns list, same as before
    # the fallback feature existed.
    fake_token = "qXz9K2mN8pL4vR7tY1wA6sD3fG5hJ0cE9rT2"
    entries, scanned, _, written = _scan_single_file(
        tmp_path, "auth.properties", f"Authorization: Bearer {fake_token}\n"
    )
    assert len(entries) == 1
    assert entries[0]["rule"] == "bearer_token"
    assert fake_token not in written


def test_bearer_placeholder_in_config_file_is_not_flagged():
    # The config-line path (redact_config_line) has its own, separate
    # is_placeholder() check from the fallback/non-key-shaped-line path -
    # both needed the same group-aware fix.
    rules = _rules()
    entries = []
    line = 'Authorization: Bearer YOUR_BEARER_TOKEN_HERE\n'
    result = engine.redact_config_line(line, rules, entries, "settings.properties", 1)
    assert entries == []
    assert result == line


def test_realistic_bearer_token_in_config_file_is_still_redacted():
    rules = _rules()
    entries = []
    fake_token = "qXz9K2mN8pL4vR7tY1wA6sD3fG5hJ0cE9rT2"
    line = f"Authorization: Bearer {fake_token}\n"
    result = engine.redact_config_line(line, rules, entries, "settings.properties", 1)
    assert len(entries) == 1
    assert entries[0]["rule"] == "bearer_token"
    assert fake_token not in result
