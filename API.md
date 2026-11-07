# TrustVault HTTP Route Reference

TrustVault currently uses server-rendered HTML routes. It does not expose a separate JSON REST API.

All routes except registration, login and the home page require an authenticated session where noted. Document permissions are checked on the server.

| Method | Route | Login required | Authorization / purpose |
|---|---|---:|---|
| GET | `/` | No | Home page |
| GET, POST | `/register` | No | Create a Viewer account |
| GET, POST | `/login` | No | Authenticate and create session |
| POST | `/logout` | Yes | End current session |
| GET | `/dashboard` | Yes | List documents owned by or shared with current user; supports name, owner, category and date filters |
| POST | `/upload` | Yes | Upload a file; current user becomes Owner after first upload |
| GET | `/view/<document_id>` | Yes | Serve a document preview to its Owner or a user with read/edit permission; records a view event |
| GET | `/download/<document_id>` | Yes | Download a document for its Owner or a user with read/edit permission |
| GET, POST | `/edit/<document_id>` | Yes | View or edit TXT files for Owner or a user with edit permission |
| POST | `/share/<document_id>` | Yes | Owner only; grant or update read/edit permission for another registered user |
| POST | `/revoke/<document_id>/<target_id>` | Yes | Owner only; remove the target user's permission |
| GET | `/audit` | Yes | View current user's activity |
| GET | `/admin/audit` | Yes | Admin role only; view global audit records and verify the HMAC chain |

## Permission rules

- Owner: may view, download, edit TXT documents, grant/update permissions and revoke access to documents they own.
- Viewer with read permission: may view and download, but cannot edit.
- Viewer with edit permission: may view, download and edit TXT files.
- Unshared users: cannot view, download or edit the document.
- Admin: can access the global audit dashboard. Admin status does not automatically grant ownership of every document.

## Audit action names

The application records actions including `login`, `logout`, `upload`, `view`, `download`, `edit`, `share`, `revoke`, and denied access attempts such as `denied_download`.

A `view` event means the server served the preview route. It cannot prove that a person actually read the file.

## File constraints

Maximum upload size is 10 MB. Allowed filename extensions are PDF, TXT, DOC, DOCX, PNG, JPG and JPEG. Only TXT files support in-app editing. Extension checking does not provide malware scanning or deep content validation.


## Request protection

All POST form submissions, including login, registration, upload, share, revoke, edit and logout, require a valid Flask-WTF CSRF token. GET routes are read-only and do not require a CSRF form token.
