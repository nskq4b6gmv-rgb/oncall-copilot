# Runbook: Severity & escalation guide

## Severity levels
- SEV1 (P1): customer-facing outage affecting all or most users (e.g. checkout down for everyone). Page the on-call lead immediately and open an incident channel.
- SEV2 (P2): significant degradation affecting some users or a single critical service.
- SEV3 (P3): minor or internal-only impact.

## Escalation
- SEV1: page the on-call lead and incident manager now; post status updates every 15 minutes.
- SEV2: notify the service owner; escalate to SEV1 if impact grows.

## Rule
When in doubt, escalate up, not down. Any full customer-facing outage is at least SEV1.
