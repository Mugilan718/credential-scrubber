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
    print("[1/6] GET / OK")

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
    print("[2/6] Static assets OK")

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
    print("[3/6] Folder-filter exclusion via the real API OK")

    # 4. Unrecognized-file fallback + unscanned-files visibility, through
    # the real preview/apply API - a .rb file with an AWS-style key AND a
    # plain password (only the former should be caught - the fallback has
    # no key-name awareness), a multi-line id_rsa-style PEM, a small binary
    # file, and a file over the 2MB fallback-scan size limit.
    folder_fallback = os.path.join(tmp_dir, "folder_fallback")
    os.makedirs(folder_fallback)
    with open(os.path.join(folder_fallback, "secret.rb"), "w", encoding="utf-8") as f:
        f.write('aws_key = "AKIAIOSFODNN7EXAMPLE"\n')
        f.write('password = "hunter2"\n')
    id_rsa_content = (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEpQIBAAKCAQEA1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJ\n"
        "KLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJ\n"
        "KLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz==\n"
        "-----END RSA PRIVATE KEY-----\n"
    )
    with open(os.path.join(folder_fallback, "id_rsa"), "w", encoding="utf-8", newline="") as f:
        f.write(id_rsa_content)
    with open(os.path.join(folder_fallback, "photo.bin"), "wb") as f:
        f.write(bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]) + os.urandom(200))
    with open(os.path.join(folder_fallback, "huge.rb"), "wb") as f:
        f.write(b'password = "hunter2"\n')
        f.write(b"x" * (2 * 1024 * 1024 + 500))

    preview2 = api("POST", f"/api/projects/{project_id}/preview", {})
    entries2 = preview2["entries"]

    # engine.py reports a finding's "file" with the OS's native path
    # separator (str(rel_path), not rel_path.as_posix()) - true for every
    # existing finding, not specific to this feature. Normalize before
    # comparing rather than assuming "/".
    def norm(path):
        return path.replace("\\", "/")

    secret_rb_entries = [e for e in entries2 if norm(e["file"]) == "folder_fallback/secret.rb"]
    if len(secret_rb_entries) != 1 or "aws_access_key_id" not in secret_rb_entries[0]["rule"]:
        fail(f"expected exactly one aws_access_key_id finding for secret.rb (and the plain password left unflagged), got: {secret_rb_entries}")

    id_rsa_entries = [e for e in entries2 if norm(e["file"]) == "folder_fallback/id_rsa"]
    if len(id_rsa_entries) != 1 or "private_key_block" not in id_rsa_entries[0]["rule"]:
        fail(f"expected exactly one private_key_block finding for id_rsa, got: {id_rsa_entries}")

    unscanned_rel_paths = {norm(u["rel_path"]): u["reason"] for u in preview2["unscanned_files"]}
    if unscanned_rel_paths.get("folder_fallback/photo.bin") != "binary":
        fail(f"expected photo.bin in unscanned_files with reason 'binary', got: {unscanned_rel_paths}")
    if unscanned_rel_paths.get("folder_fallback/huge.rb") != "oversize":
        fail(f"expected huge.rb in unscanned_files with reason 'oversize', got: {unscanned_rel_paths}")
    print("[4/6] Unrecognized-file fallback + unscanned-files list via the real preview API OK")

    # 5. Apply, then verify the ACTUAL applied output on disk: the AWS key
    # is really redacted, the plain password really isn't, the PEM body is
    # masked with its line count preserved, and the binary/oversized files
    # are really present (copied through untouched).
    apply_result = api("POST", f"/api/projects/{project_id}/apply", {})
    applied_unscanned = {norm(u["rel_path"]): u["reason"] for u in apply_result["unscanned_files"]}
    if applied_unscanned.get("folder_fallback/photo.bin") != "binary" or applied_unscanned.get("folder_fallback/huge.rb") != "oversize":
        fail(f"Apply response's unscanned_files missing expected entries: {applied_unscanned}")

    with open(os.path.join(out_dir, "folder_fallback", "secret.rb"), "r", encoding="utf-8") as f:
        secret_rb_written = f.read()
    if "AKIAIOSFODNN7EXAMPLE" in secret_rb_written:
        fail("AWS key was NOT redacted in the applied output")
    if 'password = "hunter2"' not in secret_rb_written:
        fail("plain password was unexpectedly redacted in the applied output (documented limit regressed)")

    with open(os.path.join(out_dir, "folder_fallback", "id_rsa"), "r", encoding="utf-8") as f:
        id_rsa_written = f.read()
    if "MIIEpQIBAAKCAQEA" in id_rsa_written:
        fail("PEM key body was NOT masked in the applied output")
    if len(id_rsa_written.splitlines()) != len(id_rsa_content.splitlines()):
        fail(f"PEM line count was not preserved: expected {len(id_rsa_content.splitlines())} lines, got {len(id_rsa_written.splitlines())}")

    photo_out = os.path.join(out_dir, "folder_fallback", "photo.bin")
    if not os.path.isfile(photo_out):
        fail("binary file was not copied to the applied output")
    huge_out = os.path.join(out_dir, "folder_fallback", "huge.rb")
    if not os.path.isfile(huge_out) or os.path.getsize(huge_out) < 2 * 1024 * 1024:
        fail("oversized file was not copied to the applied output")
    print("[5/6] Applied output on disk OK: AWS key redacted, plain password untouched, PEM masked with line count preserved, binary/oversized files present")

    # 6. Stop, relaunch, confirm the project survived (database persistence).
    stop_exe(proc)
    proc = launch_exe()
    projects = api("GET", "/api/projects")
    if not any(p["id"] == project_id for p in projects):
        fail(f"project {project_id} not found after restart - database was not persisted")
    print("[6/6] Database persistence across restart OK")

    stop_exe(proc)
    print("SMOKE TEST PASSED")


if __name__ == "__main__":
    main()
