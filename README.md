# TrustVault

TrustVault is a Flask web application for private document upload, controlled sharing, and activity tracking.

- **GitHub:** https://github.com/palavallisuma/TrustVault
- **Existing live demo:** https://trustvault-zkiw.onrender.com

## Main features

- Register and log in with hashed passwords.
- Roles: Admin, Owner, and Viewer.
- Upload, preview and download supported documents (maximum 10 MB).
- Owners can share documents with read or edit permission and revoke access.
- Search accessible documents by file name, owner, category, and date range.
- Edit shared TXT documents when the user has edit permission.
- Audit events include login, upload, view, download, edit, share, revoke and denied access; Admin can view the global audit dashboard.
- HMAC-SHA256 chained audit records with an integrity verification check.
- Server-side access checks and automated tests.

## Roles and permissions

- **Admin:** Can open the global audit dashboard and check the audit-chain integrity.
- **Owner:** The user who uploaded a document. Can manage sharing and revoke access for that document.
- **Viewer:** A newly registered account. Can read documents shared with it. A viewer with explicit edit permission can edit TXT files.

An account becomes an Owner after its first upload. A user can own documents and also view documents shared by others.

## Run locally

1. Install Python 3.10 or later.
2. Clone the repository:
   ```bash
   git clone https://github.com/palavallisuma/TrustVault.git
   cd TrustVault
   ```
3. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows: venv\\Scripts\\activate
   # macOS/Linux: source venv/bin/activate
   ```
4. Install packages:
   ```bash
   pip install -r requirements.txt
   ```
5. Set a strong secret key:
   ```bash
   # macOS/Linux
   export SECRET_KEY="replace-with-a-long-random-secret"
   # PowerShell
   $env:SECRET_KEY="replace-with-a-long-random-secret"
   ```
6. Start the app:
   ```bash
   python app.py
   ```
7. Open http://127.0.0.1:5000 and create an account.

## Create the first Admin account

Do not use a hard-coded default admin password. Set these environment variables before starting the app:

```bash
export ADMIN_USERNAME="your-admin-name"
export ADMIN_PASSWORD="use-a-unique-password-of-at-least-12-characters"
export AUDIT_SECRET="another-long-random-secret-kept-stable"
```

PowerShell:
```powershell
$env:ADMIN_USERNAME="your-admin-name"
$env:ADMIN_PASSWORD="use-a-unique-password-of-at-least-12-characters"
$env:AUDIT_SECRET="another-long-random-secret-kept-stable"
```

On startup, TrustVault creates or promotes that account to Admin. Keep these values private. For production, also set a separate long random `AUDIT_SECRET`; do not change it after audit entries have been written, or integrity verification will fail.

## Demo account setup

TrustVault does not publish default usernames or passwords. Configure the Admin account using the private Render environment variables below. For Owner and Viewer demonstrations, register two separate accounts in the application. Log in as the Owner, upload a sample document, then use the Share form to give the Viewer read or edit permission. Use the Owner account to revoke access. Never commit real passwords or private documents to GitHub.

## Project documentation

- [Threat model and security limitations](THREATS.md)
- [HTTP route and permission reference](API.md)
- [AI development prompt log](PROMPTS.md)

## Run automated tests

```bash
pip install -r requirements.txt
pytest -q
```

The tests cover account roles, upload/view/download, sharing and revocation, editing, search filters, admin audit access, denied access logging, file validation, and audit tampering detection. Check the repository's **Actions** tab for the actual CI result.

## Preview and audit events

Use the **View** link to serve a document through the preview route. A view audit event means the server served that route; it cannot prove that a person actually read the content. Download, upload, edit, share and revoke actions are recorded separately.

## Audit integrity

Each new audit record includes an HMAC-SHA256 signature and the previous record's hash. The Admin audit page checks the chain and reports whether the signed records still match. This helps detect changes to recorded events. Protect the `AUDIT_SECRET` environment variable and database; this is an educational project and not a substitute for a professionally audited logging service.

## Security notes and limitations

- Passwords are hashed; they are not stored as plain text.
- Protected routes check login and document permissions on the server.
- State-changing forms use CSRF tokens.
- File type and file size are checked.
- In-app editing is supported for TXT files only; other file types can be uploaded and downloaded.
- SQLite and uploaded files are stored on the local filesystem. A hosted service needs persistent storage or external database/file storage to retain data across restarts.
- Do not upload confidential or sensitive documents to this educational project.

## Project structure

```text
TrustVault/
├── app.py
├── database.py
├── requirements.txt
├── render.yaml
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── dashboard.html
│   ├── audit.html
│   └── edit.html
├── static/
├── tests/
│   └── test_app.py
└── .github/workflows/
    └── python-app.yml
```
