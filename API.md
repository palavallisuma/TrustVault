# TrustVault route and permission reference

All write operations use POST forms protected by Flask-WTF CSRF tokens. Authorization is enforced in the route, not only in the UI.

| Route | Method | Access | Purpose |
|---|---|---|---|
| / | GET | Public | Landing page |
| /register | GET/POST | Public | Register owner account |
| /login | GET/POST | Public | Sign in |
| /logout | POST | Signed-in user | End session |
| /dashboard | GET | Owner/viewer | View accessible documents and search |
| /upload | POST | Owner/admin | Upload a file (10 MB max) |
| /download/{document_id} | GET | Owner, admin or explicitly granted user | Download after server-side permission check |
| /share/{document_id} | POST | Document owner/admin | Grant read or edit permission |
| /revoke/{document_id}/{target_id} | POST | Document owner/admin | Revoke a user's grant |
| /document/{document_id}/update | POST | Owner or non-viewer with edit grant | Change display name/category |
| /delete/{document_id} | POST | Document owner/admin | Delete file and metadata; retain deletion audit event |
| /audit | GET | Signed-in user | View own audit entries and chain status |
| /admin | GET | Admin only | View users, documents and system activity |
| /admin/users | POST | Admin only | Create owner/viewer account |

## Permission rules

- Owner can read, edit metadata, share, revoke and delete their document.
- Shared read user can download only.
- Shared edit user can download and edit document metadata.
- Viewer account is read-only even if a database permission row says edit.
- Admin can inspect all documents and system activity. Public registration cannot create admin.
- Unknown document IDs return 404. Existing but unauthorized downloads/mutations return 403.

## Search fields

Dashboard accepts q (document name), owner, category, date_from and date_to. Results remain scoped to documents owned by or shared with the signed-in user.
