import os
import sqlite3
from flask import g

DATABASE = os.path.join(os.path.dirname(__file__), "trustvault.db")

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db

def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'viewer' CHECK(role IN ('admin','owner','viewer'))
    );
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER NOT NULL,
        original_name TEXT NOT NULL,
        stored_name TEXT NOT NULL,
        created_at TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT '',
        FOREIGN KEY(owner_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS permissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        permission TEXT NOT NULL CHECK(permission IN ('read','edit')),
        UNIQUE(document_id,user_id),
        FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        document_id INTEGER,
        action TEXT NOT NULL,
        details TEXT,
        created_at TEXT NOT NULL,
        previous_hash TEXT NOT NULL DEFAULT '',
        entry_hash TEXT NOT NULL DEFAULT '',
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(document_id) REFERENCES documents(id)
    );
    """)
    # Safe, repeatable upgrades for databases created by earlier TrustVault versions.
    user_columns = {r[1] for r in db.execute("PRAGMA table_info(users)")}
    if "role" not in user_columns:
        db.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'viewer'")
    doc_columns = {r[1] for r in db.execute("PRAGMA table_info(documents)")}
    if "category" not in doc_columns:
        db.execute("ALTER TABLE documents ADD COLUMN category TEXT NOT NULL DEFAULT ''")
    audit_columns = {r[1] for r in db.execute("PRAGMA table_info(audit_logs)")}
    if "previous_hash" not in audit_columns:
        db.execute("ALTER TABLE audit_logs ADD COLUMN previous_hash TEXT NOT NULL DEFAULT ''")
    if "entry_hash" not in audit_columns:
        db.execute("ALTER TABLE audit_logs ADD COLUMN entry_hash TEXT NOT NULL DEFAULT ''")
    db.execute("UPDATE users SET role='viewer' WHERE role NOT IN ('admin','owner','viewer')")
    db.commit()
    db.close()

def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
