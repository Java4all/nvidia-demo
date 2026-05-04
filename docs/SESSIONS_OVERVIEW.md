# Sessions overview (log triage copilot track)

Work through these in order in **`nvidia-demo`**. Session **0** must be green before coding Session **1**.

| Session | Focus | Repo / artifacts |
|--------|--------|-------------------|
| **0** | Python, PyTorch+CUDA, deps, `check_env.py`, optional **Ollama** or **NIM** on Windows | [README](../README.md), [SESSION0_LLM_WINDOWS.md](SESSION0_LLM_WINDOWS.md), [SESSION0_7_CHECKLIST.md](../SESSION0_7_CHECKLIST.md) |
| **1** | One agent + tools + **strict JSON** triage schema from `samples/incident_01.json` | `src/`, `scripts/run_session1.py` |
| **2** | Prompts, redaction, JSON repair pass | `src/prompts/session2_system.txt`, `src/redaction.py`, `src/json_repair.py`, `scripts/run_session2.py` |
| **3** | **RAG** over runbooks (`data/docs`) | |
| **4** | CLI: `--alert` / `--logs` → `--out` JSON | |
| **5** | **eval** harness (`eval_cases.jsonl`) | |
| **6** | Optional multi-agent | |
| **7** | Benchmark Ollama vs NIM vs API; **NeMo** strategy (local smoke vs cloud train) | `docs/model_strategy.md` |

Ask to implement **Session N** in chat when you are ready; we keep changes scoped to that session.
