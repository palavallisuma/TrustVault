import os
import sqlite3
from flask import g

DATABASE = os.environ.get(
    "DATABASE_PATH", os.path.join(os.path.dirname(__file__), "trustvault.db")
)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.execute("PRAGMA journal_mode = WAL")
    return g.db


def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DATABASE)), exist_ok=True)
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'owner'
                CHECK(role IN ('admin', 'owner', 'viewer'))
        );
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            original_name TEXT NOT NULL,
            stored_name TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'General',
            created_at TEXT NOT NULL,
            deleted_at TEXT,
            FOREIGN KEY (owner_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            permission TEXT NOT NULL CHECK(permission IN ('read', 'edit')),
            UNIQUE(document_id, user_id),
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (document_id) REFERENCES documents(id)
        );
    """)
    # Safe, additive migrations for existing SQLite deployments.
    document_columns = {
        row[1] for row in db.execute("PRAGMA table_info(documents)").fetchall()
    }
    if "category" not in document_columns:
        db.execute("ALTER TABLE documents ADD COLUMN category TEXT NOT NULL DEFAULT 'General'")
    if "deleted_at" not in document_columns:
        db.execute("ALTER TABLE documents ADD COLUMN deleted_at TEXT")
    audit_columns = {
        row[1] for row in db.execute("PRAGMA table_info(audit_logs)").fetchall()
    }
    if "previous_hash" not in audit_columns:
        db.execute("ALTER TABLE audit_logs ADD COLUMN previous_hash TEXT NOT NULL DEFAULT ''")
    if "entry_hash" not in audit_columns:
        db.execute("ALTER TABLE audit_logs ADD COLUMN entry_hash TEXT NOT NULL DEFAULT ''")
    # Migrate old generic accounts to the owner role.
    db.execute("UPDATE users SET role = 'owner' WHERE role = 'user'")
    db.commit()
    db.close()


def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
