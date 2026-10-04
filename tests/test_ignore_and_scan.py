"""
Ignore feature + hash-verification, and end-to-end scan_project behavior
(including changed-files-only / git-diff mode).

All values below are synthetic and clearly fake.
"""
import subprocess
from pathlib import Path

import engine
import db

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


def test_unclassified_extension_plain_password_is_not_redacted(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "notes.txt").write_text('password = "fake-Sup3rSecret!"\n', encoding="utf-8")

    output_dir = tmp_path / "out"
    entries, files_scanned, _ = engine.scan_project(project, output_dir, _rules())

    # .txt isn't a CONFIG_EXTENSIONS/CODE_EXTENSIONS member, so classify_file()
    # returns None - but it IS scanned by the unrecognized-file fallback
    # (process_fallback_file()), restricted to FALLBACK_VALUE_PATTERN_NAMES.
    # A plain "key = value" assignment has no key-name awareness outside a
    # recognized config/code file, and this value doesn't match any of the
    # high-confidence value shapes in the fallback subset - so it passes
    # through unredacted. This is a documented limit, not a bug: the
    # fallback only catches credential-shaped VALUES (AWS keys, GitHub/Slack
    # tokens, JWTs, private-key blocks, URLs with embedded credentials), not
    # "looks like a secret because of its key name."
    copied = (output_dir / "notes.txt").read_text(encoding="utf-8")
    assert copied == 'password = "fake-Sup3rSecret!"\n'
    assert entries == []
    assert files_scanned == 1


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


# ---------------------------------------------------------------------
# Ignore-safety (Phase 1): full db + engine round trip - ignoring suppresses
# a finding on the NEXT scan, and "Restore redaction" (db.remove_ignore())
# makes the NEXT scan after that redact it again. Exercises the exact same
# ignore_map shape app.py's api_run_scan() builds from db.list_ignores(),
# not just engine.check_ignore() in isolation.
# ---------------------------------------------------------------------

def _ignore_map_for(project_id):
    return {(i["file"], i["key"], i["rule"]): i["value_hash"] for i in db.list_ignores(project_id)}


def test_restore_redaction_makes_a_later_scan_redact_the_value_again(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test_app.db")
    db.init_db()

    project = tmp_path / "project"
    project.mkdir()
    secret = "fake-Restorable-Secret-789"
    (project / "app.properties").write_text(f'password = "{secret}"\n', encoding="utf-8")
    output_dir = tmp_path / "out"

    project_id = db.create_project("Test Project", str(project), str(output_dir), {})

    # 1. First scan (nothing ignored yet) - the secret is redacted.
    entries, _, _ = engine.scan_project(project, output_dir, _rules(), ignore_map=_ignore_map_for(project_id))
    assert len(entries) == 1
    sanitized_first = (output_dir / "app.properties").read_text(encoding="utf-8")
    assert secret not in sanitized_first

    # 2. Ignore it (as app.py's api_add_ignore does: hash the real value
    # captured by this scan and store it against the (file, key, rule) triple).
    finding = entries[0]
    value_hash = engine.hash_value(finding["before"])
    db.add_ignore(project_id, finding["file"], finding["key"], finding["rule"], value_hash)

    # 3. Next scan - now suppressed, the real value is written to output.
    entries2, _, _ = engine.scan_project(project, output_dir, _rules(), ignore_map=_ignore_map_for(project_id))
    assert entries2 == []
    sanitized_second = (output_dir / "app.properties").read_text(encoding="utf-8")
    assert secret in sanitized_second, "ignored finding's real value is written once suppressed"

    # 4. Restore it (the "Restore redaction" action - db.remove_ignore(),
    # exactly what DELETE /api/projects/<id>/ignore/<ignore_id> calls).
    [ig] = db.list_ignores(project_id)
    db.remove_ignore(ig["id"])
    assert db.list_ignores(project_id) == []

    # 5. Next scan after restoring - redacted again, exactly like the very
    # first scan, proving the restore isn't just removed from a list but
    # actually changes scan behavior.
    entries3, _, _ = engine.scan_project(project, output_dir, _rules(), ignore_map=_ignore_map_for(project_id))
    assert len(entries3) == 1
    sanitized_third = (output_dir / "app.properties").read_text(encoding="utf-8")
    assert secret not in sanitized_third, "restored finding is redacted again on the next scan"


# ---------------------------------------------------------------------
# Folder-filtering tree (Phase 2): excluded_paths and list_project_files
# ---------------------------------------------------------------------

def test_list_project_files_lists_everything_except_skip_dirs(tmp_path):
    project = tmp_path / "project"
    (project / "src").mkdir(parents=True)
    (project / "node_modules" / "pkg").mkdir(parents=True)
    (project / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    (project / "top.env").write_text("A=1\n", encoding="utf-8")
    (project / "node_modules" / "pkg" / "index.js").write_text("// should never appear\n", encoding="utf-8")

    paths = engine.list_project_files(project)
    assert paths == ["src/app.py", "top.env"]


def test_excluded_directory_is_skipped_entirely_not_just_left_out_of_the_report(tmp_path):
    project = tmp_path / "project"
    (project / "keep").mkdir(parents=True)
    (project / "exclude_me").mkdir(parents=True)
    (project / "keep" / "app.properties").write_text('password = "fake-Keep-123"\n', encoding="utf-8")
    (project / "exclude_me" / "secrets.properties").write_text('password = "fake-Excluded-456"\n', encoding="utf-8")

    output_dir = tmp_path / "out"
    entries, files_scanned, _ = engine.scan_project(project, output_dir, _rules(), excluded_paths=["exclude_me"])

    assert files_scanned == 1
    assert len(entries) == 1
    # report entries use str(rel_path) (platform-native separators), same
    # pre-existing convention as every other "file" field in this codebase.
    assert entries[0]["file"] == str(Path("keep") / "app.properties")
    # Not merely excluded from the report - never copied through either,
    # so a real secret in an excluded folder can't end up unredacted in
    # the output (unlike changed_files_only mode's copy-nothing guarantee,
    # applied here too for the same reason).
    assert not (output_dir / "exclude_me").exists()


def test_excluded_individual_file_is_skipped_while_its_siblings_still_scan(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "a.properties").write_text('password = "fake-A-111"\n', encoding="utf-8")
    (project / "b.properties").write_text('password = "fake-B-222"\n', encoding="utf-8")

    output_dir = tmp_path / "out"
    entries, files_scanned, _ = engine.scan_project(project, output_dir, _rules(), excluded_paths=["a.properties"])

    assert files_scanned == 1
    assert len(entries) == 1
    assert entries[0]["file"] == "b.properties"
    assert not (output_dir / "a.properties").exists()
    assert (output_dir / "b.properties").exists()


def test_no_excluded_paths_behaves_exactly_as_before(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.properties").write_text('password = "fake-Unaffected-789"\n', encoding="utf-8")

    output_dir = tmp_path / "out"
    entries, files_scanned, _ = engine.scan_project(project, output_dir, _rules())  # no excluded_paths at all
    assert files_scanned == 1
    assert len(entries) == 1


# ---------------------------------------------------------------------
# "Re-scan now" / "Scan again" parity (Phase 3): scan_project() always
# reads fresh from disk, on a project's first scan or its Nth - there is
# no cache to go stale. This is exactly the property the desktop app's
# scanBtn relabeling documents rather than changes (see app.js's
# updateScanButtonLabel() and README.md section 5).
# ---------------------------------------------------------------------

def test_rescanning_the_same_project_picks_up_an_on_disk_edit(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    secret_file = project / "app.properties"
    secret_file.write_text('password = "fake-BeforeEdit-111"\n', encoding="utf-8")
    output_dir = tmp_path / "out"

    first_entries, _, _ = engine.scan_project(project, output_dir, _rules())
    assert "fake-BeforeEdit-111" in first_entries[0]["before"]

    # Edit the file on disk between the two scans, exactly as a user would
    # between clicking "Run scan" and later clicking "Re-scan now".
    secret_file.write_text('password = "fake-AfterEdit-222"\n', encoding="utf-8")

    second_entries, _, _ = engine.scan_project(project, output_dir, _rules())
    assert "fake-AfterEdit-222" in second_entries[0]["before"], "a later scan of the same project must read the current on-disk content, not a cached copy"


# ---------------------------------------------------------------------
# Preview-before-write (Phase 4): stage_project()/apply_staged_project()/
# find_newly_unredacted_ignores()
# ---------------------------------------------------------------------

def test_stage_project_writes_nothing_to_disk(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.properties").write_text('password = "fake-StageOnly-111"\n', encoding="utf-8")
    output_dir = tmp_path / "out"

    entries, files_scanned, files_skipped, staged_files, newly_unredacted, unscanned_files = engine.stage_project(
        project, output_dir, _rules()
    )

    assert len(entries) == 1
    assert files_scanned == 1
    assert not output_dir.exists(), "stage_project() must not create the output directory at all"
    assert len(staged_files) == 1
    assert staged_files[0]["rel_path"] == "app.properties"
    assert "fake-StageOnly-111" not in staged_files[0]["content"]


def test_apply_staged_project_then_matches_what_scan_project_would_have_written(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.properties").write_text('password = "fake-ApplyMatch-222"\n', encoding="utf-8")
    (project / "notes.txt").write_text("not a classified extension\n", encoding="utf-8")

    staged_output = tmp_path / "staged_out"
    direct_output = tmp_path / "direct_out"

    _, _, _, staged_files, _, _ = engine.stage_project(project, staged_output, _rules())
    engine.apply_staged_project(staged_output, staged_files)
    engine.scan_project(project, direct_output, _rules())

    for name in ("app.properties", "notes.txt"):
        assert (staged_output / name).read_text(encoding="utf-8") == (direct_output / name).read_text(encoding="utf-8")


def test_preview_flags_an_unchanged_ignored_value_as_newly_unredacted(tmp_path):
    # check_ignore() hashes the raw captured value exactly as find_key_value
    # returns it (quotes included for a quoted config value) - unquoted
    # here so the hash input used by the test matches engine.hash_value(secret)
    # unambiguously (see test_ignored_finding_is_suppressed's own comment).
    project = tmp_path / "project"
    project.mkdir()
    secret = "fake-StillIgnored-333"
    (project / "app.properties").write_text(f'password = {secret}\n', encoding="utf-8")
    output_dir = tmp_path / "out"

    value_hash = engine.hash_value(secret)
    ignore_map = {("app.properties", "password", "key_name_match"): value_hash}

    entries, _, _, staged_files, newly_unredacted, _ = engine.stage_project(
        project, output_dir, _rules(), ignore_map=ignore_map
    )

    assert entries == [], "suppressed - not in the report"
    assert newly_unredacted == [{"file": "app.properties", "key": "password", "rule": "key_name_match"}]
    assert secret in staged_files[0]["content"], "the staged content really does contain the real value"


def test_preview_does_not_flag_an_ignored_value_that_changed_since_it_was_ignored(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.properties").write_text('password = "fake-RotatedValue-444"\n', encoding="utf-8")
    output_dir = tmp_path / "out"

    stale_hash = engine.hash_value("fake-OldValue-444")  # hash of the OLD value, not the current one
    ignore_map = {("app.properties", "password", "key_name_match"): stale_hash}

    entries, _, _, staged_files, newly_unredacted, _ = engine.stage_project(
        project, output_dir, _rules(), ignore_map=ignore_map
    )

    assert len(entries) == 1 and entries[0]["previously_ignored_value_changed"] is True
    assert newly_unredacted == [], "a changed value gets RE-redacted, not written unredacted - must not be flagged"
    assert "fake-RotatedValue-444" not in staged_files[0]["content"]


def test_preview_with_no_ignores_reports_nothing_newly_unredacted(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.properties").write_text('password = "fake-NoIgnores-555"\n', encoding="utf-8")
    output_dir = tmp_path / "out"

    _, _, _, _, newly_unredacted, _ = engine.stage_project(project, output_dir, _rules())  # no ignore_map at all
    assert newly_unredacted == []


def test_changing_an_ignore_between_two_previews_changes_the_newly_unredacted_result(tmp_path):
    """Models the "stale preview must be invalidated" requirement at the
    engine level: two stage_project() calls with different ignore_map
    states (before/after adding an ignore) must themselves disagree -
    the API layer is what actually enforces re-preview-before-apply."""
    project = tmp_path / "project"
    project.mkdir()
    secret = "fake-AddedMidway-666"
    (project / "app.properties").write_text(f'password = {secret}\n', encoding="utf-8")  # unquoted - see note above
    output_dir = tmp_path / "out"

    _, _, _, _, newly_unredacted_before, _ = engine.stage_project(project, output_dir, _rules(), ignore_map={})
    assert newly_unredacted_before == []

    ignore_map = {("app.properties", "password", "key_name_match"): engine.hash_value(secret)}
    _, _, _, _, newly_unredacted_after, _ = engine.stage_project(project, output_dir, _rules(), ignore_map=ignore_map)
    assert newly_unredacted_after == [{"file": "app.properties", "key": "password", "rule": "key_name_match"}]
