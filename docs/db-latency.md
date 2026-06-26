# Runbook: High database latency

## Symptoms
`p99_latency_ms` rising across services that share the primary database.

## First checks
1. Look at `p99_latency_ms` for the affected service.
2. Check for long-running queries and connection-pool exhaustion.

## Remediation
- Scaling read replicas is the safe first step.
- Kill obviously runaway queries only with DBA approval.
- Never restart the production database without explicit human approval.
