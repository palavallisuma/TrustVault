# TrustVault threat model

Updated: 2026-11-08

This threat model describes the current educational implementation. It is not a claim that the application has passed an independent penetration test.

## Assets and trust boundaries

Assets include uploaded document bytes, user accounts and password hashes, session cookies, permission grants, audit records and the HMAC key. The browser is untrusted. The Flask server is the authorization enforcement point. The database and upload directory must remain private server-side resources. Deployment secrets must stay outside Git.

## Threats, controls and accepted limitations

| Threat | Current control | Remaining risk / next step |
|---|---|---|
| User changes a document ID in a download URL (IDOR) | Server checks owner or a matching grant on every download | Add black-box tests for every future file endpoint |
| User guesses another user's file path | Server-generated random storage name and protected download route | Verify hosting does not expose uploads as static content |
| User keeps access after revocation | Every download checks the current permission table | Test revocation while a user remains signed in |
| Viewer attempts edit or upload | Viewer role is denied on upload and metadata edit routes | Add tests for every new mutation route |
| Shared editor changes sharing rules | Only owner/admin can grant or revoke | Recheck when adding group/folder permissions |
| Cross-site form submission | Flask-WTF CSRF protection on POST forms | Test every new form and API mutation |
| Password/database leak | Werkzeug password hashes; no plaintext password storage | Add MFA, rate limiting and account recovery protections |
| Disallowed/oversized upload | Extension allow-list and 10 MB request limit | Not malware scanning or robust file-signature validation |
| Path traversal through filenames | secure_filename plus random server-side stored name | Add content scanning and isolated object storage |
| Audit record modification | New events use HMAC-SHA256 chaining; key is external to database | A compromised app host/key can forge logs; export to independent append-only storage |
| Deletion hides evidence | Deletion event is recorded without a foreign-key dependency on deleted document | Back up audit data separately |
| Search leaks other users' records | Dashboard query is scoped to owner or current user's permission | Add tests for all filters and pagination |
| Public user creates admin | Public registration always creates owner; admin seeded from private environment variables | Protect and rotate initial admin credentials |
| CSRF/session theft | HttpOnly, SameSite=Lax; Secure cookie in production; HSTS on secure requests | Confirm Render environment and HTTPS proxy behavior |
| Data loss after restart/redeploy | Database and upload paths are configurable | Persistent disk, backups and restore test are required |

## Explicitly not built

- Malware scanning or antivirus integration.
- MFA, SSO or password reset.
- Version history, recycle bin or retention policies.
- Group/folder inheritance or external guest sharing.
- Independent immutable audit service or external timestamping.
- Editing the binary contents of PDF/Word files. Edit permission currently covers display name and category metadata.

## Security test plan

1. Create Alice (owner), Bob (viewer) and Charlie (owner).
2. Alice uploads a document. Charlie must receive 403 from the download route.
3. Alice shares read access with Bob. Bob can download.
4. Alice revokes Bob. Bob's next download must receive 403 without signing in again.
5. Change Bob's stored grant to edit in a test database. Viewer role must still be unable to upload or edit metadata.
6. Bob attempts Alice's share/revoke/delete routes. Each must return 403.
7. Tamper with an audit row in a test database. The integrity check must fail.
8. Configure persistent storage, restart/redeploy, and verify both database and file survive.
