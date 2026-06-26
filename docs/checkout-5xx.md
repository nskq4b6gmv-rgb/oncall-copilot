# Runbook: Checkout service returning 5xx

## Symptoms
Elevated 5xx error rate on the `checkout` service; customers see "payment failed".

## First checks (in order)
1. Look at the `checkout` `error_rate` metric. Above 2% sustained is an incident.
2. Check `recent_deploys` for `checkout`. A bad deploy is the most common cause.
3. Search logs for "checkout" ERROR lines to find the stack trace.

## Remediation
- If a recent deploy correlates with the spike, roll back to the previous version.
  Rollback requires human approval — do not auto-execute.
- If no deploy correlates, check the `payments` dependency next.
