import os
import sqlite3
import secrets
import hmac
import hashlib
import json
from functools import wraps
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from database import init_db, get_db, close_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
                  MAX_CONTENT_LENGTH=10 * 1024 * 1024)
UPLOAD_FOLDER = os.path.join(app.root_path, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"pdf", "txt", "doc", "docx", "png", "jpg", "jpeg"}
app.teardown_appcontext(close_db)

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def audit_key():
    return (os.environ.get("AUDIT_SECRET") or app.secret_key).encode()

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def role_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            user = get_db().execute("SELECT role FROM users WHERE id=?", (session["user_id"],)).fetchone()
            if not user or user["role"] not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator

def log_action(user_id, action, document_id=None, details=""):
    db = get_db()
    previous = db.execute("SELECT entry_hash FROM audit_logs ORDER BY id DESC LIMIT 1").fetchone()
    previous_hash = previous["entry_hash"] if previous and previous["entry_hash"] else "0" * 64
    created_at = now()
    payload = json.dumps({"user_id": user_id, "document_id": document_id, "action": action,
                          "details": details, "created_at": created_at, "previous_hash": previous_hash},
                         sort_keys=True, separators=(",", ":"))
    entry_hash = hmac.new(audit_key(), payload.encode(), hashlib.sha256).hexdigest()
    db.execute("""INSERT INTO audit_logs(user_id,document_id,action,details,created_at,previous_hash,entry_hash)
                  VALUES(?,?,?,?,?,?,?)""",
               (user_id, document_id, action, details, created_at, previous_hash, entry_hash))
    db.commit()

def verify_audit_chain():
    rows = get_db().execute("SELECT * FROM audit_logs ORDER BY id").fetchall()
    previous_hash = "0" * 64
    for row in rows:
        # Pre-upgrade rows are retained but have no signature to verify.
        if not row["entry_hash"]:
            continue
        payload = json.dumps({"user_id": row["user_id"], "document_id": row["document_id"],
                              "action": row["action"], "details": row["details"] or "",
                              "created_at": row["created_at"], "previous_hash": previous_hash},
                             sort_keys=True, separators=(",", ":"))
        expected = hmac.new(audit_key(), payload.encode(), hashlib.sha256).hexdigest()
        if row["previous_hash"] != previous_hash or not hmac.compare_digest(row["entry_hash"], expected):
            return False
        previous_hash = row["entry_hash"]
    return True

def is_document_owner(user_id, document_id):
    row = get_db().execute("SELECT owner_id FROM documents WHERE id=?", (document_id,)).fetchone()
    return bool(row and row["owner_id"] == user_id)

def can_access_document(user_id, document_id, required="read"):
    db = get_db()
    document = db.execute("SELECT owner_id FROM documents WHERE id=?", (document_id,)).fetchone()
    if not document:
        return False
    if document["owner_id"] == user_id:
        return True
    permission = db.execute("SELECT permission FROM permissions WHERE document_id=? AND user_id=?",
                            (document_id, user_id)).fetchone()
    if not permission:
        return False
    return permission["permission"] == "edit" if required == "edit" else permission["permission"] in ("read", "edit")

def deny(user_id, action, document_id=None):
    log_action(user_id, "denied_" + action, document_id)
    abort(403)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if len(username) < 3 or len(password) < 8:
            flash("Username must be at least 3 characters and password at least 8 characters.")
            return redirect(url_for("register"))
        db = get_db()
        try:
            db.execute("INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",
                       (username, generate_password_hash(password), "viewer"))
            db.commit()
            flash("Account created. Please log in.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That username is already taken.")
            return redirect(url_for("register"))
    return render_template("login.html", mode="register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        user = get_db().execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if user and check_password_hash(user["password_hash"], request.form.get("password", "")):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            log_action(user["id"], "login")
            return redirect(url_for("dashboard"))
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
    q = request.args.get("q", "").strip()
    owner = request.args.get("owner", "").strip()
    category = request.args.get("category", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()
    sql = """SELECT DISTINCT d.*, u.username AS owner_name FROM documents d
             JOIN users u ON u.id=d.owner_id LEFT JOIN permissions p ON p.document_id=d.id
             WHERE (d.owner_id=? OR p.user_id=?)"""
    params = [user_id, user_id]
    if q:
        sql += " AND d.original_name LIKE ?"
        params.append("%" + q + "%")
    if owner:
        sql += " AND u.username LIKE ?"
        params.append("%" + owner + "%")
    if category:
        sql += " AND d.category LIKE ?"
        params.append("%" + category + "%")
    if date_from:
        sql += " AND substr(d.created_at,1,10)>=?"
        params.append(date_from)
    if date_to:
        sql += " AND substr(d.created_at,1,10)<=?"
        params.append(date_to)
    sql += " ORDER BY d.created_at DESC"
    documents = db.execute(sql, params).fetchall()
    users = db.execute("SELECT id,username FROM users WHERE id!=?", (user_id,)).fetchall()
    shared = {}
    for document in documents:
        shared[document["id"]] = db.execute(
            """SELECT p.user_id, p.permission, u.username
               FROM permissions p JOIN users u ON u.id=p.user_id
               WHERE p.document_id=? ORDER BY u.username""",
            (document["id"],)
        ).fetchall()
    current_user = db.execute("SELECT role FROM users WHERE id=?", (user_id,)).fetchone()
    return render_template("dashboard.html", documents=documents, users=users, q=q,
                           owner=owner, category=category, date_from=date_from,
                           date_to=date_to, role=current_user["role"], shared=shared)

@app.route("/upload", methods=["POST"])
@login_required
def upload():
    file = request.files.get("file")
    if not file or not file.filename or not allowed_file(file.filename):
        flash("Choose a supported file (PDF, TXT, DOC, DOCX, PNG, JPG, JPEG).")
        return redirect(url_for("dashboard"))
    original_name = secure_filename(file.filename)
    if not original_name:
        flash("Invalid filename.")
        return redirect(url_for("dashboard"))
    stored_name = secrets.token_hex(16) + "_" + original_name
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], stored_name))
    category = request.form.get("category", "").strip()[:80]
    db = get_db()
    cursor = db.execute("INSERT INTO documents(owner_id,original_name,stored_name,created_at,category) VALUES(?,?,?,?,?)",
                        (session["user_id"], original_name, stored_name, now(), category))
    db.execute("UPDATE users SET role='owner' WHERE id=? AND role='viewer'", (session["user_id"],))
    db.commit()
    log_action(session["user_id"], "upload", cursor.lastrowid, original_name)
    flash("Document uploaded.")
    return redirect(url_for("dashboard"))

@app.route("/download/<int:document_id>")
@login_required
def download(document_id):
    user_id = session["user_id"]
    if not can_access_document(user_id, document_id):
        deny(user_id, "download", document_id)
    document = get_db().execute("SELECT * FROM documents WHERE id=?", (document_id,)).fetchone()
    if not os.path.isfile(os.path.join(app.config["UPLOAD_FOLDER"], document["stored_name"])):
        abort(404)
    log_action(user_id, "download", document_id)
    return send_from_directory(app.config["UPLOAD_FOLDER"], document["stored_name"],
                               as_attachment=True, download_name=document["original_name"])

@app.route("/edit/<int:document_id>", methods=["GET", "POST"])
@login_required
def edit_document(document_id):
    user_id = session["user_id"]
    if not can_access_document(user_id, document_id, "edit"):
        deny(user_id, "edit", document_id)
    document = get_db().execute("SELECT * FROM documents WHERE id=?", (document_id,)).fetchone()
    if not document["original_name"].lower().endswith(".txt"):
        flash("In-app editing is currently supported for TXT files only.")
        return redirect(url_for("dashboard"))
    path = os.path.join(app.config["UPLOAD_FOLDER"], document["stored_name"])
    if request.method == "POST":
        content = request.form.get("content", "")
        if len(content.encode("utf-8")) > 1024 * 1024:
            abort(413)
        with open(path, "w", encoding="utf-8") as stream:
            stream.write(content)
        log_action(user_id, "edit", document_id, "Updated text document")
        flash("Document saved.")
        return redirect(url_for("dashboard"))
    with open(path, encoding="utf-8") as stream:
        content = stream.read()
    return render_template("edit.html", document=document, content=content)

@app.route("/share/<int:document_id>", methods=["POST"])
@login_required
def share(document_id):
    user_id = session["user_id"]
    if not is_document_owner(user_id, document_id):
        deny(user_id, "share", document_id)
    target_id = request.form.get("user_id", type=int)
    permission = request.form.get("permission", "read")
    if permission not in ("read", "edit") or target_id == user_id:
        abort(400)
    db = get_db()
    if not db.execute("SELECT id FROM users WHERE id=?", (target_id,)).fetchone():
        flash("User not found.")
        return redirect(url_for("dashboard"))
    db.execute("""INSERT INTO permissions(document_id,user_id,permission) VALUES(?,?,?)
                  ON CONFLICT(document_id,user_id) DO UPDATE SET permission=excluded.permission""",
               (document_id, target_id, permission))
    db.commit()
    log_action(user_id, "share", document_id, "Shared with user " + str(target_id) + ": " + permission)
    flash("Permission updated.")
    return redirect(url_for("dashboard"))

@app.route("/revoke/<int:document_id>/<int:target_id>", methods=["POST"])
@login_required
def revoke(document_id, target_id):
    user_id = session["user_id"]
    if not is_document_owner(user_id, document_id):
        deny(user_id, "revoke", document_id)
    db = get_db()
    db.execute("DELETE FROM permissions WHERE document_id=? AND user_id=?", (document_id, target_id))
    db.commit()
    log_action(user_id, "revoke", document_id, "Revoked access from user " + str(target_id))
    flash("Access revoked.")
    return redirect(url_for("dashboard"))

@app.route("/audit")
@login_required
def audit():
    logs = get_db().execute("""SELECT a.*,u.username FROM audit_logs a LEFT JOIN users u ON u.id=a.user_id
                               WHERE a.user_id=? ORDER BY a.id DESC LIMIT 200""",
                            (session["user_id"],)).fetchall()
    return render_template("audit.html", logs=logs, admin=False)

@app.route("/admin/audit")
@role_required("admin")
def admin_audit():
    logs = get_db().execute("""SELECT a.*,u.username FROM audit_logs a LEFT JOIN users u ON u.id=a.user_id
                               ORDER BY a.id DESC LIMIT 500""").fetchall()
    return render_template("audit.html", logs=logs, admin=True,
                           chain_valid=verify_audit_chain())

@app.errorhandler(403)
def forbidden(error):
    return "Access denied.", 403

@app.errorhandler(413)
def too_large(error):
    return "File too large. Maximum size is 10 MB.", 413

init_db()

def configure_initial_admin():
    username = os.environ.get("ADMIN_USERNAME", "").strip()
    password = os.environ.get("ADMIN_PASSWORD", "")
    if not username or len(password) < 12:
        return
    db = sqlite3.connect(__import__("database").DATABASE)
    try:
        db.execute(
            "INSERT INTO users(username,password_hash,role) VALUES(?,?, 'admin') "
            "ON CONFLICT(username) DO UPDATE SET role='admin', password_hash=excluded.password_hash",
            (username, generate_password_hash(password))
        )
        db.commit()
    finally:
        db.close()

configure_initial_admin()

if __name__ == "__main__":
    app.run()
