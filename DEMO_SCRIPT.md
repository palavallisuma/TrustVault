# TrustVault 5-Minute Demonstration Script

Use this script while recording your own screen. Do not show real passwords, private files, or secret environment values.

| Time | Demonstration |
|---|---|
| 0:00–0:30 | Introduce TrustVault: a Flask application for private document upload, controlled sharing and activity tracking. Show the home page and GitHub repository. |
| 0:30–1:10 | Log in as Admin using the credentials configured privately in Render. Show the role label and Admin Audit Dashboard. |
| 1:10–2:00 | Log out. Register or log in as the Owner account. Upload a harmless sample TXT file and show it in the dashboard. |
| 2:00–2:50 | Share the sample document with the Viewer account using read permission. Show the permission listed for that Viewer. |
| 2:50–3:35 | Log out and log in as Viewer. Open the shared document using View and Download. Show that editing is not allowed with read permission. |
| 3:35–4:10 | Log out, return as Owner and revoke the Viewer permission. Log in as Viewer again and show that access is denied. |
| 4:10–4:40 | Return as Admin and show the audit entries for upload, view, download, share, revoke and denied access. Show the audit-chain integrity result. |
| 4:40–5:00 | Show the GitHub Actions passing result and briefly mention the documented limitations. |

## Recording checklist

- Use separate Admin, Owner and Viewer accounts.
- Use a harmless sample file named demo-notes.txt.
- Confirm the deployed version contains the latest branch changes before recording.
- Make sure the Admin environment variables are configured in Render.
- Do not display passwords, secret keys, personal documents or private account information.
- Record the actual application behavior. Do not narrate an action as successful unless it worked during recording.
