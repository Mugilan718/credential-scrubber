"""
app.py - Local web app for the Credential Scrubber.

Run with: python app.py
Then open: http://127.0.0.1:5057

Everything runs locally. No data leaves this machine.
"""

import argparse
import copy
import json
import os
import re
import webbrowser
import threading
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

import yaml
from flask import Flask, jsonify, request, render_template, send_from_directory

import db
import engine

APP_DIR = Path(__file__).parent
DEFAULT_RULES_PATH = APP_DIR / "rules_default.yaml"

app = Flask(__name__)

# Guards tkinter's Tk() root creation/teardown in api_browse_folder() so two
# overlapping browse requests can never construct two Tk() instances at once
# (undefined behavior in tkinter) - relevant if the dev server is ever run
# with threaded=True; by default it handles requests on the main thread.
_browse_lock = threading.Lock()


def load_default_rules_dict():
    with open(DEFAULT_RULES_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def strip_sensitive(entries):
    """Return report entries without 'before'/'after' raw values - safe to display/export by default."""
    return [{"file": e["file"], "line": e["line"], "key": e.get("key"), "rule": e["rule"],
              "previously_ignored_value_changed": e.get("previously_ignored_value_changed", False)}
            for e in entries]


def _is_str_list(value):
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def validate_rules(rules):
    """Validate the shape of a rules dict before it's persisted.

    Only checks keys that are present, so a partial update doesn't need to
    restate every section. Returns an error message string, or None if valid.
    """
    if not isinstance(rules, dict):
        return "Request body must be a JSON object"

    if "key_patterns" in rules:
        key_patterns = rules["key_patterns"]
        if not _is_str_list(key_patterns):
            return "key_patterns must be a list of strings"
        for pattern in key_patterns:
            try:
                re.compile(pattern, re.IGNORECASE)
            except re.error as e:
                return f"Invalid regex in key_patterns: {pattern!r} ({e})"

    if "placeholder_allowlist" in rules:
        if not _is_str_list(rules["placeholder_allowlist"]):
            return "placeholder_allowlist must be a list of strings"

    if "value_patterns" in rules:
        value_patterns = rules["value_patterns"]
        if not isinstance(value_patterns, list):
            return "value_patterns must be a list of objects with 'name' and 'regex' string fields"
        for vp in value_patterns:
            if (not isinstance(vp, dict)
                    or not isinstance(vp.get("name"), str)
                    or not isinstance(vp.get("regex"), str)):
                return "value_patterns must be a list of objects with 'name' and 'regex' string fields"
            try:
                re.compile(vp["regex"], re.IGNORECASE)
            except re.error as e:
                return f"Invalid regex in value_patterns ({vp['name']!r}): {vp['regex']!r} ({e})"

    if "code_patterns" in rules:
        code_patterns = rules["code_patterns"]
        if not isinstance(code_patterns, dict):
            return "code_patterns must be a dict mapping language to a list of strings"
        for lang, patterns in code_patterns.items():
            if not _is_str_list(patterns):
                return f"code_patterns[{lang!r}] must be a list of strings"
            for pattern in patterns:
                try:
                    re.compile(pattern)
                except re.error as e:
                    return f"Invalid regex in code_patterns[{lang!r}]: {pattern!r} ({e})"

    return None


def validate_ignore_body(data):
    """Validate the body of POST /api/projects/<id>/ignore. Returns an error
    message string, or None if valid."""
    if not isinstance(data, dict):
        return "Request body must be a JSON object"
    if not isinstance(data.get("file"), str) or not data["file"].strip():
        return "file is required and must be a non-empty string"
    if not isinstance(data.get("rule"), str) or not data["rule"].strip():
        return "rule is required and must be a non-empty string"
    if "key" in data and data["key"] is not None and not isinstance(data["key"], str):
        return "key must be a string or null"
    return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/projects", methods=["GET"])
def api_list_projects():
    return jsonify(db.list_projects())


@app.route("/api/projects", methods=["POST"])
def api_create_project():
    data = request.get_json()
    name = data.get("name", "").strip()
    input_path = data.get("input_path", "").strip()
    output_path = data.get("output_path", "").strip()

    if not name or not input_path or not output_path:
        return jsonify({"error": "name, input_path, and output_path are all required"}), 400

    if not Path(input_path).exists():
        return jsonify({"error": f"Input path does not exist: {input_path}"}), 400

    rules_dict = load_default_rules_dict()
    project_id = db.create_project(name, input_path, output_path, rules_dict)
    return jsonify(db.get_project(project_id)), 201


@app.route("/api/browse-folder", methods=["POST"])
def api_browse_folder():
    """Open a native OS folder-selection dialog on this machine and return
    the chosen absolute path, or {"path": null} if the user cancels.

    This blocks the request until the dialog closes - acceptable for a
    single-user local tool where only one browse can meaningfully happen at
    a time. _browse_lock rejects a second overlapping request with 409
    rather than risk two Tk() roots existing at once.
    """
    if not _browse_lock.acquire(blocking=False):
        return jsonify({"error": "A folder browser is already open"}), 409
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        try:
            path = filedialog.askdirectory(parent=root)
        finally:
            root.destroy()
    finally:
        _browse_lock.release()
    return jsonify({"path": path or None})


@app.route("/api/projects/<int:project_id>", methods=["DELETE"])
def api_delete_project(project_id):
    db.delete_project(project_id)
    return jsonify({"deleted": True})


@app.route("/api/projects/<int:project_id>/rules", methods=["GET"])
def api_get_rules(project_id):
    project = db.get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    return jsonify(json.loads(project["rules_json"]))


@app.route("/api/projects/<int:project_id>/rules", methods=["PUT"])
def api_update_rules(project_id):
    project = db.get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    new_rules = request.get_json()
    error = validate_rules(new_rules)
    if error:
        return jsonify({"error": error}), 400
    db.update_project_rules(project_id, new_rules)
    return jsonify(new_rules)


@app.route("/api/projects/<int:project_id>/scan", methods=["POST"])
def api_run_scan(project_id):
    project = db.get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    body = request.get_json(silent=True) or {}
    changed_only = bool(body.get("changed_only", False))

    rules_dict = json.loads(project["rules_json"])

    # Write rules_dict to a temp yaml file since engine.load_rules expects a path
    tmp_rules_path = APP_DIR / "data" / f"rules_project_{project_id}.yaml"
    with open(tmp_rules_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(rules_dict, f)

    compiled_rules = engine.load_rules(tmp_rules_path)

    ignore_map = {(i["file"], i["key"], i["rule"]): i["value_hash"] for i in db.list_ignores(project_id)}

    try:
        report_entries, files_scanned, files_skipped = engine.scan_project(
            project["input_path"], project["output_path"], compiled_rules, ignore_map,
            changed_files_only=changed_only,
        )
    except engine.NotAGitRepoError as e:
        return jsonify({"error": str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 400

    scan_id = db.record_scan(project_id, files_scanned, len(report_entries), report_entries)

    return jsonify({
        "scan_id": scan_id,
        "files_scanned": files_scanned,
        "files_skipped": files_skipped,
        "total_redactions": len(report_entries),
        "output_path": project["output_path"],
        "changed_only": changed_only,
    })


@app.route("/api/projects/<int:project_id>/scans", methods=["GET"])
def api_list_scans(project_id):
    return jsonify(db.list_scans(project_id))


@app.route("/api/projects/<int:project_id>/ignore", methods=["GET"])
def api_list_ignores(project_id):
    project = db.get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    return jsonify(db.list_ignores(project_id))


def _lookup_current_value_hash(project_id, file, key, rule):
    """Find this (file, key, rule) finding's raw value in the project's most
    recent scan and hash it, so future scans can tell if the value has since
    changed. Reuses the value the scan already captured (record_scan stores
    full before/after, not just the stripped safe view) rather than asking
    the client to send the real secret through this endpoint - the safe
    results view's Ignore button never has the raw value to send anyway.
    Returns None if there's no scan yet or no matching finding in it.
    """
    scans = db.list_scans(project_id)
    if not scans:
        return None
    latest = db.get_scan_report(scans[0]["id"])
    if not latest:
        return None
    for entry in latest["report"]:
        if entry["file"] == file and entry.get("key") == key and entry["rule"] == rule:
            return engine.hash_value(entry["before"])
    return None


@app.route("/api/projects/<int:project_id>/ignore", methods=["POST"])
def api_add_ignore(project_id):
    project = db.get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    data = request.get_json()
    error = validate_ignore_body(data)
    if error:
        return jsonify({"error": error}), 400
    value_hash = _lookup_current_value_hash(project_id, data["file"], data.get("key"), data["rule"])
    ignore_id = db.add_ignore(project_id, data["file"], data.get("key"), data["rule"], value_hash)
    return jsonify({"id": ignore_id, "project_id": project_id, "file": data["file"],
                     "key": data.get("key"), "rule": data["rule"], "value_hash": value_hash}), 201


@app.route("/api/projects/<int:project_id>/ignore/<int:ignore_id>", methods=["DELETE"])
def api_remove_ignore(project_id, ignore_id):
    project = db.get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    existing_ids = {i["id"] for i in db.list_ignores(project_id)}
    if ignore_id not in existing_ids:
        return jsonify({"error": "Ignore entry not found for this project"}), 404
    db.remove_ignore(ignore_id)
    return jsonify({"deleted": True})


@app.route("/api/scans/<int:scan_id>/report", methods=["GET"])
def api_get_safe_report(scan_id):
    """Safe report - never includes raw secret values."""
    scan = db.get_scan_report(scan_id)
    if not scan:
        return jsonify({"error": "Scan not found"}), 404
    return jsonify({
        "scan_id": scan["id"],
        "timestamp": scan["timestamp"],
        "files_scanned": scan["files_scanned"],
        "total_redactions": scan["total_redactions"],
        "entries": strip_sensitive(scan["report"]),
    })


@app.route("/api/scans/<int:scan_id>/sensitive", methods=["GET"])
def api_get_sensitive_report(scan_id):
    """
    Sensitive report - includes raw before/after secret values.
    Caller (frontend) is responsible for gating this behind an explicit
    user action and warning. Never cache, log, or export this by default.
    """
    scan = db.get_scan_report(scan_id)
    if not scan:
        return jsonify({"error": "Scan not found"}), 404
    return jsonify({
        "scan_id": scan["id"],
        "timestamp": scan["timestamp"],
        "warning": "This report contains real secret values. Do not share, export, or paste this elsewhere.",
        "entries": scan["report"],
    })


def open_browser():
    webbrowser.open("http://127.0.0.1:5057")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-browser", action="store_true",
                         help="Don't auto-open a browser tab on startup")
    args = parser.parse_args()

    no_browser = args.no_browser or os.environ.get("CREDENTIAL_SCRUBBER_NO_BROWSER", "") not in ("", "0")

    db.init_db()
    if not no_browser:
        threading.Timer(1.0, open_browser).start()
    app.run(host="127.0.0.1", port=5057, debug=False)
