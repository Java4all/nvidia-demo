# Golden incidents + benchmark workflow (Session 5 / 7)

## What is in the repo

| Artifact | Role |
|----------|------|
| `samples/incident_01.json` … `incident_05.json` | **Five golden** synthetic incidents (checkout/payments, DB, auth, search, queue). |
| `data/eval_cases.jsonl` | One line per case: `id`, `incident_path`, optional `expect` (see `src/eval_harness.py`). |
| `scripts/run_eval.py` | Pass/fail per case (Session 5). |
| `scripts/benchmark_session7.py` | Same cases + **latency** + **schema_valid** + JSON report (NIM, Session 7). |

Lines in `eval_cases.jsonl` may start with `#` (comments); blank lines are ignored.

## Editing expectations

After you **change the model** (new NIM image, new `OPENAI_MODEL`, or a **NeMo fine-tune** served behind NIM), triage wording may shift.

- If **`summary_contains`** fails often, relax or remove it for that case, or add alternate substrings.
- Keep **`min_next_steps`** / **`min_likely_causes`** as a cheap quality bar without forcing exact wording.
- **`golden_01_checkout_payments`** keeps **`summary_contains": ["checkout"]`** as a slightly stricter check on the original scenario.

## After you deploy a new checkpoint to NIM

1. Update **`.env`** (or the instance env): `OPENAI_BASE_URL`, **`OPENAI_MODEL`** (id from `GET /v1/models`), API key if needed.
2. Smoke one incident:  
   `python scripts/run_session3.py --incident samples/incident_01.json`
3. Run the **benchmark** (records latency + validity):  
   `python scripts/benchmark_session7.py --cases data/eval_cases.jsonl --out data/session7_nim_report.json`
4. Compare **`session7_nim_report.json`** to a saved baseline (rename by date or git-track summaries only).
5. Optionally run Session 5 eval for pass/fail only:  
   `python scripts/run_eval.py --cases data/eval_cases.jsonl --out eval_report.json`

## Adding a sixth golden incident

1. Add `samples/incident_06.json` (same top-level shape as `incident_01`).
2. Append one JSON line to `data/eval_cases.jsonl` (no trailing commas; one object per line).
3. Re-run `benchmark_session7.py`.
