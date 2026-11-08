import io
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import database
from app import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    database_path = tmp_path / "test_trustvault.db"
    upload_path = tmp_path / "uploads"
    upload_path.mkdir()
    monkeypatch.setattr(database, "DATABASE", str(database_path))
    monkeypatch.setattr("app.UPLOAD_FOLDER", str(upload_path))
    app.config.update(
        TESTING=True, SECRET_KEY="test-only-secret",
        WTF_CSRF_ENABLED=False, MAX_CONTENT_LENGTH=10 * 1024 * 1024,
    )
    database.init_db()
    with app.test_client() as test_client:
        yield test_client


def register(client, username, password="test-password-123"):
    return client.post("/register", data={"username": username, "password": password},
                       follow_redirects=True)


def login(client, username, password="test-password-123"):
    return client.post("/login", data={"username": username, "password": password},
                       follow_redirects=True)


def logout(client):
    return client.post("/logout", follow_redirects=True)


def upload_text_file(client, filename="notes.txt", content=b"TrustVault test file"):
    return client.post("/upload",
        data={"file": (io.BytesIO(content), filename), "category": "Reports"},
        content_type="multipart/form-data", follow_redirects=True)


def test_registration_login_and_dashboard(client):
    response = register(client, "alice")
    assert response.status_code == 200
    assert b"Account created" in response.data
    login(client, "alice")
    assert b"Welcome, alice" in client.get("/dashboard").data
    assert client.get("/dashboard").status_code == 200


def test_dashboard_requires_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_owner_upload_download_and_search(client):
    register(client, "alice")
    login(client, "alice")
    assert upload_text_file(client).status_code == 200
    assert b"notes.txt" in client.get("/dashboard?q=notes&category=Reports").data
    response = client.get("/download/1")
    assert response.status_code == 200
    assert response.data == b"TrustVault test file"


def test_shared_user_can_download_but_unshared_user_cannot(client):
    register(client, "alice")
    register(client, "bob")
    register(client, "charlie")
    login(client, "alice")
    upload_text_file(client)
    assert client.post("/share/1", data={"user_id": "2", "permission": "read"}).status_code == 302
    logout(client)
    login(client, "bob")
    assert client.get("/download/1").status_code == 200
    logout(client)
    login(client, "charlie")
    assert client.get("/download/1").status_code == 403


def test_viewer_is_read_only_even_if_database_grant_is_edit(client):
    register(client, "owner")
    register(client, "viewer")
    with app.app_context():
        db = database.get_db()
        db.execute("UPDATE users SET role='viewer' WHERE username='viewer'")
        db.execute("INSERT INTO documents(owner_id, original_name, stored_name, category, created_at) VALUES (1,'a.txt','a.txt','General','2026-01-01')")
        db.execute("INSERT INTO permissions(document_id,user_id,permission) VALUES (1,2,'edit')")
        db.commit()
    Path(app.UPLOAD_FOLDER, "a.txt").write_bytes(b"viewer download test")
    login(client, "viewer")
    assert client.get("/download/1").status_code == 200
    assert client.post("/document/1/update", data={"name":"b.txt","category":"New"}).status_code == 403
    assert client.post("/upload", data={}).status_code == 403


def test_only_owner_can_change_permissions_and_revoke(client):
    register(client, "alice")
    register(client, "bob")
    register(client, "charlie")
    login(client, "alice")
    upload_text_file(client)
    assert client.post("/share/1", data={"user_id":"2","permission":"edit"}).status_code == 302
    assert client.post("/share/1", data={"user_id":"3","permission":"read"}).status_code == 302
    logout(client)
    login(client, "bob")
    assert client.post("/share/1", data={"user_id":"3","permission":"edit"}).status_code == 403
    assert client.post("/revoke/1/3").status_code == 403


def test_audit_is_user_scoped_and_chain_verifies(client):
    register(client, "alice")
    register(client, "bob")
    login(client, "alice")
    upload_text_file(client)
    logout(client)
    login(client, "bob")
    response = client.get("/audit")
    assert b"upload" not in response.data
    assert b"Valid" in response.data


def test_disallowed_extension_is_rejected(client):
    register(client, "alice")
    login(client, "alice")
    response = upload_text_file(client, filename="malware.exe")
    assert b"File type or file content is not valid" in response.data


def test_admin_can_view_activity_and_create_viewer(client):
    from werkzeug.security import generate_password_hash
    with app.app_context():
        db = database.get_db()
        db.execute("INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",
                   ("admin", generate_password_hash("admin-password"), "admin"))
        db.commit()
    login(client, "admin", "admin-password")
    assert client.get("/admin").status_code == 200
    response = client.post("/admin/users", data={
        "username":"newviewer", "password":"viewer-password", "role":"viewer"
    })
    assert response.status_code == 302
    with app.app_context():
        user = database.get_db().execute("SELECT role FROM users WHERE username='newviewer'").fetchone()
        assert user["role"] == "viewer"


def test_delete_keeps_deletion_audit_record(client):
    register(client, "owner")
    login(client, "owner")
    upload_text_file(client)
    assert client.post("/delete/1").status_code == 302
    assert client.get("/download/1").status_code == 404
    with app.app_context():
        row = database.get_db().execute(
            "SELECT action, document_id FROM audit_logs WHERE action='deletion'"
        ).fetchone()
        assert row["action"] == "deletion"
        assert row["document_id"] == 1
        from app import verify_audit_chain
        assert verify_audit_chain() is True
