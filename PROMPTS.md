# AI prompt and review log

Updated: 2026-11-08. These entries describe the work performed during this security-focused update. They do not claim every generated suggestion was accepted without review.

## 2026-11-08 — Entry 1: Server-side authorization and roles

- **Prompt / request:** Review TrustVault against the challenge and complete Admin, Owner and Viewer authorization.
- **What the tool produced:** Role-aware route decorators, owner-only sharing, viewer read-only enforcement and admin-only routes.
- **What was wrong:** The first pass needed a migration for existing accounts using the old generic user role. Without it, existing accounts would not match the new owner/viewer checks.
- **What I did instead:** Added an additive migration mapping old user accounts to owner and added role/authorization tests.
- **Code commit:** https://github.com/palavallisuma/TrustVault/commit/c07513c8c4c00aa6203790a1fbf6a6441f5dc483
- **Migration commit:** https://github.com/palavallisuma/TrustVault/commit/6bd7eb46909e5e7f795e11c9104d9ca5d035046a

## 2026-11-08 — Entry 2: Direct-object access and revocation

- **Prompt / request:** Check whether a user can download another user's file by changing the document ID, and make revocation effective immediately.
- **What the tool produced:** A centralized access check used by the download route, plus tests for shared and unshared users.
- **What was wrong:** A permission check in the page/UI alone would not protect a direct route. The route must query the current grant on every download.
- **What I did instead:** Kept authorization inside the download handler and added tests for allowed and denied users. Owners alone manage grants.
- **Code commit:** https://github.com/palavallisuma/TrustVault/commit/c07513c8c4c00aa6203790a1fbf6a6441f5dc483
- **Test commit:** https://github.com/palavallisuma/TrustVault/commit/0c5984c2cc8a0e01a92678935d6b36019c3272d8

## 2026-11-08 — Entry 3: Audit trail integrity

- **Prompt / request:** Add evidence that audit records have not been silently edited.
- **What the tool produced:** HMAC-SHA256 entries linked to the previous entry, with an integrity verifier.
- **What was wrong:** Updating an earlier audit row to clear its document foreign key would invalidate its hash. Old pre-upgrade rows also cannot be authenticated retroactively.
- **What I did instead:** Kept audit entries immutable during deletion by soft-deleting the document row, retaining its audit foreign key, removing its grants and deleting its stored file. The verifier starts a new chain after legacy unhashed rows and the README explains this limitation.
- **Code commit:** https://github.com/palavallisuma/TrustVault/commit/d608c74bcdfdadea7745ab9f0e2061d88c751e64

## 2026-11-08 — Entry 4: Automated security tests

- **Prompt / request:** Expand tests beyond the happy path to cover roles, access denial, search, audit and deletion.
- **What the tool produced:** Tests for unauthorized downloads, viewer read-only behavior, non-owner share/revoke denial, admin user creation and retained deletion evidence.
- **What was wrong:** Some tests initially accessed Flask's request-scoped database connection without an application context, which would fail before testing the intended behavior.
- **What I did instead:** Wrapped direct test database setup/assertions in an application context and updated logout tests for the POST-only route.
- **Test commit:** https://github.com/palavallisuma/TrustVault/commit/6e71c53493321818fbf946f09a80b79e692d109f

## 2026-11-08 — Entry 5: Deployment and honest limitations

- **Prompt / request:** Make the README accurately explain how to deploy and hand over the three roles.
- **What the tool produced:** Role setup, environment variables, run/test commands, route documentation and explicit limitations.
- **What was wrong:** Publishing real demo passwords or claiming ephemeral Render storage was durable would be unsafe and misleading.
- **What I did instead:** Documented how to provision admin credentials privately, create owner/viewer accounts, and configure persistent storage. No production passwords or secrets are committed.
- **Documentation commit:** https://github.com/palavallisuma/TrustVault/commit/3f1faf432e248a4d8d8efb3ab83ff97a250303c1
