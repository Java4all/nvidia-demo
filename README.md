# nvidia-demo — learning track (log triage copilot)

This repo follows a **session-based plan**: orchestration + RAG + optional **NVIDIA NeMo** / **NIM**.

---

## Python version

Use **64-bit Python 3.10–3.12** for the smoothest **PyTorch** install. If you use **3.13+**, check [pytorch.org](https://pytorch.org/get-started/locally/) for support. If PyTorch has no wheel for your version, install **3.12** from [python.org](https://www.python.org/downloads/) and recreate `.venv`.

---

## Session 0 — Environment (goals)

| Step | Goal | Done when |
|------|------|-----------|
| **0.1** | Isolated Python env | `python -m venv .venv` works |
| **0.2** | PyTorch sees your GPU | `check_env.py` prints CUDA device name |
| **0.3** | Agent libraries installed | `import langgraph` succeeds |
| **0.4** | One LLM endpoint for later sessions | Ollama **or** NIM responds (optional same day) — **Windows:** [docs/SESSION0_LLM_WINDOWS.md](docs/SESSION0_LLM_WINDOWS.md) (NIM docs are often bash/Ubuntu; same ideas in PowerShell + Docker Desktop) |
| **0.5** | Sample incident file exists | `samples/incident_01.json` loads |

**Hardware reminder (RTX 3070 laptop + 16 GB RAM):** use **short contexts** and **small / quantized** models locally. Heavy **NeMo training** is for a **cloud GPU** later, not Session 0.

---

## Session 0 — Steps (Windows 11)

### 1) Open this folder

```powershell
cd C:\Users\elesvi\Downloads\nvidia-demo
```

### 2) Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
```

(Use **Python 3.12** if available. If you use the `py` launcher: `py -3.12 -m venv .venv`.)

### 3) Install PyTorch with CUDA (official installer)

Use the matrix at [PyTorch Get Started](https://pytorch.org/get-started/locally/). Example (change `cu124` to match the site and your driver):

```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

Check the driver: **NVIDIA App** or `nvidia-smi` in a terminal.

### 4) Install Session 0 dependencies

```powershell
pip install -r requirements-session0.txt
```

### 5) Run the environment check

```powershell
python scripts\check_env.py
```

Optional - Ollama:

```powershell
$env:OLLAMA_BASE = "http://127.0.0.1:11434"
python scripts\check_env.py
```

Optional - NIM OpenAI-compatible base:

```powershell
$env:NIM_OPENAI_BASE = "http://127.0.0.1:8000/v1"
python scripts\check_env.py
```

### 6) Session 0.4 — LLM endpoint (goal row **0.4**): Windows, not Ubuntu-only

Official NIM examples often use **bash** (`export`, `/home/...`). On **Windows 11** you use **PowerShell** + **Docker Desktop**: containers are still **Linux**, but you run `docker` from PowerShell and map cache folders with Windows paths.

**Step-by-step (Ollama + NIM + `curl.exe` + env vars):** **[docs/SESSION0_LLM_WINDOWS.md](docs/SESSION0_LLM_WINDOWS.md)**

Quick path:

1. **Ollama:** [download](https://ollama.com/download), then `ollama pull llama3.2:3b`, test with `curl.exe -s http://127.0.0.1:11434/api/tags`. App URL: `http://127.0.0.1:11434/v1` (see `.env.example`).
2. **NIM:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) + `docker login nvcr.io` + `docker run ...` from [NIM LLMs Quickstart](https://docs.nvidia.com/nim/large-language-models/latest/get-started/quickstart.html), translating env vars and `-v` paths like in the doc above.
3. If NIM **OOMs** on ~8 GB VRAM, use Ollama until you have a larger GPU; agent code unchanged.

Goal **0.4** is satisfied when step **6** works (optional same day as steps 1–5): run `check_env.py` with `OLLAMA_BASE` or `NIM_OPENAI_BASE` set and see the OK lines.

### 7) NeMo (Session 0 = read only)

- Skim [NVIDIA NeMo](https://github.com/NVIDIA/NeMo) README. Do **not** block Session 0 on a full `nemo-toolkit` install; plan **cloud GPU** for training recipes.

---

## Layout (after Session 0)

```text
nvidia-demo/
  README.md
  SESSION0_7_CHECKLIST.md
  docs/SESSION0_LLM_WINDOWS.md
  docs/SESSIONS_OVERVIEW.md
  requirements-session0.txt
  scripts/check_env.py
  scripts/run_session1.py
  src/
  samples/incident_01.json
  .env.example
```

---

## Session 1 — log triage agent (tools + JSON)

**Goal:** one **OpenAI-compatible** endpoint (your **EC2 NIM** via SSH tunnel, **Ollama**, or OpenAI) + **LangGraph** ReAct agent with **three stub tools** + **Pydantic** `TriageOutput`.

### Configure `.env` (repo root)

Set (see `.env.example`):

- `OPENAI_BASE_URL` — e.g. `http://127.0.0.1:8000/v1` when tunneling EC2 NIM to your laptop.
- `OPENAI_API_KEY` — often dummy (`not-used`) for NIM/Ollama.
- `OPENAI_MODEL` — **exact** model id from `GET …/v1/models` (NIM/Ollama names differ).

### Run

```powershell
cd C:\Users\elesvi\Downloads\nvidia-demo
.\.venv\Scripts\Activate.ps1
python scripts\run_session1.py
python scripts\run_session1.py --trace out\session1_trace.json
```

**SSH tunnel example (NIM on EC2):**

```bash
ssh -i key.pem -L 8000:127.0.0.1:8000 ec2-user@<dns>
```

Then `OPENAI_BASE_URL=http://127.0.0.1:8000/v1` on your PC.

### Code layout

- `src/schema.py` — `TriageOutput` contract  
- `src/tools_log.py` — `extract_timestamps_and_ids`, `classify_severity_keywords`, `stub_lookup_playbook`  
- `src/session1.py` — `create_react_agent` + JSON parse / repair via `src/json_repair.py`  

Full roadmap: **[docs/SESSIONS_OVERVIEW.md](docs/SESSIONS_OVERVIEW.md)**.

---

## Session 2 — redaction, prompts, repair (same agent)

**Goal:** pre-redact incident text before the LLM, use a **Session 2** system prompt (placeholder-aware + strict JSON), and keep the shared **JSON repair** path in `src/json_repair.py`.

### Run

```powershell
python scripts\run_session2.py
python scripts\run_session2.py --incident samples\incident_01.json --trace out\session2_trace.json
```

### Code layout

- `src/redaction.py` — `redact_incident()` for emails, JWT-like strings, AWS-style keys, `sk-…` keys, long hex, bearer/basic  
- `src/prompts/session2_system.txt` — system prompt for redacted inputs  
- `src/json_repair.py` — fence strip, first-`{` extract, trailing-comma relax, `repair_triage_json()`  

Session 1 still defaults to `session1_system.txt` and **no** redaction; Session 2 calls `run_triage(..., prompt_file="session2_system.txt", redact=True)`.

---

## Session 3 — RAG over runbooks (`data/docs`)

**Goal:** retrieve markdown runbook chunks for the alert and logs, then triage with the same `TriageOutput` JSON. Retrieval is **lexical** (chunk + term overlap) so it runs on an inference-only node without a separate embedding service.

### Run

```powershell
python scripts\run_session3.py
python scripts\run_session3.py --incident samples\incident_01.json --trace out\session3_trace.json
```

Add or edit files under **`data/docs/`** (e.g. `payments_dependency.md`). The agent tool **`lookup_runbook_rag`** searches these at runtime.

### Code layout

- `data/docs/*.md` — runbook source  
- `src/rag_runbooks.py` — `RunbookIndex` (chunk + score)  
- `src/tools_rag.py` — `TOOLS_SESSION3` (RAG tool + same log tools as before; **no** `stub_lookup_playbook`)  
- `src/prompts/session3_system.txt` — instructs use of RAG and runbook citations in `references`  

---

## Session 4 — CLI (`--alert` / `--logs` → `--out`)

**Goal:** build an incident from the shell, run triage (default **Session 3**: RAG + redaction), write **`TriageOutput`** JSON to **`--out`**.

### Examples

```powershell
python scripts\run_session4.py --alert "High error rate on checkout-api" `
  --logs samples\sample_logs.txt --out triage.json

python scripts\run_session4.py --alert-file my_alert.txt --logs samples\sample_logs.txt `
  --out triage.json --service checkout-api --region eu-west-1 --env prod --trace trace.json

# stdin logs (PowerShell)
Get-Content samples\sample_logs.txt | python scripts\run_session4.py --alert "Test" --logs - --out out.json
```

- **`--session {1,2,3}`** — tool/prompt profile (default **3**). Session **2** adds redaction prompt without RAG; Session **1** is baseline tools only.

### Code layout

- `src/cli_incident.py` — `build_incident(alert_title, log_text, …)`  
- `scripts/run_session4.py` — argparse entrypoint  

---

## Session 5 — eval harness (`eval_cases.jsonl`)

**Goal:** run many incidents + optional **expect** rules; report pass/fail (default profile: Session **3**).

### Run

```powershell
python scripts\run_eval.py --cases data\eval_cases.jsonl
python scripts\run_eval.py --cases data\eval_cases.jsonl --out eval_report.json --session 3
```

Each **JSONL** line is one JSON object: `id`, `incident` or `incident_path`, optional `expect`, optional `skip`. Expect rules are documented in **`src/eval_harness.py`** (`check_expectations`).

### Code layout

- `data/eval_cases.jsonl` — sample cases  
- `src/eval_harness.py` — load cases, resolve incidents, check expectations  
- `src/triage_profile.py` — `run_triage_for_session` (shared with Session 4 CLI)  
- `scripts/run_eval.py` — batch runner and JSON report  

---

## Session 6 — optional multi-agent (research + synthesis)

**Goal:** split work into two LLM phases—**(1)** ReAct + Session 3 tools/RAG with a **research summary**, **(2)** a separate **synthesis** call that outputs only **`TriageOutput`** JSON (no tools).

### Run

```powershell
python scripts\run_session6.py
python scripts\run_session6.py --incident samples\incident_01.json --trace session6_trace.json
```

Uses **`get_llm()`** from Session 1, redacts incidents like Session 2/3, and reuses **`parse_triage_json` / `repair_triage_json`** on the synthesis reply.

### Live LLM tests (optional)

From repo root, with **`.env`** pointing at your NIM (same as `run_session6.py`):

**PowerShell**

```powershell
$env:RUN_LIVE_LLM = "1"
python -m pytest tests/test_session6_live.py -v
```

**bash**

```bash
export RUN_LIVE_LLM=1
python -m pytest tests/test_session6_live.py -v
```

Without `RUN_LIVE_LLM`, that file’s tests are **skipped** so normal `pytest tests/` stays offline and fast. Expect **minutes** per test (two LLM phases + tools).

### Code layout

- `src/prompts/session6_research.txt` — phase 1 system prompt  
- `src/prompts/session6_synthesis.txt` — phase 2 schema instructions  
- `src/session6.py` — `run_multi_agent_triage`, `triage_session6_from_incident_path`  

---

## Troubleshooting

| Issue | What to try |
|--------|-------------|
| CUDA False | Match PyTorch CUDA wheel to driver; reinstall torch. |
| OOM | Smaller model, shorter logs, close other apps. |
| Docker GPU | Docker Desktop: enable GPU; WSL2 updated. |
