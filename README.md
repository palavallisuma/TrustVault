# TrustVault

**TrustVault** is a Flask-based secure document-sharing application. It is designed to let registered users upload documents, keep ownership of their files, share access with other users, and review account activity.

- **Live demo:** https://trustvault-zkiw.onrender.com
- **GitHub repository:** https://github.com/palavallisuma/TrustVault

## Contents

- [TrustVault](#trustvault)
- [Problem statement](#problem-statement)
- [Features](#features)
- [Project structure](#project-structure)
- [Run locally](#run-locally)
- [Run automated tests](#run-automated-tests)
- [Deploy on Render](#deploy-on-render)
- [Security notes](#security-notes)
- [Current implementation status](#current-implementation-status)

## Problem statement

Documents shared between people or teams can be exposed, changed, or downloaded by users who should not have access. TrustVault addresses this problem by providing a centralized application for document storage and controlled sharing.

The project objectives are to:

1. Allow users to register, sign in, and manage their own documents.
2. Support document upload, download, and organized access.
3. Let document owners grant and revoke document-specific permissions.
4. Distinguish read access from edit access and prevent unauthorized actions.
5. Record important activity, including access-denied attempts, for accountability.
6. Provide an audit view so activity can be reviewed.
7. Validate uploaded files and restrict unsupported file types and oversized uploads.
8. Use automated tests to check authentication, permission enforcement, and isolation between users.
9. Document security assumptions, threats, and the use of AI assistance where applicable.

## Features

The current application includes:

- User registration and login.
- Password hashing using Werkzeug.
- Private document ownership.
- Upload support for PDF, TXT, DOC, DOCX, PNG, JPG, and JPEG files.
- A maximum upload size of 10 MB.
- File-name sanitization and randomized stored file names.
- Document sharing with read or edit permission values.
- Server-side checks for document download access.
- Owner-only permission sharing and revocation routes.
- Audit entries for login, logout, upload, download, sharing, revocation, and denied downloads.
- Per-user audit history.
- SQLite database storage.
- GitHub Actions workflow configured to run lint checks and pytest.

## Project structure

```text
TrustVault/
├── .github/
│   └── workflows/
│       └── python-app.yml
├── static/
│   └── style.css
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── dashboard.html
│   └── audit.html
├── tests/
├── app.py
├── database.py
├── requirements.txt
├── render.yaml
└── README.md
```

## Run locally

### 1. Install Python

Install Python 3.10 or later.

### 2. Clone the repository

```bash
git clone https://github.com/palavallisuma/TrustVault.git
cd TrustVault
```

### 3. Create and activate a virtual environment

**Windows (Command Prompt):**

```bash
python -m venv venv
venv\\Scripts\\activate
```

**Linux / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure the Flask secret key

Set a long, random secret key in your environment before running the application. Do not commit the secret key to GitHub.

**Windows (PowerShell):**

```powershell
$env:SECRET_KEY = "replace-with-a-long-random-secret"
```

**Linux / macOS:**

```bash
export SECRET_KEY="replace-with-a-long-random-secret"
```

### 6. Start the application

```bash
python app.py
```

Open this address in your browser:

http://127.0.0.1:5000

Create an account using the registration page, then sign in. The application initializes its SQLite database when it starts.

## Run automated tests

Install the project dependencies and pytest:

```bash
pip install -r requirements.txt
pip install pytest
```

Run the test suite from the repository root:

```bash
pytest
```

The GitHub Actions workflow in `.github/workflows/python-app.yml` is configured to run Python lint checks and pytest on pushes and pull requests targeting `main`.

## Deploy on Render

This repository includes a `render.yaml` file for a Render web service.

1. Push the project to GitHub.
2. Sign in to [Render](https://render.com/).
3. Choose **New** → **Blueprint** (or create a **Web Service** and connect the GitHub repository).
4. Select the `palavallisuma/TrustVault` repository.
5. If using the Blueprint, let Render read the settings from `render.yaml`.
6. Confirm the build command is `pip install -r requirements.txt`.
7. Confirm the start command is `gunicorn app:app`.
8. In the Render environment settings, set `SECRET_KEY` to a long, random secret value. Keep it private.
9. Deploy and open the service URL.

**Live application:** https://trustvault-zkiw.onrender.com

> **Deployment storage note:** The current application stores its SQLite database and uploaded files on the service's local filesystem. On a hosting plan with an ephemeral filesystem, this data can be lost when the service restarts or is redeployed. Configure persistent storage or move to managed database/object storage before relying on the deployment for important documents.

## Security notes

- Passwords are stored as Werkzeug password hashes, not as plain text.
- File extensions are checked against an allowlist, file names are sanitized, and stored names are randomized.
- The application enforces login checks and verifies document access on the download route.
- Sharing and revocation routes check that the requesting user owns the document.
- Uploads are limited to 10 MB.
- Keep `SECRET_KEY` in the hosting provider's environment settings; never publish it in source code or screenshots.
- Use HTTPS in deployment and restrict access to the hosting account and its environment variables.
- This project is an educational prototype. Do not upload confidential or sensitive real-world documents until the remaining security and deployment limitations have been addressed.

## Current implementation status

The following distinction keeps the project documentation accurate:

| Problem-statement requirement | Current status in this repository |
|---|---|
| User registration and login | Implemented |
| Password hashing | Implemented |
| Document upload and download | Implemented |
| Per-document read/edit permission records | Implemented |
| Owner-controlled sharing and revocation | Implemented |
| Download authorization checks | Implemented |
| Audit entries, including denied downloads | Implemented using SQLite audit records |
| Separate Admin, Owner, and Viewer role workflows | Not yet implemented; registration currently assigns the `user` role |
| Search by document name, owner, category, or date | Not yet implemented |
| Editing document contents through the application | Not yet implemented; edit permission can be assigned, but there is no document-editing route/UI |
| Admin-wide activity dashboard | Not yet implemented; the audit page currently shows the signed-in user's own events |
| HMAC-SHA256 tamper-evident audit chain | Not yet implemented; current audit records are ordinary SQLite rows |
| Complete automated security test coverage | Verify the tests in the `tests/` directory and the latest GitHub Actions run |

The status table describes the code currently in the repository; it does not claim that unimplemented requirements are complete.
