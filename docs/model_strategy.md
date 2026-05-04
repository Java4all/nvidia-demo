# Model strategy — NIM inference vs NeMo training (Session 7)

This doc ties together **how this repo runs today** and **where NeMo fits** if you invest in custom models for the log-triage copilot.

**Hands-on NeMo (tutorials + training experiments):** you do **not** need to lock a strategy first. Use **[NeMo_learning_lab.md](NeMo_learning_lab.md)** for Docker/Jupyter, the Primer notebook, and local artifact layout under **`training/experiments/`**.

---

## 1. What you run in production for this app

The agent stack talks to an **OpenAI-compatible HTTP API** (`OPENAI_BASE_URL`, `OPENAI_MODEL`). On GPU hosts that usually means **NVIDIA NIM** (vLLM-backed container from NGC), e.g. `nvcr.io/nim/meta/llama-3.1-8b-instruct:...`.

**Session 7 benchmark (NIM-only):** use `scripts/benchmark_session7.py` with `.env` pointing at NIM. It records **per-case latency**, whether **`TriageOutput`** was produced (**schema valid**), and whether **`eval_cases.jsonl`** expectations passed (**expect rules**). See `data/session7_nim_report.json` after a run.

---

## 2. NeMo is not a swap-in for NIM’s HTTP port

| Piece | Role in *this* scenario |
|--------|-------------------------|
| **NIM** | **Inference**: serves a model behind `/v1/chat/completions` for LangChain / your scripts. |
| **NeMo Framework** | **Training & tooling**: data prep, fine-tuning, evaluation pipelines, export to checkpoints. |

NeMo does **not** replace the **browser/agent → REST** path by itself. After training, you still **serve** the model (often via **NIM**, custom vLLM, or another inference stack) if you want the same OpenAI-style client code.

So: **NeMo answers “how do I improve the model?”** not “what replaces my NIM URL?”.

---

## 3. How you could use NeMo for this triage scenario

Realistic paths:

1. **Stay on a general instruct model (current approach)**  
   No NeMo required. Tune prompts, RAG runbooks, eval cases, and NIM flags (`NIM_MAX_MODEL_LEN`, `NIM_PASSTHROUGH_ARGS`, etc.).

2. **Fine-tune a smaller or domain model on triage-style data**  
   Use **NeMo** (often with **Megatron-Bridge** in current NVIDIA docs) to:
   - Curate **(incident JSON → ideal triage JSON)** pairs (or conversation traces).
   - Run a **supervised fine-tune** (or preference optimization later) in a **cloud GPU** if local VRAM is tight.
   - **Export** checkpoints and deploy via a stack NVIDIA documents for that model family — often **NGC / NIM** when a NIM profile exists, or self-hosted vLLM.

3. **Evaluate before/between training steps**  
   Use the same **`eval_cases.jsonl`** + **`benchmark_session7.py`** (against NIM serving **baseline vs fine-tuned** checkpoints if both expose OpenAI-compatible endpoints) to compare **latency**, **schema validity**, and **expect pass rate**.

---

## 4. Practical constraints

- **Local laptop**: good for **smoke** NeMo installs and tiny runs; serious fine-tunes usually need **cloud GPU**.
- **Compliance / air-gap**: training data with real logs may need **PII redaction** first (your Session **2** redaction helpers are the right direction).
- **Inference**: keep **one** stable OpenAI-compatible endpoint for the app; swap **`OPENAI_MODEL`** / URL when you change the served checkpoint.

---

## 5. After a NeMo checkpoint is deployed to NIM

1. Point **`.env`** at the NIM host and set **`OPENAI_MODEL`** to the new model id (`GET /v1/models`).
2. Run **`scripts/benchmark_session7.py`** against **`data/eval_cases.jsonl`** and save the report (e.g. `data/session7_nim_report.json`).
3. Compare **latency** (mean / p95), **`schema_valid_count`**, and **`expect_pass_count`** to your previous baseline.
4. If expectations fail only on wording, adjust **`expect`** in **`eval_cases.jsonl`** (see **[eval_golden_workflow.md](eval_golden_workflow.md)**).

---

## 6. Links (bookmark)

- [NeMo documentation hub](https://docs.nvidia.com/nemo/) — Framework (LLM) vs Speech sections.
- [Megatron-Bridge](https://docs.nvidia.com/nemo/megatron-bridge/latest/index.html) — modern LLM training stack aligned with recent NeMo releases.
- [NIM LLMs quickstart](https://docs.nvidia.com/nim/large-language-models/latest/get-started/quickstart.html) — inference containers you already use.
- [NeMo Primer notebook](https://github.com/NVIDIA/NeMo/blob/main/tutorials/00_NeMo_Primer.ipynb) — orientation.

*(URLs change; use the version picker on NVIDIA docs if a link moves.)*
