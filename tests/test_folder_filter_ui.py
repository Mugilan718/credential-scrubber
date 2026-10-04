"""
UI-level regression test for the folder-filter tree's findNodeByPath crash
(static/app.js) - drives the real app.js in a real browser via Playwright,
not just the Python backend. Every Python-level test of folder exclusion
(engine.scan_project(), the /preview API, etc.) already passed while this
bug was live, because the bug was a frontend JS crash in the checkbox click
handler, not anything wrong with how exclusions are computed or applied
once they're actually saved - a real-browser test is the only way to catch
it. See CHANGELOG.md's [2.0.1] entry and the findNodeByPath docstring-style
comment in static/app.js for the full story.

Skipped entirely if Playwright (or its browser binaries) isn't available -
this is a local/manual verification aid, not a hard CI dependency (see
requirements-dev.txt, which does not include playwright), so its absence
must never fail the suite or break the GitHub Actions workflow.
"""
import threading

import pytest

pytest.importorskip("playwright")

from werkzeug.serving import make_server

import app as app_module
import db

PORT = 5099


@pytest.fixture
def live_server(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test_app.db")
    db.init_db()

    server = make_server("127.0.0.1", PORT, app_module.app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{PORT}"
    finally:
        server.shutdown()
        thread.join(timeout=5)


@pytest.fixture
def nested_project(tmp_path, live_server):
    project_dir = tmp_path / "nested_project"
    (project_dir / "src" / "main" / "resources").mkdir(parents=True)
    (project_dir / "src" / "test" / "resources").mkdir(parents=True)
    (project_dir / "src" / "main" / "resources" / "application.properties").write_text(
        "password = fake-KeepMeSecret123\n", encoding="utf-8"
    )
    (project_dir / "src" / "test" / "resources" / "application-test.properties").write_text(
        "password = fake-ExcludeMeSecret456\n", encoding="utf-8"
    )
    output_dir = tmp_path / "nested_project_out"
    project_id = db.create_project("nested-ui-test", str(project_dir), str(output_dir), {})
    return project_id


def test_unchecking_a_nested_file_in_the_folder_tree_excludes_it_from_the_preview(
    nested_project, live_server
):
    """
    Reproduces the exact reported symptom end to end through the real UI:
    open "Edit folders", uncheck a nested file via a real click (not the
    API), save, run a preview, and confirm that file's finding is gone and
    the other file's finding is still there. Before the findNodeByPath fix,
    the checkbox click threw ("node.children is not iterable") and
    checkedPaths was silently never updated, so this assertion fails - the
    excluded file's finding stays present because nothing was actually
    excluded despite the checkbox visually toggling.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as e:
            pytest.skip(f"Playwright browser binaries not installed: {e}")

        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page_errors = []
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        page.goto(live_server)
        page.wait_for_selector("body", timeout=10000)
        page.evaluate(f"async () => {{ await selectProject({nested_project}); }}")
        page.wait_for_timeout(300)

        page.click("#editFoldersBtn")
        page.wait_for_selector("#folderFilterModalOverlay:not(.hidden)", timeout=5000)
        page.click('.tree-toggle[data-path="src"]')
        page.wait_for_timeout(100)
        page.click('.tree-toggle[data-path="src/test"]')
        page.wait_for_timeout(100)
        page.click('.tree-toggle[data-path="src/test/resources"]')
        page.wait_for_timeout(100)

        # The plain checkbox path, not the "Only" button - this is exactly
        # the interaction that was silently broken.
        page.locator('.tree-checkbox[data-path$="application-test.properties"]').first.click(
            force=True
        )
        page.wait_for_timeout(100)
        assert page_errors == [], f"unexpected JS error(s) during checkbox click: {page_errors}"

        page.click("#saveFolderFilterBtn")
        page.wait_for_timeout(300)

        page.click("#scanBtn")
        page.wait_for_selector("#resultsTable:not(.hidden)", timeout=15000)
        page.wait_for_timeout(200)

        files_in_results = page.locator(".result-file").all_inner_texts()
        browser.close()

    assert not any("application-test.properties" in f for f in files_in_results), (
        "the excluded (unchecked) file's finding is still in the results - "
        f"folder exclusion did not take effect. Results showed: {files_in_results}"
    )
    assert any("application.properties" in f and "test" not in f for f in files_in_results), (
        "the file that should still be included is missing from the results - "
        f"over-excluded. Results showed: {files_in_results}"
    )
