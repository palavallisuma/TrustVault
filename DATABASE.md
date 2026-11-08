# TrustVault database setup

TrustVault uses SQLite. The schema is created automatically by `database.init_db()` when the Flask application starts. The setup is additive: existing databases are kept, and missing columns are added with safe `ALTER TABLE` migrations.

## Tables

| Table | Purpose | Important fields |
|---|---|---|
| `users` | Login accounts and roles | `id`, unique `username`, `password_hash`, `role` |
| `documents` | Document metadata and ownership | `id`, `owner_id`, `original_name`, `stored_name`, `category`, `created_at`, `deleted_at` |
| `permissions` | Per-document user grants | `document_id`, `user_id`, `permission` (`read` or `edit`) |
| `audit_logs` | Activity history and integrity chain | `user_id`, `document_id`, `action`, `details`, `created_at`, `previous_hash`, `entry_hash` |

Foreign keys connect documents to owners, permissions to documents and users, and audit records to users/documents. SQLite foreign-key enforcement is enabled for application connections. User passwords are stored as Werkzeug password hashes, not plaintext.

## Local setup

From the repository root:

```bash
python -m venv .venv
# Activate the environment, then:
pip install -r requirements.txt
```

Set environment variables before starting the app. Use private, randomly generated values; do not commit secrets:

```bash
export SECRET_KEY="replace-with-a-long-random-secret"
export AUDIT_LOG_KEY="replace-with-a-different-long-random-secret"
python app.py
```

On Windows PowerShell, use `$env:SECRET_KEY = "..."` and `$env:AUDIT_LOG_KEY = "..."`.

By default, SQLite is stored at `trustvault.db` in the project directory and uploaded files are stored in `uploads/`. Override these locations with `DATABASE_PATH` and `UPLOAD_FOLDER`.

## Render persistent-disk setup

The default Render filesystem is ephemeral. To keep uploaded files and SQLite data across deploys/restarts:

1. In the Render dashboard, open the TrustVault web service.
2. Add a persistent disk. Choose a mount path of `/var/data` and a size appropriate for the demo.
3. Add these environment variables to the service:

   - `DATABASE_PATH=/var/data/trustvault.db`
   - `UPLOAD_FOLDER=/var/data/uploads`

4. Save and redeploy.
5. Upload a harmless test file, note its presence, then verify it remains after a controlled redeploy/restart.
6. Keep a separate backup of the SQLite database and uploaded files. A persistent disk is not a backup.

The application creates the database directory and upload directory when it starts. Confirm the selected Render plan supports persistent disks and review its current pricing before adding one.

## Admin and demo account setup

The exact account named by `ADMIN_USERNAME` is reconciled to the `admin` role at application startup and before each login. Its password hash is reset from `ADMIN_PASSWORD`. Choose a dedicated username intended only for administration; if that username currently belongs to an Owner, it will become an Admin.

After first admin creation:

1. Register a dedicated demo Owner through the app's registration page.
2. Sign in as Admin and create a dedicated demo Viewer from the admin page.
3. Sign in as Owner, upload a harmless sample document, and grant the Viewer read access.
4. Test that the Viewer can download the shared sample and cannot access an unshared document.
5. Revoke the grant and confirm the Viewer is denied.

Use only synthetic demo data. Never use customer documents or reuse personal/production passwords for demo accounts.

## Schema and migration notes

The canonical schema and additive migrations are defined in `database.py` in `init_db()`. There is currently no separate SQL dump or migration framework; a clean database is initialized automatically by the application. Back up the database before making manual schema changes.
