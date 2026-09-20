"""
Ignore feature + hash-verification, and end-to-end scan_project behavior
(including changed-files-only / git-diff mode).

All values below are synthetic and clearly fake.
"""
import subprocess
from pathlib import Path

import engine

_RULES_PATH = Path(engine.__file__).resolve().parent / "rules_default.yaml"


def _rules():
    return engine.load_rules(_RULES_PATH)


# ---------------------------------------------------------------------
# Ignore + hash verification
# ---------------------------------------------------------------------

def test_ignored_finding_is_suppressed():
    rules = _rules()
    # check_ignore hashes the raw captured value exactly as find_key_value
    # returns it (quotes included for a quoted config value) - use an
    # unquoted value here so the hash input is unambiguous.
    value_hash = engine.hash_value("fake-secret-1")
    ignore_map = {("f.properties", "password", "key_name_match"): value_hash}
    entries = []
    out = engine.redact_config_line('password = fake-secret-1\n', rules, entries, "f.properties", 1, ignore_map)
    assert out == 'password = fake-secret-1\n'  # untouched - explicitly ignored
    assert entries == []


def test_ignored_finding_whose_value_changed_is_not_suppressed_and_is_flagged():
    rules = _rules()
    stale_hash = engine.hash_value("fake-old-value")
    ignore_map = {("f.properties", "password", "key_name_match"): stale_hash}
    entries = []
    out = engine.redact_config_line('password = "fake-NEW-value"\n', rules, entries, "f.properties", 1, ignore_map)
    assert "fake-NEW-value" not in out
    assert entries[0]["previously_ignored_value_changed"] is True


def test_ignore_with_no_recorded_hash_always_reflags():
    rules = _rules()
    ignore_map = {("f.properties", "password", "key_name_match"): None}
    entries = []
    engine.redact_config_line('password = "fake-value"\n', rules, entries, "f.properties", 1, ignore_map)
    assert entries and entries[0]["previously_ignored_value_changed"] is True


# ---------------------------------------------------------------------
# scan_project end-to-end
# ---------------------------------------------------------------------

def test_scan_project_never_modifies_the_input(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    original_text = 'password = "fake-Sup3rSecret!"\n'
    (project / "app.properties").write_text(original_text, encoding="utf-8")

    output_dir = tmp_path / "out"
    engine.scan_project(project, output_dir, _rules())

    assert (project / "app.properties").read_text(encoding="utf-8") == original_text


def test_scan_project_redacts_into_output_dir(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.properties").write_text('password = "fake-Sup3rSecret!"\n', encoding="utf-8")

    output_dir = tmp_path / "out"
    entries, files_scanned, files_skipped = engine.scan_project(project, output_dir, _rules())

    sanitized = (output_dir / "app.properties").read_text(encoding="utf-8")
    assert "fake-Sup3rSecret!" not in sanitized
    assert files_scanned == 1
    assert files_skipped == []
    assert len(entries) == 1


def test_unclassified_extension_is_copied_through_untouched(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "notes.txt").write_text('password = "fake-Sup3rSecret!"\n', encoding="utf-8")

    output_dir = tmp_path / "out"
    entries, files_scanned, _ = engine.scan_project(project, output_dir, _rules())

    # .txt isn't a CONFIG_EXTENSIONS/CODE_EXTENSIONS member, but
    # process_file's fallback path (redact_value_patterns_only) still runs
    # for it via classify_file() returning None -> shutil.copy2 (no scan at
    # all) - confirm today's actual behavior rather than assume it.
    copied = (output_dir / "notes.txt").read_text(encoding="utf-8")
    assert copied == 'password = "fake-Sup3rSecret!"\n'
    assert files_scanned == 0


# ---------------------------------------------------------------------
# changed-files-only (git-diff) mode
# ---------------------------------------------------------------------

def _init_git_repo(path):
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)


def test_changed_files_only_scans_only_the_changed_file(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    _init_git_repo(project)

    (project / "unchanged.properties").write_text('password = "fake-old-Secret1"\n', encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=project, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=project, check=True)

    (project / "changed.properties").write_text('password = "fake-new-Secret2"\n', encoding="utf-8")

    output_dir = tmp_path / "out"
    entries, files_scanned, _ = engine.scan_project(project, output_dir, _rules(), changed_files_only=True)

    assert (output_dir / "changed.properties").exists()
    assert not (output_dir / "unchanged.properties").exists()
    assert files_scanned == 1


def test_changed_files_only_raises_on_non_git_dir(tmp_path):
    import pytest

    project = tmp_path / "not_a_repo"
    project.mkdir()
    (project / "f.properties").write_text("a=b\n", encoding="utf-8")

    with pytest.raises(engine.NotAGitRepoError):
        engine.scan_project(project, tmp_path / "out", _rules(), changed_files_only=True)
