# TrustVault

TrustVault is a web application for safely uploading and sharing documents. Users can create an account, upload files, and share documents with other registered users.

- **Live Demo:** https://trustvault-zkiw.onrender.com
- **GitHub Repository:** https://github.com/palavallisuma/TrustVault

## Features

- Create an account and log in.
- Upload and download documents.
- Keep your uploaded documents private.
- Share documents with read or edit permission.
- Revoke access to a shared document.
- Check your own activity history.
- Accept PDF, TXT, DOC, DOCX, PNG, JPG, and JPEG files.
- Maximum file size: 10 MB.

## Problem Statement

When documents are shared, people who should not have access may view or download them. TrustVault aims to solve this problem by allowing document owners to control who can access their files.

The project aims to:
- Keep each user's documents private.
- Allow owners to share and revoke access.
- Give users read or edit permissions.
- Block users who do not have permission.
- Record important activities.
- Test that users cannot access other users' private documents.

## Project Structure

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

## Run Locally

Follow these steps to run TrustVault on your computer.

**1. Install Python 3.10 or later.**

**2. Download the project:**

```bash
git clone https://github.com/palavallisuma/TrustVault.git
cd TrustVault
```

**3. Create a virtual environment:**

```bash
python -m venv venv
```

Activate it:

Windows:
```bash
venv\\Scripts\\activate
```

Linux / macOS:
```bash
source venv/bin/activate
```

**4. Install the required packages:**

```bash
pip install -r requirements.txt
```

**5. Set a secret key.** Keep this value private.

Windows PowerShell:
```powershell
$env:SECRET_KEY = "your-long-random-secret"
```

Linux / macOS:
```bash
export SECRET_KEY="your-long-random-secret"
```

**6. Start the application:**

```bash
python app.py
```

Open http://127.0.0.1:5000 in your browser. Create an account and log in.

## Run Automated Tests

Run these commands from the project folder:

```bash
pip install pytest
pytest
```

GitHub Actions is also set up to run code checks and tests when changes are pushed to GitHub or a pull request is created. Check the **Actions** tab in the repository to see the actual result.

## Deploy on Render

TrustVault is deployed using Render.

To deploy your own copy:

1. Sign in at [Render](https://render.com/).
2. Choose **New** and create a **Web Service** or use the Blueprint option.
3. Connect your GitHub account.
4. Select the `TrustVault` repository.
5. Set the build command to `pip install -r requirements.txt`.
6. Set the start command to `gunicorn app:app`.
7. Add a private environment variable named `SECRET_KEY`.
8. Deploy the application.

**Open the live application:** https://trustvault-zkiw.onrender.com

**Note:** The current app saves uploaded files and its SQLite database on local storage. Depending on the Render service plan, this data may be lost after a restart or redeployment. Persistent storage is needed before using it for important documents.

## Security Notes

- Passwords are stored as password hashes.
- Only allowed file types can be uploaded.
- File names are checked before saving.
- Users must log in to access protected pages.
- The app checks permission before allowing a document download.
- Only the document owner can share or revoke access.
- Keep your secret key private.
- This is an educational project. Do not upload confidential documents.

## Current Project Status

Some problem-statement requirements are not yet available in the current application:

- Separate Admin, Owner, and Viewer roles.
- Search documents by name, owner, category, or date.
- Editing document contents inside the application.
- An admin page to view all users' activity.
- A tamper-evident HMAC audit log.
- Full automated security test coverage.

The current audit history is stored in the SQLite database. These features should not be considered completed until they are added and tested.
