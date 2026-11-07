# TrustVault AI Development Prompt Log

This file records concise summaries of actual project requests made while developing and checking TrustVault. The wording below is summarized for readability; it is not presented as a verbatim transcript. Dates reflect the project work discussed in ChatGPT.

| Date | Prompt summary | Area |
|---|---|---|
| 2026-11-01 | Build the TrustVault secure document-sharing application using the technologies in the project brief, and prepare a clear README with a live demo link. | Project setup and documentation |
| 2026-11-06 | Fix the failing TrustVault GitHub Actions tests and make the final project include a real audit file. | Testing and audit logging |
| 2026-11-06 | Complete the remaining project tasks from the requirements and fix failures without introducing bugs. | Final requirements review |
| 2026-11-07 | Implement Admin, Owner and Viewer login roles, document dashboard, upload validation, permission grant/revoke and an audit trail. | Role-based authorization |
| 2026-11-07 | Check whether the audit trail shows who uploaded, viewed, downloaded or changed a document, and verify the final submission requirements. | Audit security and verification |

## Security-focused prompt notes

1. **Authorization prompt (2026-11-07):** Add Admin, Owner and Viewer roles, then check that document permissions control who can access and change a document. The implementation uses server-side permission checks; automated tests cover allowed and denied examples.
2. **Audit-integrity prompt (2026-11-06 to 2026-11-07):** Build a real audit record for document activity and check whether unauthorized changes to audit records can be detected. The implementation uses HMAC-SHA256 chained records and an integrity check in the Admin dashboard.

## How AI assistance was used

AI assistance was used to plan features, explain implementation steps, review code, troubleshoot test failures and draft project documentation. Code and documentation must still be reviewed and tested by the project developer. AI-generated suggestions are not proof of security or correctness.
