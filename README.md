# TrustVault

TrustVault is a Flask web application for securely uploading, managing, downloading, and sharing documents with other registered users.

## Features

* **User registration and login** with hashed passwords
* **Upload PDF, TXT, DOC, DOCX, PNG, JPG, and JPEG files** (10 MB maximum)
* **Private document ownership**
* **Share documents** with read or edit permissions
* **Download access checks** to prevent unauthorized access
* **Cryptographic audit log trail** backed by HMAC-SHA256 hash chaining
* **Per-user audit history** and admin audit viewer
* **SQLite database** integration

## Project structure

```text
trustvault/
├── app.py
├── database.py
├── requirements.txt
├── render.yaml
├── THREATS.md
├── PROMPTS.md
├── audit.log
├── static/
│   └── style.css
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   └── audit.html
└── tests/
    ├── __init__.py
    └── test_trustvault.py

Run locally
Install Python 3.10 or later.

Clone this repository:
Bash
git clone [https://github.com/palavallisuma/Trust-vault2.git]
Create and activate a virtual environment:

Linux/macOS:

Bash
python -m venv venv
source venv/bin/activate
Windows:

DOS
python -m venv venv
venv\Scripts\activate
Install required packages:

Bash
pip install -r requirements.txt
Initialize database and run the app:

Bash
python app.py
The app will run locally at http://127.0.0.1:5000.

Run automated tests:

Bash
pytest
Key Submission Files
THREATS.md: Outlines threat models, authorization rules, and access control edge cases.

PROMPTS.md: Logs prompt iterations, AI generation checks, and human verification steps.

audit.log: Generated real-time audit log secured by HMAC-SHA256 hash-chaining.
