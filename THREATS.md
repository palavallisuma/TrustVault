# TrustVault Threat Model

## Scope

TrustVault is an educational Flask application for uploading documents and sharing them with other registered users. It is not a certified document-management or production security product.

## Assets to protect

- Usernames and password hashes
- Uploaded document contents
- Document ownership and read/edit permissions
- Session cookies and application secrets
- Audit records and their integrity chain

## Trust boundaries

- A browser is untrusted. Every protected route must check the session and document permission on the server.
- A registered user is not automatically trusted to access another user's documents.
- The application server and its environment variables are trusted only while the host and deployment account remain secure.
- The SQLite database and upload directory contain sensitive application data and must be protected together.

## Main threats and current controls

| Threat | Current control | Remaining limitation |
|---|---|---|
| Password disclosure from database theft | Passwords are stored as Werkzeug password hashes, not plain text | No multi-factor authentication or login rate limiting |
| User accesses another user's document | Server-side owner/share permission checks on view, download and edit routes | Must be tested on the deployed instance; administrator does not automatically own every document |
| Viewer changes a read-only document | Edit route requires owner or explicit edit permission | Editing is limited to TXT files |
| Owner's sharing controls abused by another user | Share and revoke routes require document ownership | CSRF protection is not currently implemented; malicious cross-site form submissions remain a risk |
| Unsafe filename/path manipulation | Werkzeug secure_filename and generated stored names | File content is not malware-scanned |
| Oversized upload | Flask request limit and 10 MB application limit | Allowed extension checking is not a substitute for MIME/content inspection |
| Unsupported file extension | Server-side extension allow-list | An attacker may rename a file; actual file contents are not deeply validated |
| Audit record edited in database | HMAC-SHA256 chained records, with Admin integrity check | Detection depends on protecting AUDIT_SECRET; this is not an external immutable log |
| Secret leakage | Secrets are configured through environment variables | Anyone with Render environment access can read/change them |
| Data loss after restart/redeploy | README explains local filesystem storage | SQLite and uploads need persistent storage or managed external storage on hosting |
| Session theft | HttpOnly and SameSite=Lax cookie settings; secure cookie can be enabled | HTTPS deployment should set COOKIE_SECURE=1; no session revocation dashboard |

## Recommended deployment settings

- Set a long, random SECRET_KEY in the host environment.
- Set a separate, long, random AUDIT_SECRET and keep it stable. Changing it makes existing signed audit entries fail verification.
- Set ADMIN_USERNAME and an ADMIN_PASSWORD of at least 12 characters privately in the host environment.
- Set COOKIE_SECURE=1 when the app is served over HTTPS.
- Restrict access to the hosting account, database and upload storage.
- Do not upload real confidential documents to this educational demo.

## Security tests

The automated tests cover authentication, owner promotion, permitted and denied access, sharing/revocation, upload extension checks, audit event creation and audit tampering detection. Passing tests do not prove the application is free from vulnerabilities. Perform manual tests against the deployed URL before evaluation.

## Known work not implemented

- CSRF tokens on state-changing forms
- Malware scanning and deep file-content validation
- Login throttling / account lockout
- Multi-factor authentication
- External immutable audit storage
- Persistent managed database and object storage configuration
- Automated backup and recovery
