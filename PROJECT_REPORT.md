# TrustVault Project Report

## 1. Project overview

TrustVault is an educational Flask web application for uploading documents, sharing them with registered users and recording document-related activity. Its main goal is to demonstrate role-based access control and an audit trail.

## 2. Main roles

- **Admin:** Can access the global audit dashboard and check audit-chain integrity.
- **Owner:** Owns uploaded documents and can grant, update and revoke permissions for other registered users.
- **Viewer:** Can access documents shared with them. Read permission allows viewing and downloading; edit permission additionally allows editing TXT documents.

A newly registered account starts as Viewer. After its first upload, it becomes an Owner. An account may own documents and also receive access to documents owned by other users.

## 3. Main design decisions

- Flask provides the server-side web application and route handling.
- SQLite stores user accounts, document metadata, permissions and audit records.
- Werkzeug password hashing is used rather than storing plain-text passwords.
- Document access is checked on the server for preview, download and edit routes.
- Uploaded filenames are sanitized and stored under generated server-side names.
- File upload size is limited to 10 MB and filename extensions are checked against an allow-list.
- Flask-WTF CSRF protection is enabled for state-changing form submissions.
- Audit records are linked using HMAC-SHA256 and the previous record hash. The Admin dashboard verifies the chain.

## 4. Testing

The GitHub Actions workflow runs Python lint checks and pytest. The latest verified pull-request CI run for the current application changes reported 16 passing tests. Tests cover registration and roles, upload/download, preview audit events, sharing and revocation, editing permissions, search filters, Admin audit access, denied access, file validation, CSRF rejection and audit tampering detection.

CI passing does not prove the absence of all vulnerabilities. Manual testing on the live deployment is still required.

## 5. Known limitations and unfinished production work

- In-app editing is supported only for TXT files.
- Extension validation is not malware scanning or deep file-content validation.
- The application does not currently include multi-factor authentication or login rate limiting.
- Audit-chain verification depends on protecting the AUDIT_SECRET. It is tamper-evident, not a truly immutable external audit service.
- SQLite and uploaded files are stored on the local filesystem. Persistent managed database and file storage are needed to retain data reliably on a hosted service.
- Manual Admin, Owner and Viewer testing on the deployed version must be completed before claiming live end-to-end verification.

## 6. Conclusion

TrustVault demonstrates basic role-based document sharing, server-side permission checks, CSRF protection, document activity logging and tamper-evident audit records. It is suitable as an educational project demonstration, subject to the limitations listed above.
