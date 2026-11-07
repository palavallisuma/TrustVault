import io
from werkzeug.security import generate_password_hash
import database
from app import app, log_action, verify_audit_chain

import pytest

@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    upload_path = tmp_path / "uploads"
    upload_path.mkdir()
    monkeypatch.setattr(database, "DATABASE", str(db_path))
    app.config.update(TESTING=True, SECRET_KEY="test-secret", UPLOAD_FOLDER=str(upload_path))
    database.init_db()
    with app.test_client() as c:
        yield c

def db_one(sql, params=()):
    with app.app_context():
        return database.get_db().execute(sql, params).fetchone()

def db_exec(sql, params=()):
    with app.app_context():
        db = database.get_db()
        db.execute(sql, params)
        db.commit()

def register(c, name):
    return c.post("/register", data={"username":name,"password":"strong-password-123"}, follow_redirects=True)

def login(c, name, password="strong-password-123"):
    return c.post("/login", data={"username":name,"password":password}, follow_redirects=True)

def upload(c, filename="file.txt", content=b"original", category="Study"):
    return c.post("/upload", data={"file":(io.BytesIO(content),filename),"category":category},
                  content_type="multipart/form-data", follow_redirects=True)

def test_register_login_and_default_viewer(client):
    register(client,"alice")
    assert db_one("SELECT role FROM users WHERE username='alice'")["role"] == "viewer"
    assert b"Welcome, alice" in login(client,"alice").data

def test_dashboard_requires_login(client):
    assert client.get("/dashboard").status_code == 302

def test_upload_download_and_owner_role(client):
    register(client,"alice")
    login(client,"alice")
    upload(client)
    assert db_one("SELECT role FROM users WHERE username='alice'")["role"] == "owner"
    response=client.get("/download/1")
    assert response.status_code == 200 and response.data == b"original"

def test_viewer_read_allowed_edit_denied(client):
    register(client,"alice"); register(client,"bob")
    login(client,"alice"); upload(client)
    client.post("/share/1",data={"user_id":"2","permission":"read"})
    client.post("/logout"); login(client,"bob")
    assert client.get("/download/1").status_code == 200
    assert client.get("/edit/1").status_code == 403

def test_editor_can_edit_txt(client):
    register(client,"alice"); register(client,"bob")
    login(client,"alice"); upload(client)
    client.post("/share/1",data={"user_id":"2","permission":"edit"})
    client.post("/logout"); login(client,"bob")
    assert client.get("/edit/1").status_code == 200
    client.post("/edit/1",data={"content":"changed"})
    assert client.get("/download/1").data == b"changed"

def test_non_owner_cannot_share_or_revoke(client):
    register(client,"alice"); register(client,"bob"); register(client,"carol")
    login(client,"alice"); upload(client)
    client.post("/share/1",data={"user_id":"2","permission":"edit"})
    client.post("/logout"); login(client,"bob")
    assert client.post("/share/1",data={"user_id":"3","permission":"read"}).status_code == 403
    assert client.post("/revoke/1/2").status_code == 403

def test_search_by_name_and_category(client):
    register(client,"alice"); login(client,"alice")
    upload(client,"lecture.txt",b"one","College")
    upload(client,"recipe.txt",b"two","Home")
    response=client.get("/dashboard?q=lecture&category=College")
    assert b"lecture.txt" in response.data and b"recipe.txt" not in response.data

def test_admin_audit_access_is_role_protected(client):
    register(client,"alice"); login(client,"alice")
    assert client.get("/admin/audit").status_code == 403
    client.post("/logout")
    db_exec("INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",
            ("admin",generate_password_hash("admin-password-123"),"admin"))
    login(client,"admin","admin-password-123")
    assert client.get("/admin/audit").status_code == 200

def test_denied_download_is_audited(client):
    register(client,"alice"); register(client,"bob")
    login(client,"alice"); upload(client)
    client.post("/logout"); login(client,"bob")
    assert client.get("/download/1").status_code == 403
    assert db_one("SELECT id FROM audit_logs WHERE action='denied_download'") is not None

def test_audit_chain_detects_tampering(client):
    register(client,"alice"); login(client,"alice")
    with app.app_context():
        log_action(1,"test_event",None,"original")
        assert verify_audit_chain()
    db_exec("UPDATE audit_logs SET details='tampered' WHERE action='test_event'")
    with app.app_context():
        assert verify_audit_chain() is False

def test_unsupported_file_type_rejected(client):
    register(client,"alice"); login(client,"alice")
    response=upload(client,"payload.exe")
    assert b"supported file" in response.data
