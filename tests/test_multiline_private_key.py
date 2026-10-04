"""
Multi-line private-key block detection in the unrecognized-file fallback
(process_fallback_file()/_mask_multiline_private_key_blocks()): unlike
rules_default.yaml's private_key_block value_pattern (which only ever
matches within one physical line - see redact_value_patterns_only()), a
REAL multi-line key (id_rsa, server.pem, ...) spans many lines and needed
its own, separate detector.

All values below are synthetic and clearly fake.
"""
from pathlib import Path

import engine

_RULES_PATH = Path(engine.__file__).resolve().parent / "rules_default.yaml"


def _rules():
    return engine.load_rules(_RULES_PATH)


def _scan_single_file(tmp_path, filename, content, **kwargs):
    project = tmp_path / "project"
    project.mkdir()
    (project / filename).write_text(content, encoding="utf-8", newline="")
    output_dir = tmp_path / "out"
    entries, files_scanned, files_skipped = engine.scan_project(project, output_dir, _rules(), **kwargs)
    written = (output_dir / filename).read_text(encoding="utf-8")
    return entries, files_scanned, files_skipped, written


_ID_RSA = (
    "-----BEGIN RSA PRIVATE KEY-----\n"
    "MIIEpQIBAAKCAQEA1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJ\n"
    "KLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJ\n"
    "KLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz==\n"
    "-----END RSA PRIVATE KEY-----\n"
)


def test_realistic_id_rsa_fixture_is_masked_and_line_count_preserved(tmp_path):
    entries, scanned, _, written = _scan_single_file(tmp_path, "id_rsa", _ID_RSA)
    assert scanned == 1
    assert len(entries) == 1
    assert entries[0]["rule"] == "fallback:private_key_block"
    assert entries[0]["key"] is None
    assert entries[0]["line"] == 1
    assert "MIIEpQIBAAKCAQEA" not in written
    assert written.startswith("-----BEGIN RSA PRIVATE KEY-----\n")
    assert written.rstrip("\n").endswith("-----END RSA PRIVATE KEY-----")
    assert len(written.splitlines()) == len(_ID_RSA.splitlines())


_SERVER_PEM_CRLF = (
    "-----BEGIN EC PRIVATE KEY-----\r\n"
    "MIIFAKEFAKEFAKEFAKEFAKEFAKEFAKE\r\n"
    "MOREFAKEDATAHEREFAKEFAKEFAKEFAKE\r\n"
    "-----END EC PRIVATE KEY-----\r\n"
)


def test_realistic_server_pem_fixture_with_crlf_is_masked(tmp_path):
    entries, scanned, _, written = _scan_single_file(tmp_path, "server.pem", _SERVER_PEM_CRLF)
    assert len(entries) == 1
    assert entries[0]["rule"] == "fallback:private_key_block"
    assert "MIIFAKEFAKE" not in written
    assert "-----BEGIN EC PRIVATE KEY-----" in written
    assert "-----END EC PRIVATE KEY-----" in written
    # 4 physical lines in, regardless of \r\n vs \n - line count preserved.
    assert len(written.splitlines()) == 4


def test_txt_file_containing_a_key_block_is_masked(tmp_path):
    content = f"Here is a key dump for debugging:\n{_ID_RSA}End of dump.\n"
    entries, scanned, _, written = _scan_single_file(tmp_path, "notes.txt", content)
    assert len(entries) == 1
    assert entries[0]["rule"] == "fallback:private_key_block"
    assert entries[0]["line"] == 2  # the BEGIN line, after the first text line
    assert "MIIEpQIBAAKCAQEA" not in written
    assert "Here is a key dump for debugging:" in written
    assert "End of dump." in written
    assert len(written.splitlines()) == len(content.splitlines())


def test_truncated_key_with_no_end_line_is_masked_to_end_of_file(tmp_path):
    truncated = (
        "-----BEGIN OPENSSH PRIVATE KEY-----\n"
        "b3BlbnNzaC1rZXktdjEAAAAABG5vbmUFAKEFAKEFAKEFAKEFAKE\n"
        "AAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZWQyNTUxOUFAKE\n"
    )
    entries, scanned, _, written = _scan_single_file(tmp_path, "id_ed25519", truncated)
    assert len(entries) == 1
    assert entries[0]["rule"] == "fallback:private_key_block"
    assert "b3BlbnNzaC1rZXktdjEAAAAABG5vbmU" not in written
    assert "AAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZWQyNTUx" not in written
    assert written.startswith("-----BEGIN OPENSSH PRIVATE KEY-----\n")
    assert len(written.splitlines()) == len(truncated.splitlines())


def test_certificate_block_is_not_masked(tmp_path):
    cert = (
        "-----BEGIN CERTIFICATE-----\n"
        "MIIBFAKECERTDATAHEREFAKEFAKEFAKEFAKE1234567890\n"
        "-----END CERTIFICATE-----\n"
    )
    entries, scanned, _, written = _scan_single_file(tmp_path, "cert.pem", cert)
    assert entries == []
    assert written == cert


def test_single_line_escaped_newline_pem_still_caught(tmp_path):
    # The pre-existing single-line case (rules_default.yaml's
    # private_key_block value_pattern, via the ordinary per-line fallback
    # pass) - a key pasted as one physical line with literal "\n" escapes,
    # e.g. a JSON/.env-style value. Must keep working unchanged alongside
    # the new multi-line detector.
    pem = "-----BEGIN RSA PRIVATE KEY-----\\nMIIFAKEFAKEFAKEFAKEFAKEFAKEFAKE\\n-----END RSA PRIVATE KEY-----\n"
    entries, scanned, _, written = _scan_single_file(tmp_path, "id_rsa.bak", pem)
    assert len(entries) == 1
    assert entries[0]["rule"] == "fallback:private_key_block"
    assert "MIIFAKEFAKE" not in written


def test_multiline_key_block_respects_ignore_with_no_key(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "id_rsa").write_text(_ID_RSA, encoding="utf-8")
    output_dir = tmp_path / "out"

    value_hash = engine.hash_value(_ID_RSA)
    ignore_map = {("id_rsa", None, "fallback:private_key_block"): value_hash}

    entries, scanned, _ = engine.scan_project(project, output_dir, _rules(), ignore_map=ignore_map)
    assert entries == [], "a multi-line key finding (key=None) must be suppressible via the ignore system"
    written = (output_dir / "id_rsa").read_text(encoding="utf-8")
    assert written == _ID_RSA, "ignored - the real multi-line key passes through byte-for-byte"


def test_multiline_key_block_respects_placeholder_mode(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "a_key").write_text(_ID_RSA, encoding="utf-8")
    (project / "b_key").write_text(_ID_RSA, encoding="utf-8")
    output_dir = tmp_path / "out"

    entries, scanned, _ = engine.scan_project(project, output_dir, _rules(), placeholder_mode=True)
    assert scanned == 2
    assert len(entries) == 2
    written_a = (output_dir / "a_key").read_text(encoding="utf-8")
    written_b = (output_dir / "b_key").read_text(encoding="utf-8")
    assert "<PRIVATE_KEY_1>" in written_a
    assert "<PRIVATE_KEY_1>" in written_b, "same real key, same deterministic placeholder token across files"
    assert "MIIEpQIBAAKCAQEA" not in written_a


def test_yaml_block_scalar_pem_is_not_caught_known_pre_existing_limitation(tmp_path):
    """Investigative, not a requirement: YAML block-scalar bodies are
    already documented (README.md) as not scanned at all - confirms a
    multi-line PEM pasted as a block-scalar value falls under that same
    existing, pre-existing limitation rather than being newly broken by
    this feature. Deliberately not fixed here - out of this task's scope."""
    yml = (
        "private_key: |\n"
        "  -----BEGIN RSA PRIVATE KEY-----\n"
        "  MIIFAKEDATA1234567890ABCDEFGHIJ\n"
        "  -----END RSA PRIVATE KEY-----\n"
    )
    entries, scanned, _, written = _scan_single_file(tmp_path, "config.yml", yml)
    assert entries == []
    assert "MIIFAKEDATA1234567890ABCDEFGHIJ" in written


def test_properties_continuation_pem_is_not_caught_known_pre_existing_limitation(tmp_path):
    """Investigative, not a requirement: engine.py has no line-continuation
    joining for .properties files at all (each line is parsed
    independently) - a key pasted across several backslash-continued
    lines was never caught before this feature and still isn't.
    Deliberately not fixed here - out of this task's scope."""
    props = (
        "server.key=-----BEGIN RSA PRIVATE KEY-----\\\n"
        "MIIFAKEDATA1234567890ABCDEFGHIJ\\\n"
        "-----END RSA PRIVATE KEY-----\n"
    )
    entries, scanned, _, written = _scan_single_file(tmp_path, "app.properties", props)
    assert entries == []
    assert "MIIFAKEDATA1234567890ABCDEFGHIJ" in written
