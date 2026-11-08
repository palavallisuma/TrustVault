# TrustVault

TrustVault is a Flask document-sharing application. Owners upload documents, grant named users read/edit access, and revoke that access. Every new activity is recorded in an HMAC-linked audit chain.

- **Live demo:** https://trustvault-zkiw.onrender.com
- **Source code:** https://github.com/palavallisuma/TrustVault

## Roles

- **Admin:** created only from deployment environment variables; can view users, documents and system activity, and create owner/viewer accounts.
- **Owner:** registers normally, uploads documents, searches their own and shared documents, grants/revokes permissions, edits document details and deletes their own documents.
- **Viewer:** created by an admin; can download only documents explicitly shared with them. Viewer accounts are read-only even if an old database grant says edit.

The server checks authorization on each protected route. Hiding a button is not an access-control check.

## Features

- Password hashing and session-based login.
- Per-document read/edit grants and immediate revocation checks.
- Private file downloads through an authorization-checked route.
- 10 MB upload limit and extension allow-list (PDF, TXT, DOC, DOCX, PNG, JPG, JPEG).
- Search by document name, owner, category and date range.
- Document detail editing and owner deletion.
- User-scoped audit history and admin-wide activity view.
- HMAC-SHA256 chained audit entries for new events.
- CSRF protection on POST forms and security response headers.
- Automated tests for ownership, sharing, viewer restrictions, downloads, deletion and audit behavior.

## Run locally

Python 3.10+ is recommended.

```bash
git clone https://github.com/palavallisuma/TrustVault.git
cd TrustVault
python -m venv venv
```

Activate the environment:

- Windows: `venv\\Scripts\\activate`
- macOS/Linux: `source venv/bin/activate`

Install and configure:

```bash
pip install -r requirements.txt
```

Set a strong secret before starting. Use a separate random key for the audit chain in production.

macOS/Linux:
```bash
export SECRET_KEY="replace-with-a-long-random-secret"
export AUDIT_LOG_KEY="replace-with-a-different-long-random-secret"
python app.py
```

Windows PowerShell:
```powershell
$env:SECRET_KEY = "replace-with-a-long-random-secret"
$env:AUDIT_LOG_KEY = "replace-with-a-different-long-random-secret"
python app.py
```

Open http://127.0.0.1:5000 and register an owner account. To create the first administrator, set both `ADMIN_USERNAME` and `ADMIN_PASSWORD` before the first app start. The application creates that admin only when no admin account already exists. Log in as admin, then use the admin page to create viewer accounts.

## Demo credentials for judges

Create dedicated demo accounts using synthetic data before sharing the live demo. The repository does not contain pre-seeded accounts, so the account owner must create these accounts in the deployed app and then replace the placeholders below with the actual demo-only credentials:

| Role | Demo username | Demo password |
|---|---|---|
| Admin | `<add dedicated demo admin username>` | `<add demo-only password>` |
| Owner | `<add demo owner username>` | `<add demo-only password>` |
| Viewer | `<add demo viewer username>` | `<add demo-only password>` |

Do not publish personal passwords, production admin credentials, `SECRET_KEY`, or `AUDIT_LOG_KEY`. If the challenge requires public judge access, use accounts created only for this demo, restrict them to synthetic sample documents, and rotate/delete them after judging. Admin is initially created from the deployment environment only when no admin account already exists; changing environment variables does not reset an existing admin password.

See [DATABASE.md](DATABASE.md) for the schema, clean setup, Render persistent-disk configuration and demo-account creation steps.

## Run automated tests

```bash
pip install -r requirements.txt
pytest -q
```

GitHub Actions runs pytest and basic lint checks on pushes to `main`. Check the repository Actions tab for the actual run result.

## Deploy on Render

The repository includes `render.yaml`. Connect the GitHub repository to Render and deploy the web service with:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- `SECRET_KEY`: strong private random value
- `AUDIT_LOG_KEY`: separate strong private random value
- `FLASK_ENV=production`
- Optional first-admin setup: `ADMIN_USERNAME` and `ADMIN_PASSWORD`

**Important storage limitation:** the default SQLite database and uploads directory are local filesystem paths. On hosts with ephemeral filesystems, uploaded files and database changes can disappear after a restart/redeploy. Configure a persistent disk and set `DATABASE_PATH` and `UPLOAD_FOLDER` to paths on that disk before using real documents. Do not use the demo for confidential files until persistent storage, backups and restore have been verified.

## Security and known limitations

- Uploaded files are checked by extension and size. This is not malware scanning or deep content-type validation.
- The audit chain uses HMAC-SHA256. Keep `AUDIT_LOG_KEY` secret and back it up securely. Legacy audit rows created before this upgrade cannot be authenticated retroactively; new chained entries are verified separately.
- A local SQLite database is suitable for this small demonstration, not a high-volume multi-instance production service.
- No malware scanning, MFA, external identity provider, version history or recovery workflow is included.
- The edit permission currently permits editing document metadata (display name/category), not changing the binary contents of a PDF/Word file.
- Review `THREATS.md`, `PROMPTS.md`, `API.md` and `DATABASE.md` for the security model, AI-use notes, route-level access rules and database setup.

This is an educational project. Do not upload confidential documents or use it as a production document-management service without a further security review.
