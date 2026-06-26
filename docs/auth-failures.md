# Runbook: Auth login failures

## Symptoms
Users cannot log in; `auth` `error_rate` rising; logs show token/signature errors.

## First checks
1. Look at the `auth` `error_rate` metric. A sharp rise is an incident.
2. Check `recent_deploys` for `auth` — a signing-key or token change after a deploy is a common cause.
3. Search logs for "token" or "signature" errors.

## Remediation
- If a recent deploy correlates (e.g. signature mismatch after a release), roll back.
  Rollback requires human approval — do not auto-execute.
- If keys rotated incorrectly, restore the previous signing key with security approval.
