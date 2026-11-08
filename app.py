import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from functools import wraps

from flask import (
    Flask, abort, flash, redirect, render_template, request,
    send_from_directory, session, url_for
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from database import close_db, get_db, init_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production",
    MAX_CONTENT_LENGTH=10 * 1024 * 1024,
    WTF_CSRF_TIME_LIMIT=None,
)
csrf = CSRFProtect(app)

UPLOAD_FOLDER = os.environ.get(
    "UPLOAD_FOLDER", os.path.join(app.root_path, "uploads")
)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"pdf", "txt", "doc", "docx", "png", "jpg", "jpeg"}
app.teardown_appcontext(close_db)


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def audit_key():
    return (os.environ.get("AUDIT_LOG_KEY") or app.secret_key).encode("utf-8")


def log_action(user_id, action, document_id=None, details=""):
    """Append an HMAC-protected audit event linked to the previous event."""
    db = get_db()
    previous = db.execute(
        "SELECT entry_hash FROM audit_logs ORDER BY id DESC LIMIT 1"
    ).fetchone()
    previous_hash = previous["entry_hash"] if previous and previous["entry_hash"] else ("legacy-history" if previous else "")
    created_at = now()
    payload = {
        "user_id": user_id, "document_id": document_id, "action": action,
        "details": details, "created_at": created_at,
        "previous_hash": previous_hash,
    }
    digest = hmac.new(
        audit_key(), json.dumps(payload, sort_keys=True).encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    db.execute(
        """INSERT INTO audit_logs
           (user_id, document_id, action, details, created_at, previous_hash, entry_hash)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, document_id, action, details, created_at, previous_hash, digest)
    )
    db.commit()


def verify_audit_chain():
    db = get_db()
    rows = db.execute("SELECT * FROM audit_logs ORDER BY id").fetchall()
    previous_hash = ""
    started = False
    for row in rows:
        # Old records cannot be authenticated retroactively; verify the new chain after them.
        if not row["entry_hash"] and not started:
            continue
        if not started and row["previous_hash"] == "legacy-history":
            previous_hash = "legacy-history"
        started = True
        if (row["previous_hash"] or "") != previous_hash:
            return False
        payload = {
            "user_id": row["user_id"], "document_id": row["document_id"],
            "action": row["action"], "details": row["details"] or "",
            "created_at": row["created_at"], "previous_hash": previous_hash,
        }
        expected = hmac.new(
            audit_key(), json.dumps(payload, sort_keys=True).encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(row["entry_hash"] or "", expected):
            return False
        previous_hash = row["entry_hash"]
    return True


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            user = get_db().execute(
                "SELECT role FROM users WHERE id = ?", (session["user_id"],)
            ).fetchone()
            if not user or user["role"] not in roles:
                if user:
                    log_action(session["user_id"], "denied_role_access", None, request.path)
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def is_document_owner(user_id, document_id):
    document = get_db().execute(
        "SELECT owner_id FROM documents WHERE id = ?", (document_id,)
    ).fetchone()
    return bool(document and document["owner_id"] == user_id)


def can_access_document(user_id, document_id, required="read"):
    db = get_db()
    user = db.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
    document = db.execute(
        "SELECT owner_id FROM documents WHERE id = ?", (document_id,)
    ).fetchone()
    if not user or not document:
        return False
    if user["role"] == "admin" or document["owner_id"] == user_id:
        return True
    permission = db.execute(
        "SELECT permission FROM permissions WHERE document_id = ? AND user_id = ?",
        (document_id, user_id)
    ).fetchone()
    if not permission:
        return False
    if required == "edit":
        return user["role"] != "viewer" and permission["permission"] == "edit"
    return permission["permission"] in ("read", "edit")


def get_document_or_404(document_id):
    document = get_db().execute(
        "SELECT * FROM documents WHERE id = ? AND deleted_at IS NULL", (document_id,)
    ).fetchone()
    if not document:
        abort(404)
    return document


def seed_admin():
    username = os.environ.get("ADMIN_USERNAME")
    password = os.environ.get("ADMIN_PASSWORD")
    if not username or not password:
        return
    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1").fetchone()
    if not existing:
        db.execute(
            "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, 'admin')",
            (username.strip(), generate_password_hash(password))
        )
        db.commit()


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; object-src 'none'; frame-ancestors 'none'"
    )
    if request.is_secure:
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if len(username) < 3 or len(password) < 8:
            flash("Username must be 3+ characters and password 8+ characters.")
            return redirect(url_for("register"))
        try:
            db = get_db()
            db.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'owner')",
                (username, generate_password_hash(password))
            )
            db.commit()
            flash("Account created as document owner. Please log in.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That username is already taken.")
            return redirect(url_for("register"))
    return render_template("login.html", mode="register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_db().execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            log_action(user["id"], "login")
            return redirect(url_for("admin") if user["role"] == "admin" else url_for("dashboard"))
        flash("Invalid username or password.")
    return render_template("login.html", mode="login")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    user_id = session["user_id"]
    log_action(user_id, "logout")
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    user_id = session["user_id"]
    user = db.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
    if user["role"] == "admin":
        return redirect(url_for("admin"))
    search = request.args.get("q", "").strip()
    owner_filter = request.args.get("owner", "").strip()
    category = request.args.get("category", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()
    sql = """SELECT DISTINCT d.*, u.username AS owner_name,
             p.permission AS my_permission
             FROM documents d JOIN users u ON u.id = d.owner_id
             LEFT JOIN permissions p ON d.id = p.document_id AND p.user_id = ?
             WHERE d.deleted_at IS NULL AND (d.owner_id = ? OR p.user_id = ?)"""
    args = [user_id, user_id, user_id]
    if search:
        sql += " AND d.original_name LIKE ?"
        args.append("%" + search + "%")
    if owner_filter:
        sql += " AND u.username LIKE ?"
        args.append("%" + owner_filter + "%")
    if category:
        sql += " AND d.category = ?"
        args.append(category)
    if date_from:
        sql += " AND date(d.created_at) >= date(?)"
        args.append(date_from)
    if date_to:
        sql += " AND date(d.created_at) <= date(?)"
        args.append(date_to)
    sql += " ORDER BY d.created_at DESC"
    documents = db.execute(sql, args).fetchall()
    users = db.execute(
        "SELECT id, username FROM users WHERE id != ? AND role != 'admin' ORDER BY username",
        (user_id,)
    ).fetchall()
    categories = db.execute(
        "SELECT DISTINCT category FROM documents WHERE category != '' ORDER BY category"
    ).fetchall()
    return render_template(
        "dashboard.html", documents=documents, users=users,
        categories=categories, search=search, owner_filter=owner_filter,
        category=category, date_from=date_from, date_to=date_to,
        role=user["role"]
    )


@app.route("/upload", methods=["POST"])
@roles_required("owner", "admin")
def upload():
    file = request.files.get("file")
    if not file or not file.filename:
        flash("Choose a file to upload.")
        return redirect(url_for("dashboard"))
    if not allowed_file(file.filename):
        flash("File type not allowed.")
        return redirect(url_for("dashboard"))
    original_name = secure_filename(file.filename)
    if not original_name:
        flash("Invalid file name.")
        return redirect(url_for("dashboard"))
    category = request.form.get("category", "General").strip()[:80] or "General"
    stored_name = secrets.token_hex(16) + "_" + original_name
    path = os.path.join(UPLOAD_FOLDER, stored_name)
    file.save(path)
    db = get_db()
    cursor = db.execute(
        """INSERT INTO documents
           (owner_id, original_name, stored_name, category, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (session["user_id"], original_name, stored_name, category, now())
    )
    db.commit()
    log_action(session["user_id"], "upload", cursor.lastrowid, original_name)
    flash("Document uploaded.")
    return redirect(url_for("dashboard"))


@app.route("/download/<int:document_id>")
@login_required
def download(document_id):
    document = get_document_or_404(document_id)
    if not can_access_document(session["user_id"], document_id):
        log_action(session["user_id"], "denied_download", document_id)
        abort(403)
    log_action(session["user_id"], "download", document_id, document["original_name"])
    return send_from_directory(
        UPLOAD_FOLDER, document["stored_name"],
        as_attachment=True, download_name=document["original_name"],
        conditional=True
    )


@app.route("/share/<int:document_id>", methods=["POST"])
@roles_required("owner", "admin")
def share(document_id):
    document = get_document_or_404(document_id)
    user_id = session["user_id"]
    if document["owner_id"] != user_id and session.get("role") != "admin":
        log_action(user_id, "denied_share", document_id, "Non-owner attempted to change sharing")
        abort(403)
    target_id = request.form.get("user_id", type=int)
    permission = request.form.get("permission", "read")
    if permission not in ("read", "edit") or target_id == user_id:
        abort(400)
    db = get_db()
    target = db.execute(
        "SELECT id, role FROM users WHERE id = ?", (target_id,)
    ).fetchone()
    if not target or target["role"] == "admin":
        abort(400)
    if target["role"] == "viewer":
        permission = "read"
    db.execute(
        """INSERT INTO permissions (document_id, user_id, permission)
           VALUES (?, ?, ?)
           ON CONFLICT(document_id, user_id)
           DO UPDATE SET permission = excluded.permission""",
        (document_id, target_id, permission)
    )
    db.commit()
    log_action(user_id, "permission_granted", document_id,
               f"Granted {permission} to user {target_id}")
    flash("Permission updated.")
    return redirect(url_for("dashboard"))


@app.route("/revoke/<int:document_id>/<int:target_id>", methods=["POST"])
@roles_required("owner", "admin")
def revoke(document_id, target_id):
    document = get_document_or_404(document_id)
    user_id = session["user_id"]
    if document["owner_id"] != user_id and session.get("role") != "admin":
        log_action(user_id, "denied_revoke", document_id, "Non-owner attempted to revoke access")
        abort(403)
    get_db().execute(
        "DELETE FROM permissions WHERE document_id = ? AND user_id = ?",
        (document_id, target_id)
    )
    get_db().commit()
    log_action(user_id, "permission_revoked", document_id,
               f"Revoked access from user {target_id}")
    flash("Access revoked.")
    return redirect(url_for("dashboard"))


@app.route("/document/<int:document_id>/update", methods=["POST"])
@login_required
def update_document(document_id):
    document = get_document_or_404(document_id)
    user_id = session["user_id"]
    if document["owner_id"] != user_id and not can_access_document(user_id, document_id, "edit"):
        log_action(user_id, "denied_edit", document_id, "User attempted an unauthorized document edit")
        abort(403)
    if session.get("role") == "viewer":
        abort(403)
    name = secure_filename(request.form.get("name", "").strip())
    category = request.form.get("category", "").strip()[:80]
    if not name or not category:
        abort(400)
    get_db().execute(
        "UPDATE documents SET original_name = ?, category = ? WHERE id = ?",
        (name, category, document_id)
    )
    get_db().commit()
    log_action(user_id, "document_changed", document_id, f"Updated name/category to {name}/{category}")
    flash("Document details updated.")
    return redirect(url_for("dashboard"))


@app.route("/delete/<int:document_id>", methods=["POST"])
@roles_required("owner", "admin")
def delete_document(document_id):
    document = get_document_or_404(document_id)
    user_id = session["user_id"]
    if document["owner_id"] != user_id and session.get("role") != "admin":
        log_action(user_id, "denied_delete", document_id, "Non-owner attempted document deletion")
        abort(403)
    log_action(user_id, "deletion", document_id, document["original_name"])
    db = get_db()
    db.execute("UPDATE documents SET deleted_at = ? WHERE id = ?", (now(), document_id))
    db.execute("DELETE FROM permissions WHERE document_id = ?", (document_id,))
    db.commit()
    try:
        os.remove(os.path.join(UPLOAD_FOLDER, os.path.basename(document["stored_name"])))
    except FileNotFoundError:
        pass
    flash("Document deleted.")
    return redirect(url_for("dashboard"))


@app.route("/audit")
@login_required
def audit():
    user_id = session["user_id"]
    logs = get_db().execute(
        """SELECT a.*, u.username FROM audit_logs a
           LEFT JOIN users u ON a.user_id = u.id
           WHERE a.user_id = ? ORDER BY a.id DESC LIMIT 200""",
        (user_id,)
    ).fetchall()
    return render_template("audit.html", logs=logs, verified=verify_audit_chain())


@app.route("/admin")
@roles_required("admin")
def admin():
    db = get_db()
    users = db.execute(
        "SELECT id, username, role FROM users ORDER BY id"
    ).fetchall()
    logs = db.execute(
        """SELECT a.*, u.username FROM audit_logs a
           LEFT JOIN users u ON u.id = a.user_id
           ORDER BY a.id DESC LIMIT 300"""
    ).fetchall()
    documents = db.execute(
        """SELECT d.*, u.username AS owner_name FROM documents d
           JOIN users u ON u.id = d.owner_id WHERE d.deleted_at IS NULL ORDER BY d.created_at DESC"""
    ).fetchall()
    return render_template(
        "admin.html", users=users, logs=logs, documents=documents,
        audit_verified=verify_audit_chain()
    )


@app.route("/admin/users", methods=["POST"])
@roles_required("admin")
def admin_create_user():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "")
    if len(username) < 3 or len(password) < 8 or role not in ("owner", "viewer"):
        abort(400)
    try:
        get_db().execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, generate_password_hash(password), role)
        )
        get_db().commit()
        log_action(session["user_id"], "user_created", None, f"{role} account: {username}")
    except sqlite3.IntegrityError:
        flash("That username already exists.")
    return redirect(url_for("admin"))


@app.errorhandler(403)
def forbidden(error):
    return "Access denied.", 403


@app.errorhandler(413)
def too_large(error):
    return "File too large. Maximum size is 10 MB.", 413


init_db()
with app.app_context():
    seed_admin()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_ENV") != "production")
