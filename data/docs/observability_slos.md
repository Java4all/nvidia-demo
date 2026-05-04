# Observability and SLO hygiene

## Metrics that matter

- **Latency:** p50/p95/p99 vs gateway timeouts seen in logs (`latency_ms`).
- **Saturation:** CPU, connections, thread pools on API and gateway tiers.
- **Errors:** rate of 5xx vs dependency timeouts.

## Using logs with alerts

Cross-check alert `fired_at` with log line timestamps; allow clock skew of a few seconds.
