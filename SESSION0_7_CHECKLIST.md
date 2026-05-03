# Sessions 0 + 7 — checklist (Docker yes · NeMo local first · cloud fallback)

**Your choices:** Docker installed · try **NeMo locally** (Docker or laptop GPU); if VRAM/time fails, continue **NeMo on cloud GPU** · **NIM** for OpenAI-compatible serving.

**Hardware reality (RTX 3070 laptop ~8 GB VRAM, 16 GB RAM):** NeMo “full” training often needs **more VRAM** — treat local as **orientation + tiny runs**; use **cloud** for serious fine-tunes.

**EC2 + Amazon Linux 2023 (NIM on instance):** use the short checklist **[docs/SESSION0_EC2_AL2023.md](docs/SESSION0_EC2_AL2023.md)** (`requirements-ec2-inference.txt`, `SESSION0_EC2=1 python scripts/check_env.py`).

---

## A. Session 0 — environment (do in order)

1. [ ] **Python 3.10–3.12** venv + `pip install -r requirements-session0.txt` + PyTorch CUDA ([PyTorch Get Started](https://pytorch.org/get-started/locally/)).
2. [ ] Run `python scripts/check_env.py` → CUDA + imports OK.
3. [ ] **Docker Desktop** running (WSL2 backend if prompted): [Docker Desktop](https://www.docker.com/products/docker-desktop/).
4. [ ] **NGC account + API key** (needed for many official NVIDIA images): [NGC](https://ngc.nvidia.com/).
5. [ ] `docker login nvcr.io` with NGC credentials (see [NGC container registry login](https://docs.nvidia.com/ngc/ngc-private-registry-user-guide/index.html#login)).
6. [ ] Optional same day: **Ollama** for fast agent dev if NIM image won’t fit VRAM — [Ollama Windows](https://ollama.com/download).

---

## B. First NIM container (OpenAI-compatible LLM API)

Do this **after** NGC login and GPU passthrough in Docker.

1. [ ] Read prerequisites + env vars: [NIM LLMs — Quickstart](https://docs.nvidia.com/nim/large-language-models/latest/get-started/quickstart.html).
2. [ ] Optional broader context: [Deploying generative AI with NVIDIA NIM (blog)](https://developer.nvidia.com/blog/a-simple-guide-to-deploying-generative-ai-with-nvidia-nim/).
3. [ ] Pull/run the image from the doc for **one** small LLM NIM; mount cache dir as documented (`LOCAL_NIM_CACHE`).
4. [ ] Verify the API (adjust host/port): **Linux/bash:** `curl -s http://localhost:8000/v1/models` — **Windows PowerShell:** `curl.exe -s http://localhost:8000/v1/models` or `Invoke-RestMethod http://localhost:8000/v1/models` (see [docs/SESSION0_LLM_WINDOWS.md](docs/SESSION0_LLM_WINDOWS.md)).
5. [ ] Point your app at `http://localhost:<port>/v1` (same pattern as `.env.example` in this repo).

**If local NIM OOMs or won’t start:** use **Ollama** on the laptop for Sessions 1–5, run **NIM on a cloud GPU** when you have access — agent code stays OpenAI-compatible.

---

## C. NeMo — “first notebook” + local-first, cloud fallback

**LLM / log-copilot focus:** the “NeMo Framework” user guide **latest** overview is **Speech-heavy**; for **LLMs**, follow **NeMo Framework (LLM/VLM)** from [NeMo documentation hub](https://docs.nvidia.com/nemo/) and [Megatron-Bridge docs](https://docs.nvidia.com/nemo/megatron-bridge/latest/index.html) (used with newer NeMo containers).

### Read / run (ordered)

1. [ ] **Pick your track:** [NeMo documentation hub](https://docs.nvidia.com/nemo/) → **Framework** for LLM/VLM vs Speech sections.
2. [ ] **Megatron-Bridge (modern LLM stack):** [Megatron-Bridge documentation](https://docs.nvidia.com/nemo/megatron-bridge/latest/index.html) — aligns with NeMo container releases **26.02+** per NVIDIA docs.
3. [ ] **First tutorial notebook (classic GitHub entry):** [00_NeMo_Primer.ipynb](https://github.com/NVIDIA/NeMo/blob/main/tutorials/00_NeMo_Primer.ipynb) (clone repo + Jupyter, or Colab if notebook supports it).
4. [ ] **Repo / issues:** [NVIDIA NeMo on GitHub](https://github.com/NVIDIA/NeMo) (note: upstream org may show as `NVIDIA-NeMo` for framework repos).
5. [ ] **Speech only if you need ASR/TTS:** [NeMo speech tutorials](https://docs.nvidia.com/nemo/speech/latest/starthere/tutorials.html).

### Local NeMo (pick what fits your machine)

1. [ ] **Docker path (recommended for reproducible try):** use the **current** `nvcr.io` NeMo / Megatron-Bridge image tag from official docs for **your** release (tags change; copy from docs, not old blog posts).
2. [ ] **Pip path (lighter, selective):** `nemo-toolkit` with extras matching your domain — follow install instructions linked from [NeMo docs hub](https://docs.nvidia.com/nemo/).

**Stop conditions for “local didn’t work”**

- [ ] OOM or CUDA errors on first real training cell → **stop local training**; switch to **cloud GPU** (paperspace, Lambda, Azure GPU VM, etc.) with same notebook/repo.
- [ ] Install conflicts on Windows → use **NeMo in Linux**: WSL2 Ubuntu or cloud Linux box (recommended for NeMo long-term).

---

## D. Session 7 — benchmark & decision doc (merge with Session 0 success)

1. [ ] Same **5 golden incidents** (you’ll add in Session 5): run against **Ollama / NIM / API**.
2. [ ] Measure: latency, JSON schema valid %, “good enough” manual pass rate.
3. [ ] Write **half-page** `docs/model_strategy.md` (or notebook markdown):

   - **Inference:** NIM vs Ollama vs hosted API — when to use which.
   - **NeMo:** local = smoke tests; **cloud** = fine-tune / serious recipes.

---

## Link summary (bookmark order)

| Order | What |
|-------|------|
| 1 | [PyTorch Get Started](https://pytorch.org/get-started/locally/) |
| 2 | [NIM LLMs Quickstart](https://docs.nvidia.com/nim/large-language-models/latest/get-started/quickstart.html) |
| 3 | [NeMo documentation hub](https://docs.nvidia.com/nemo/) |
| 4 | [Megatron-Bridge docs](https://docs.nvidia.com/nemo/megatron-bridge/latest/index.html) |
| 5 | [NeMo Primer notebook](https://github.com/NVIDIA/NeMo/blob/main/tutorials/00_NeMo_Primer.ipynb) |
| 6 | [NeMo GitHub](https://github.com/NVIDIA/NeMo) |

*(If a “latest” URL fails, use the version picker on docs.nvidia.com and pick the newest stable release.)*
