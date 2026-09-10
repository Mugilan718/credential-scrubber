"""
db.py - Local SQLite storage for projects and scan history.
Everything stays on this machine. No network calls, no external DB.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "app.db"


def get_conn():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            input_path TEXT NOT NULL,
            output_path TEXT NOT NULL,
            rules_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            files_scanned INTEGER NOT NULL,
            total_redactions INTEGER NOT NULL,
            report_json TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()


def list_projects():
    conn = get_conn()
    rows = conn.execute("SELECT id, name, input_path, output_path, created_at FROM projects ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_project(project_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_project(name, input_path, output_path, rules_dict):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO projects (name, input_path, output_path, rules_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (name, input_path, output_path, json.dumps(rules_dict), datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    project_id = cur.lastrowid
    conn.close()
    return project_id


def update_project_rules(project_id, rules_dict):
    conn = get_conn()
    conn.execute("UPDATE projects SET rules_json = ? WHERE id = ?", (json.dumps(rules_dict), project_id))
    conn.commit()
    conn.close()


def delete_project(project_id):
    conn = get_conn()
    conn.execute("DELETE FROM scans WHERE project_id = ?", (project_id,))
    conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()


def record_scan(project_id, files_scanned, total_redactions, safe_report_entries):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO scans (project_id, timestamp, files_scanned, total_redactions, report_json) VALUES (?, ?, ?, ?, ?)",
        (project_id, datetime.now(timezone.utc).isoformat(), files_scanned, total_redactions, json.dumps(safe_report_entries)),
    )
    conn.commit()
    scan_id = cur.lastrowid
    conn.close()
    return scan_id


def list_scans(project_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, timestamp, files_scanned, total_redactions FROM scans WHERE project_id = ? ORDER BY timestamp DESC",
        (project_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_scan_report(scan_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM scans WHERE id = ?", (scan_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["report"] = json.loads(d.pop("report_json"))
    return d
