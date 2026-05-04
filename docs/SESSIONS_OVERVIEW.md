# Sessions overview (log triage copilot track)

Work through these in order in **`nvidia-demo`**. Session **0** must be green before coding Session **1**.

| Session | Focus | Repo / artifacts |
|--------|--------|-------------------|
| **0** | Python, PyTorch+CUDA, deps, `check_env.py`, optional **Ollama** or **NIM** on Windows | [README](../README.md), [SESSION0_LLM_WINDOWS.md](SESSION0_LLM_WINDOWS.md), [SESSION0_7_CHECKLIST.md](../SESSION0_7_CHECKLIST.md) |
| **1** | One agent + tools + **strict JSON** triage schema from `samples/incident_01.json` | `src/`, `scripts/run_session1.py` |
| **2** | Prompts, redaction, JSON repair pass | `src/prompts/session2_system.txt`, `src/redaction.py`, `src/json_repair.py`, `scripts/run_session2.py` |
| **3** | **RAG** over runbooks (`data/docs`) | `data/docs/`, `src/rag_runbooks.py`, `src/tools_rag.py`, `src/prompts/session3_system.txt`, `scripts/run_session3.py` |
| **4** | CLI: `--alert` / `--logs` → `--out` JSON | `src/cli_incident.py`, `scripts/run_session4.py` |
| **5** | **eval** harness (`eval_cases.jsonl`) | `data/eval_cases.jsonl`, `samples/incident_01.json`–`05`, `docs/eval_golden_workflow.md`, `src/eval_harness.py`, `src/triage_profile.py`, `scripts/run_eval.py` |
| **6** | Optional multi-agent | `src/prompts/session6_*.txt`, `src/session6.py`, `scripts/run_session6.py` |
| **7** | NIM benchmark (latency, schema, eval); **NeMo** learning + `docs/model_strategy.md` | `scripts/benchmark_session7.py`, `docs/model_strategy.md`, `docs/NeMo_learning_lab.md`, `training/` |

Ask to implement **Session N** in chat when you are ready; we keep changes scoped to that session.
