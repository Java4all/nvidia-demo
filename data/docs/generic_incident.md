# Runbook: Generic incident triage

**Id:** `generic-incident`  
**Scope:** Any service when no specialized playbook matches.

## Steps

1. Capture **scope**: environment, region, service name from alerting context.
2. Pull **recent logs** around alert fire time; note ERROR vs WARN density.
3. Compare against **recent changes**: deploys, config flags, dependency versions.
4. Open a **tracking ticket** with timeline and hypotheses.

## References format

When citing internal docs, include document title and one-line excerpt in triage output.
