# Five-minute TrustVault demo recording script

Record your own screen with the deployed application. Use only test documents and demo accounts, never private files or real passwords on camera.

## Before recording

- Confirm the latest GitHub Actions run passes.
- Wait for the Render service to finish deploying the latest main-branch commit.
- Set ADMIN_USERNAME and ADMIN_PASSWORD privately in Render, then sign in as admin once.
- Create one viewer account from the admin page.
- Register a separate owner account.
- Prepare a harmless sample TXT file containing: "TrustVault demo document".
- Keep the three demo usernames/passwords available privately for the judge handover.

## Timeline

**0:00–0:30 — Introduction**
Explain that TrustVault is a document-sharing app where the server checks permissions for each document request and records activity.

**0:30–1:00 — Admin**
Sign in as administrator. Show the user list, document overview and system activity page. Point out the audit integrity status.

**1:00–1:40 — Owner upload**
Sign out and sign in as owner. Upload the sample TXT file, assign a category and show it in the dashboard.

**1:40–2:20 — Search and sharing**
Search by file name/category. Share the file with the viewer account using read permission.

**2:20–3:00 — Viewer access**
Sign out and sign in as viewer. Download the shared file. Explain that viewer accounts are read-only.

**3:00–3:40 — Unauthorized access**
As viewer, try to open a different owner's document ID (use a test document not shared with this viewer). Show the 403 denial. Do not claim a test passed unless the response is visible.

**3:40–4:15 — Revocation**
Sign back in as owner, revoke viewer access, then sign in as viewer again and repeat the download. Show that access is denied immediately.

**4:15–4:45 — Audit trail**
Open the owner's audit page and show upload, permission grant/revocation, download and denied-attempt records where applicable. Show the chain integrity status.

**4:45–5:00 — Wrap-up**
Mention the main limitations honestly: demo storage needs a persistent disk, audit records created before the HMAC upgrade are legacy, and editing applies to metadata rather than the document's binary contents.
