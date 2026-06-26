# Runbook: Search latency high

## Symptoms
`search` `p99_latency_ms` climbing while `error_rate` stays low — slow, not failing.

## First checks
1. Look at `p99_latency_ms` for `search`.
2. Search logs for "slow query" warnings — a missing or degraded index is common.
3. Note: a low error_rate means this is a performance issue, not an outage.

## Remediation
- Reindex or add the missing index (safe, but coordinate timing).
- Add a read replica / more capacity if load-driven.
- No destructive auto-actions; rolling restarts need approval.
