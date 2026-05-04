# Runbook: Payments dependency and checkout

**Id:** `payments-dependency`  
**Scope:** `checkout-api`, `payments-gw`, payment provider timeouts

## Symptoms

- Elevated error rate on `checkout-api` with `payment.ProviderTimeout` or similar.
- Log lines show `latency_ms` above gateway SLA (often 30000 ms or configurable ceiling).
- Correlation ids may repeat across retries (`retry=2/3` patterns).

## Immediate checks

1. Confirm **payments-gw** health dashboards and error budget for the current window.
2. Compare **p95/p99 latency** for payments-gw vs documented SLO.
3. List **recent deploys** to checkout-api and payments-gw in the incident region.
4. Verify upstream provider status if integrated (vendor page / API).

## Escalation

Escalate on-call if payments-gw error budget is exhausted or provider outage is confirmed.
