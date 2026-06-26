# Runbook: Payments timeouts

## Symptoms
`checkout` failing because `payments` calls time out.

## First checks
1. Look at `payments` `error_rate` and `p99_latency_ms`.
2. If payments metrics look healthy (low error rate, stable latency), the problem is upstream in `checkout`, not payments.

## Remediation
- If payments is degraded, check its recent deploys and dependencies.
- If payments is healthy, return to the checkout runbook.
