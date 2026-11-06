# TrustVault

Confidential document sharing where **the wrong person cannot reach a
document**, and where you can **prove who reached it**, including the
attempts that were refused.

* Per-document sharing with named people, **read** or **edit**, optionally
  **time-limited**. Checked on the server on every request; nothing is
  cached, so revoking takes effect on the next click.
* Files are **encrypted at rest** (AES-256-GCM, a fresh key per version,
  wrapped by a master key) and only ever served as downloads after the check.
* **Version history**: every upload is kept; editors can download old versions.
* **Trash**: owners can delete, restore, or permanently purge. Trashed
  documents are invisible to everyone they were shared with.
* A **tamper-evident audit log**: append-only in the database, HMAC
  hash-chained, with the chain head printed to the platform log.
* **Per-document activity** for owners, including refused attempts.
* An **admin console**: deactivate/reactivate accounts, change roles, read
  and verify the audit log, and security **alerts** (access probing, failed
  logins, password spraying, bulk downloads, mass sharing, privileged
  changes, broken audit chain). The admin role gives **no document access**.
* **Login throttling**, password change that signs out other sessions,
  CSRF tokens, strict Content-Security-Policy.

| Document | What is in it |
|---|---|
| [THREATS.md](THREATS.md) | Threats, what stops each one, and which test covers it |
| [PROMPTS.md](PROMPTS.md) | How AI was used, and where it was wrong |
| [docs/mutation-results.txt](docs/mutation-results.txt) | Result of removing each security check and re-running the tests |

## Permissions

| Action | read | edit | owner |
|---|:-:|:-:|:-:|
| View details, download current version | ✓ | ✓ | ✓ |
| Download old versions, upload a new version, edit title/description | | ✓ | ✓ |
| Share / revoke, view activity log, move to trash, restore, purge | | | ✓ |

A user with no access gets `404 Not found`, exactly as if the document did
not exist. `403` is only returned when the user can already see the
document. All of this is decided in one place: `authz.py`.

## Demo accounts

Run `python seed.py` on an empty database (or set `TRUSTVAULT_AUTO_SEED=1`).

| Username | Password | What they have |
|---|---|---|
| `admin` | `Admin-Demo-2026!` | User management and audit. **No document access.** |
| `olivia` | `Owner-Demo-2026!` | Owns 2 salary letters and the HR handbook |
| `oscar` | `Owner-Demo-2026!` | Owns a partner contract and an unshared litigation memo |
| `vera` | `Viewer-Demo-2026!` | Read: her own salary letter and the handbook |
| `victor` | `Viewer-Demo-2026!` | Read: his own salary letter. Edit: the handbook |
| `pat` | `Viewer-Demo-2026!` | Read: the partner contract only |

Things to try:

* Sign in as Vera and open `/documents/2` (Victor's letter). You get 404,
  and Olivia's activity log for that document shows the refusal.
* As Olivia, revoke Vera's grant while Vera has the document open. Vera's
  next click fails.
* As admin, open *Admin* to see alerts, and *Audit* to verify the chain.
  Try to download any document as admin.

## Run locally

Requires Python 3.10+.

    python -m venv .venv && . .venv/bin/activate
    pip install -r requirements.txt
    python seed.py          # optional demo data
    python app.py           # http://127.0.0.1:5000  (FLASK_DEBUG=1 for the debugger)

In development, missing keys are generated once and saved in the data
directory (`instance/` by default). Production refuses to start without
real keys.

## Tests

    pip install -r requirements-dev.txt
    pytest                              # 35 tests
    python scripts/mutation_check.py    # removes each security check in turn; every one must fail the suite

## Configuration

| Variable | Required | Meaning |
|---|---|---|
| `TRUSTVAULT_ENV` | | `production` requires real keys and enables Secure cookies and HSTS |
| `SECRET_KEY` | prod | Signs session cookies |
| `TRUSTVAULT_MASTER_KEY` | prod | 64 hex characters. Wraps every file's key. **Losing it means losing every file.** |
| `TRUSTVAULT_AUDIT_KEY` | prod | 64 hex characters, different from the master key. Signs the audit chain. |
| `TRUSTVAULT_DATA_DIR` | | Database and encrypted files. Must be persistent storage. |
| `TRUSTVAULT_TRUST_PROXY` | | `1` only behind exactly one trusted proxy (Render, Fly), so client IPs are right |
| `TRUSTVAULT_AUTO_SEED` | | `1` seeds demo data on first start (empty database only) |
| `TRUSTVAULT_SEED_PASSWORD` | | Overrides every demo password |

Generate keys with `python -c "import secrets; print(secrets.token_hex(32))"`
(once for each key).

## Deploy

Any host that runs a Docker image with **one instance and a persistent
disk** works (SQLite).

    docker build -t trustvault .
    docker run -d -p 8080:8080 -v trustvault-data:/data \
      -e SECRET_KEY=... -e TRUSTVAULT_MASTER_KEY=... -e TRUSTVAULT_AUDIT_KEY=... \
      -e TRUSTVAULT_AUTO_SEED=1 trustvault

Without Docker: `gunicorn -w 4 wsgi:app` with the same environment variables.

Keep the keys in the platform's secret store and back them up separately
from the data. The platform log keeps one line per audit append:
`{"type": "audit_head", "seq": …, "hash": …}`. To check nobody deleted
recent entries, paste the latest one into *Audit → Verify audit chain*.

If you ran an earlier version of this app, delete the old `trustvault.db`
and `uploads/`: the schema changed and files are now encrypted.

## Layout

    app.py          routes
    authz.py        the authorisation decision (read this first)
    audit.py        hash-chained audit log
    storage.py      encrypted file storage
    validation.py   upload and form validation
    alerts.py       admin alerts
    database.py     schema and transactions
    config.py       keys
    seed.py         demo data
    wsgi.py         gunicorn entry point
    templates/ static/
    tests/          pytest suites
    scripts/mutation_check.py
