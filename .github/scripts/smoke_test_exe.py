"""
Smoke-tests the PACKAGED exe (dist/CredentialScrubber.exe) - not the Python
source. This is the only CI check that exercises the actual PyInstaller
bundle: a file missing from the bundle, a stale/broken onefile extraction,
etc. would not be caught by the regular pytest suite, which imports
engine.py/app.py/db.py directly from source, never through the built exe.

Run from the repo root, after dist/CredentialScrubber.exe has been built
(see .github/workflows/build-exe.yml). Exits non-zero on the first failed
assertion, with a "::error::" line GitHub Actions surfaces as an annotation.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:5057"
EXE_PATH = os.path.join("dist", "CredentialScrubber.exe")


def fail(msg):
    print(f"::error::{msg}")
    sys.exit(1)


def wait_for_server(timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(BASE + "/", timeout=2)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def get(path):
    try:
        with urllib.request.urlopen(BASE + path, timeout=10) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def api(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE + path, data=data, headers={"Content-Type": "application/json"}, method=method
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


def launch_exe():
    if not os.path.isfile(EXE_PATH):
        fail(f"{EXE_PATH} does not exist - build step did not produce it")
    env = dict(os.environ)
    env["CREDENTIAL_SCRUBBER_NO_BROWSER"] = "1"
    proc = subprocess.Popen([EXE_PATH], env=env)
    if not wait_for_server():
        proc.kill()
        fail("Server did not respond within the timeout after launching the exe")
    return proc


def stop_exe(proc):
    proc.terminate()
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=15)
    time.sleep(2)  # let Windows release the port before the next launch


def main():
    proc = launch_exe()
    print("Server is up.")

    # 1. GET / returns 200 and contains "Credential Scrubber"
    status, body = get("/")
    if status != 200:
        fail(f"GET / returned {status}, expected 200")
    if "Credential Scrubber" not in body:
        fail('GET / response did not contain "Credential Scrubber"')
    print("[1/4] GET / OK")

    # 2. Every /static/ asset the page actually references returns 200 -
    # catches a file missing from the PyInstaller bundle's datas.
    asset_paths = sorted(set(re.findall(r'(?:src|href)="(/static/[^"]+)"', body)))
    if not asset_paths:
        fail("No /static/ asset references found in the rendered page")
    for asset in asset_paths:
        a_status, _ = get(asset)
        if a_status != 200:
            fail(f"Static asset {asset} returned {a_status} - missing from the bundle?")
        print(f"       {asset} -> 200")
    print("[2/4] Static assets OK")

    # 3. Real API routes: create a project with two nested subfolders (one
    # fake secret each), exclude one, preview, assert the excluded file's
    # finding is absent and the other's is present.
    tmp_dir = tempfile.mkdtemp(prefix="smoke_test_proj_")
    folder_a = os.path.join(tmp_dir, "folder_a")
    folder_b = os.path.join(tmp_dir, "folder_b")
    os.makedirs(folder_a)
    os.makedirs(folder_b)
    with open(os.path.join(folder_a, "config.properties"), "w", encoding="utf-8") as f:
        f.write("password = fake-SmokeTestSecretA\n")
    with open(os.path.join(folder_b, "config.properties"), "w", encoding="utf-8") as f:
        f.write("password = fake-SmokeTestSecretB\n")
    out_dir = os.path.join(tmp_dir, "_out")

    project = api(
        "POST",
        "/api/projects",
        {"name": "smoke-test-project", "input_path": tmp_dir, "output_path": out_dir},
    )
    project_id = project["id"]
    print(f"       created project id={project_id}")

    api(
        "PUT",
        f"/api/projects/{project_id}/excluded-paths",
        {"excluded_paths": ["folder_b/config.properties"]},
    )

    preview = api("POST", f"/api/projects/{project_id}/preview", {})
    files_in_preview = [e["file"] for e in preview["entries"]]
    has_a = any("folder_a" in f for f in files_in_preview)
    has_b = any("folder_b" in f for f in files_in_preview)
    if has_b:
        fail(f"excluded file's finding is still present in the preview: {files_in_preview}")
    if not has_a:
        fail(f"included file's finding is missing from the preview: {files_in_preview}")
    print("[3/4] Folder-filter exclusion via the real API OK")

    # 4. Stop, relaunch, confirm the project survived (database persistence).
    stop_exe(proc)
    proc = launch_exe()
    projects = api("GET", "/api/projects")
    if not any(p["id"] == project_id for p in projects):
        fail(f"project {project_id} not found after restart - database was not persisted")
    print("[4/4] Database persistence across restart OK")

    stop_exe(proc)
    print("SMOKE TEST PASSED")


if __name__ == "__main__":
    main()
