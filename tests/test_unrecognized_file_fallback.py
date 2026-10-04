"""
The unrecognized-file fallback (process_fallback_file()): a file whose
extension classify_file() doesn't recognize (a lockfile, a Dockerfile, a
.rb script, a README, ...) used to be copied through scan_project()
completely untouched. It's now scanned for a high-confidence subset of
value_patterns (FALLBACK_VALUE_PATTERN_NAMES) instead of the full set, under
guards: skip known-binary extensions and null-byte content, skip files over
FALLBACK_MAX_BYTES, skip symlinks/SKIP_DIRS/excluded paths (shared with every
other scan path via _walk_and_classify()).

All values below are synthetic and clearly fake.
"""
from pathlib import Path

import engine

_RULES_PATH = Path(engine.__file__).resolve().parent / "rules_default.yaml"


def _rules():
    return engine.load_rules(_RULES_PATH)


# ---------------------------------------------------------------------
# One positive fixture per FALLBACK_VALUE_PATTERN_NAMES pattern - proves
# each of the seven high-confidence patterns actually fires on an
# unrecognized-extension file, not just aws_access_key_id (the only one
# the noise-measurement sample happened to exercise).
# ---------------------------------------------------------------------

def _scan_single_file(tmp_path, filename, content):
    project = tmp_path / "project"
    project.mkdir()
    (project / filename).write_text(content, encoding="utf-8")
    output_dir = tmp_path / "out"
    entries, files_scanned, files_skipped = engine.scan_project(project, output_dir, _rules())
    written = (output_dir / filename).read_text(encoding="utf-8")
    return entries, files_scanned, files_skipped, written


def test_fallback_redacts_aws_access_key_id(tmp_path):
    entries, scanned, _, written = _scan_single_file(
        tmp_path, "config.rb", 'aws_key = "AKIAIOSFODNN7EXAMPLE"\n'
    )
    assert scanned == 1
    assert len(entries) == 1
    assert entries[0]["rule"] == "fallback:aws_access_key_id"
    assert entries[0]["key"] is None
    assert "AKIAIOSFODNN7EXAMPLE" not in written


def test_fallback_redacts_aws_secret_key_assignment(tmp_path):
    fake_secret = "FAKEfakeFAKEfakeFAKEfakeFAKEfakeFAKEfake"[:40]
    entries, scanned, _, written = _scan_single_file(
        tmp_path, "config.rb", f'aws_secret_access_key = "{fake_secret}"\n'
    )
    assert scanned == 1
    assert len(entries) == 1
    assert entries[0]["rule"] == "fallback:aws_secret_key_assignment"
    assert fake_secret not in written


def test_fallback_redacts_github_token(tmp_path):
    fake_token = "ghp_" + "A" * 36
    entries, scanned, _, written = _scan_single_file(
        tmp_path, "deploy.rb", f"token = '{fake_token}'\n"
    )
    assert scanned == 1
    assert len(entries) == 1
    assert entries[0]["rule"] == "fallback:github_token"
    assert fake_token not in written


def test_fallback_redacts_slack_token(tmp_path):
    fake_token = "xoxb-" + "1234567890" * 2
    entries, scanned, _, written = _scan_single_file(
        tmp_path, "notify.rb", f"SLACK_TOKEN = '{fake_token}'\n"
    )
    assert scanned == 1
    assert len(entries) == 1
    assert entries[0]["rule"] == "fallback:slack_token"
    assert fake_token not in written


def test_fallback_redacts_jwt_token(tmp_path):
    fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dummysignaturevalue"
    entries, scanned, _, written = _scan_single_file(
        tmp_path, "session.rb", f"token = '{fake_jwt}'\n"
    )
    assert scanned == 1
    assert len(entries) == 1
    assert entries[0]["rule"] == "fallback:jwt_token"
    assert fake_jwt not in written


def test_fallback_redacts_private_key_block(tmp_path):
    # private_key_block's regex spans BEGIN...END, but redact_value_patterns_only
    # (used by every caller, not just the fallback) matches one physical LINE
    # at a time - a real multi-line PEM block (one BEGIN/body/END per line)
    # is a known, pre-existing engine limitation this task doesn't change.
    # A single-line escaped-newline PEM (the realistic shape for a key pasted
    # into a .env/JSON value, e.g. GOOGLE_APPLICATION_CREDENTIALS-style) is
    # what this pattern actually catches in practice, and does fit on one line.
    pem = "-----BEGIN RSA PRIVATE KEY-----\\nMIIFAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKE\\n-----END RSA PRIVATE KEY-----\n"
    entries, scanned, _, written = _scan_single_file(tmp_path, "id_rsa.bak", pem)
    assert scanned == 1
    assert len(entries) == 1
    assert entries[0]["rule"] == "fallback:private_key_block"
    assert "MIIFAKEFAKE" not in written


def test_fallback_redacts_url_with_credentials(tmp_path):
    entries, scanned, _, written = _scan_single_file(
        tmp_path, "notes.rb", "endpoint = 'https://user:hunter2@example.com/db'\n"
    )
    assert scanned == 1
    assert len(entries) == 1
    assert entries[0]["rule"] == "fallback:url_with_credentials"
    assert "hunter2" not in written


# ---------------------------------------------------------------------
# Near-miss negatives - shapes that would fire under the FULL value_patterns
# list (as the noise measurement showed) but must NOT fire once the
# fallback is restricted to FALLBACK_VALUE_PATTERN_NAMES.
# ---------------------------------------------------------------------

def test_fallback_does_not_redact_version_number(tmp_path):
    entries, scanned, _, written = _scan_single_file(
        tmp_path, "Gemfile.lock", "    rails (7.0.4.3)\n"
    )
    assert scanned == 1
    assert entries == []
    assert "7.0.4.3" in written


def test_fallback_does_not_redact_plain_url(tmp_path):
    entries, scanned, _, written = _scan_single_file(
        tmp_path, "README.rst", "API docs: https://api.example.com/v1/health\n"
    )
    assert scanned == 1
    assert entries == []
    assert "https://api.example.com/v1/health" in written


def test_fallback_does_not_redact_email_address(tmp_path):
    entries, scanned, _, written = _scan_single_file(
        tmp_path, "CONTRIBUTING.rst", "Questions: dev-team@example.com\n"
    )
    assert scanned == 1
    assert entries == []
    assert "dev-team@example.com" in written


def test_fallback_does_not_redact_bearer_token_prose(tmp_path):
    entries, scanned, _, written = _scan_single_file(
        tmp_path, "AUTH.rst", "Send requests with a bearer token in the Authorization header.\n"
    )
    assert scanned == 1
    assert entries == []
    assert "bearer token" in written


# ---------------------------------------------------------------------
# Documented limits called out explicitly by the task - a key-name-only
# "looks like a secret" is NOT caught by the fallback (no config/code
# key-name awareness exists for files classify_file() doesn't recognize).
# ---------------------------------------------------------------------

def test_rb_aws_key_is_redacted_but_plain_password_is_not(tmp_path):
    entries, scanned, _, written = _scan_single_file(
        tmp_path, "config.rb",
        'password = "hunter2"\naws_key = "AKIAIOSFODNN7EXAMPLE"\n',
    )
    assert scanned == 1
    assert len(entries) == 1
    assert entries[0]["rule"] == "fallback:aws_access_key_id"
    assert 'password = "hunter2"' in written
    assert "AKIAIOSFODNN7EXAMPLE" not in written


def test_dockerfile_env_password_is_not_redacted(tmp_path):
    entries, scanned, _, written = _scan_single_file(
        tmp_path, "Dockerfile", "FROM ubuntu:22.04\nENV DB_PASSWORD=hunter2\n"
    )
    assert scanned == 1
    assert entries == []
    assert "ENV DB_PASSWORD=hunter2" in written


# ---------------------------------------------------------------------
# Guards: binary, oversize, symlink.
# ---------------------------------------------------------------------

def test_fallback_skips_binary_file_by_extension(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "photo.png").write_bytes(b"\x89PNG\r\n\x1a\nAKIAIOSFODNN7EXAMPLE")
    output_dir = tmp_path / "out"
    entries, scanned, skipped = engine.scan_project(project, output_dir, _rules())
    assert entries == []
    assert scanned == 0
    assert (output_dir / "photo.png").read_bytes() == b"\x89PNG\r\n\x1a\nAKIAIOSFODNN7EXAMPLE"


def test_fallback_skips_file_with_null_byte_even_without_binary_extension(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "mystery.dat").write_bytes(b"AKIAIOSFODNN7EXAMPLE\x00\x01\x02")
    output_dir = tmp_path / "out"
    entries, scanned, skipped = engine.scan_project(project, output_dir, _rules())
    assert entries == []
    assert scanned == 0
    assert (output_dir / "mystery.dat").read_bytes() == b"AKIAIOSFODNN7EXAMPLE\x00\x01\x02"


def test_fallback_skips_file_over_size_limit_and_reports_it_as_unscanned(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    big_content = 'password = "hunter2"\n' + ("x" * (engine.FALLBACK_MAX_BYTES + 100))
    (project / "huge.rb").write_text(big_content, encoding="utf-8")
    output_dir = tmp_path / "out"

    entries, _, _, staged_files, _, unscanned_files = engine.stage_project(project, output_dir, _rules())
    assert entries == []
    assert unscanned_files == [{"rel_path": "huge.rb", "reason": "oversize"}]
    assert staged_files[0]["content"] is None
    assert staged_files[0]["src_path"] is not None


def test_fallback_still_skips_symlinks(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    real = tmp_path / "real_secret.rb"
    real.write_text('aws_key = "AKIAIOSFODNN7EXAMPLE"\n', encoding="utf-8")
    link = project / "linked.rb"
    try:
        link.symlink_to(real)
    except OSError:
        import pytest
        pytest.skip("symlink creation not permitted in this environment")

    output_dir = tmp_path / "out"
    entries, scanned, skipped = engine.scan_project(project, output_dir, _rules())
    assert entries == []
    assert scanned == 0
    assert skipped == ["linked.rb"]
    assert not (output_dir / "linked.rb").exists()


# ---------------------------------------------------------------------
# Unscanned-files visibility grouping.
# ---------------------------------------------------------------------

def test_unscanned_files_grouped_by_reason(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "photo.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (project / "huge.rb").write_text("x" * (engine.FALLBACK_MAX_BYTES + 10), encoding="utf-8")
    (project / "normal.rb").write_text('aws_key = "AKIAIOSFODNN7EXAMPLE"\n', encoding="utf-8")
    output_dir = tmp_path / "out"

    _, _, _, _, _, unscanned_files = engine.stage_project(project, output_dir, _rules())
    by_reason = {f["rel_path"]: f["reason"] for f in unscanned_files}
    assert by_reason == {"photo.png": "binary", "huge.rb": "oversize"}
    assert "normal.rb" not in by_reason


# ---------------------------------------------------------------------
# Ignore system + placeholder mode compatibility.
# ---------------------------------------------------------------------

def test_fallback_finding_respects_ignore_with_no_key(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "config.rb").write_text('aws_key = "AKIAIOSFODNN7EXAMPLE"\n', encoding="utf-8")
    output_dir = tmp_path / "out"

    value_hash = engine.hash_value("AKIAIOSFODNN7EXAMPLE")
    ignore_map = {("config.rb", None, "fallback:aws_access_key_id"): value_hash}

    entries, scanned, _ = engine.scan_project(project, output_dir, _rules(), ignore_map=ignore_map)
    assert entries == [], "a fallback finding (key=None) must be suppressible via the ignore system"
    written = (output_dir / "config.rb").read_text(encoding="utf-8")
    assert "AKIAIOSFODNN7EXAMPLE" in written, "ignored - the real value passes through"


def test_fallback_finding_respects_placeholder_mode(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "a.rb").write_text('key1 = "AKIAIOSFODNN7EXAMPLE"\n', encoding="utf-8")
    (project / "b.rb").write_text('key2 = "AKIAIOSFODNN7EXAMPLE"\n', encoding="utf-8")
    output_dir = tmp_path / "out"

    entries, scanned, _ = engine.scan_project(project, output_dir, _rules(), placeholder_mode=True)
    assert scanned == 2
    assert len(entries) == 2
    written_a = (output_dir / "a.rb").read_text(encoding="utf-8")
    written_b = (output_dir / "b.rb").read_text(encoding="utf-8")
    # Same real value in two different fallback-scanned files -> same
    # deterministic placeholder token (aws_access_key_id's category is
    # API_KEY), same as placeholder mode guarantees for config/code files.
    assert written_a == 'key1 = "<API_KEY_1>"\n'
    assert written_b == 'key2 = "<API_KEY_1>"\n'
    assert "AKIAIOSFODNN7EXAMPLE" not in written_a
    assert "AKIAIOSFODNN7EXAMPLE" not in written_b
