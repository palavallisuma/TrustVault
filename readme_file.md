# TrustVault

TrustVault is a Flask web application for securely uploading, managing, downloading, and sharing documents with other registered users.

## Features

* User registration and login with hashed passwords
* Upload PDF, TXT, DOC, DOCX, PNG, JPG, and JPEG files (10 MB maximum)
* Private document ownership
* Share documents with read or edit permissions
* Download access checks
* Per-user audit history
* HMAC-SHA256 hash-chain verification for audit integrity
* SQLite database

## Project structure

```text
trustvault/
├── app.py
├── database.py
├── requirements.txt
├── render.yaml
├── static/
│   └── style.css
└── templates/
    ├── index.html
    ├── login.html
    ├── dashboard.html
    └── audit.html
```

## Run locally

1. Install Python 3.10 or later.

2. Clone this repository:

```bash
git clone https://github.com/palavallisuma/Trust-vault2
cd trustvault
```

3. Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows:
```cmd
venv\Scripts\activate
```

Linux / macOS:
```bash
source venv/bin/activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Run the application:

```bash
python app.py
```

6. Run automated tests:

```bash
pytest
```