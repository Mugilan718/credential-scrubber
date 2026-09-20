"""
Permanent regression tests for the bugs found during the security audit
(2026-09). Each test pins the exact repro that demonstrated the bug, so a
future change can't silently reintroduce it.

All values below are synthetic and clearly fake - never real credentials.
"""
from pathlib import Path

import engine

_RULES_PATH = Path(engine.__file__).resolve().parent / "rules_default.yaml"


def _rules():
    return engine.load_rules(_RULES_PATH)


# ---------------------------------------------------------------------
# F2 - same-substring redaction used to mask the wrong span, leaving the
# real secret in the "sanitized" output while the report claimed success.
# ---------------------------------------------------------------------

def test_f2_key_and_value_share_text_masks_the_value_not_the_key():
    # Before the fix: line.replace("secret", MASK, 1) hit the FIRST
    # occurrence of "secret" in the whole line - the one inside the key
    # name - leaving the real value untouched. The key name legitimately
    # containing the word "secret" is not itself a leak; what matters is
    # that the output is exactly "key=MASK", not "MASK_key=secret".
    rules = _rules()
    entries = []
    out = engine.redact_config_line('secret_key=secret\n', rules, entries, "f.properties", 1)
    assert out.strip() == "secret_key=***REDACTED***"
    assert entries[0]["before"] == "secret"


def test_f2_password_equals_password():
    rules = _rules()
    entries = []
    out = engine.redact_config_line('password=password\n', rules, entries, "f.properties", 1)
    assert out.strip() == "password=***REDACTED***"


def test_f2_quoted_value_sharing_text_with_key():
    rules = _rules()
    entries = []
    out = engine.redact_config_line('secret_key = "secret"\n', rules, entries, "f.properties", 1)
    assert out.strip() == 'secret_key = "***REDACTED***"'


# ---------------------------------------------------------------------
# F1 - key-name protection used to silently not apply to JSON keys, XML
# elements, and .config (XML attribute) shapes.
# ---------------------------------------------------------------------

def test_f1_json_quoted_key_is_detected():
    rules = _rules()
    entries = []
    out = engine.redact_config_line('  "password": "fake-supersecret123",\n', rules, entries, "f.json", 1)
    assert "fake-supersecret123" not in out
    assert entries and entries[0]["key"] == "password" and entries[0]["rule"] == "key_name_match"
    assert out.strip() == '"password": "***REDACTED***",'


def test_f1_json_short_low_entropy_secret_is_still_caught_via_key_name():
    # This is the exact case that used to slip through entirely: a short,
    # human, low-entropy value that only the (previously-bypassed) key-name
    # path would ever catch.
    rules = _rules()
    entries = []
    out = engine.redact_config_line('  "db_password" : "hunter2",\n', rules, entries, "f.json", 1)
    assert "hunter2" not in out
    assert entries[0]["rule"] == "key_name_match"


def test_f1_xml_element_is_detected():
    rules = _rules()
    entries = []
    out = engine.redact_config_line('<password>fake-password</password>\n', rules, entries, "f.xml", 1)
    assert "fake-password" not in out
    assert out.strip() == "<password>***REDACTED***</password>"


def test_f1_dotnet_config_attribute_pair_is_detected():
    rules = _rules()
    entries = []
    line = '    <add key="password" value="fake-password"/>\n'
    out = engine.redact_config_line(line, rules, entries, "Web.config", 1)
    assert "fake-password" not in out
    assert 'key="password"' in out  # the key attribute itself is untouched
    assert 'value="***REDACTED***"' in out


def test_f1_dotnet_config_connection_string_attribute():
    rules = _rules()
    entries = []
    line = '<add key="ConnectionString" value="Server=fake-host;Password=fake-Sup3rSecret!"/>\n'
    out = engine.redact_config_line(line, rules, entries, "Web.config", 1)
    assert "fake-Sup3rSecret!" not in out
    assert entries and entries[0]["key"] == "ConnectionString"


def test_f1_dotconfig_extension_is_classified_as_config():
    assert engine.classify_file(Path("Web.config")) == "config"
    assert engine.classify_file(Path("App.config")) == "config"


def test_f1_json_object_opener_is_not_treated_as_a_scalar_value():
    # "auth": { on its own line opens a multi-line nested object - treating
    # "{" as a complete replaceable value would corrupt the JSON (the
    # matching "}" appears many lines later).
    rules = _rules()
    entries = []
    out = engine.redact_config_line('  "auth": {\n', rules, entries, "f.json", 1)
    assert out == '  "auth": {\n'
    assert entries == []


# ---------------------------------------------------------------------
# F4 - scanning used to follow symlinks with no boundary check.
# ---------------------------------------------------------------------

def test_f4_symlink_check_fires_even_without_privilege_to_create_one(tmp_path, monkeypatch):
    # Real symlink creation needs elevated privileges/Developer Mode on
    # Windows (WinError 1314 otherwise) and may not be available in every
    # environment this suite runs in - this test exercises the same guard
    # in scan_project() by monkeypatching is_symlink() instead, so the
    # regression is still caught even where a real symlink can't be made.
    project = tmp_path / "project"
    project.mkdir()
    (project / "config.env").write_text("API_KEY=fake-should-be-skipped\n", encoding="utf-8")

    monkeypatch.setattr(Path, "is_symlink", lambda self: self.name == "config.env")

    output_dir = tmp_path / "out"
    entries, files_scanned, files_skipped = engine.scan_project(project, output_dir, _rules())

    assert files_scanned == 0
    assert "config.env" in files_skipped
    assert not (output_dir / "config.env").exists()
    assert entries == []


def test_f4_symlinked_file_is_skipped_not_followed(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    secret_target = outside / "real_secret.env"
    secret_target.write_text("API_KEY=fake-should-never-be-read\n", encoding="utf-8")

    project = tmp_path / "project"
    project.mkdir()
    link = project / "config.env"
    try:
        link.symlink_to(secret_target)
    except (OSError, NotImplementedError):
        import pytest
        pytest.skip("symlink creation not permitted in this environment")

    output_dir = tmp_path / "out"
    rules = _rules()
    entries, files_scanned, files_skipped = engine.scan_project(project, output_dir, rules)

    assert files_scanned == 0
    assert "config.env" in files_skipped
    assert not (output_dir / "config.env").exists()
    assert entries == []
