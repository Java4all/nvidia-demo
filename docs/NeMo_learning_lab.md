# NeMo learning lab — hands-on training (experience, not a strategy vote)

This guide is for **learning NVIDIA NeMo by running real tutorials and small training experiments**. It does **not** require you to pick a long-term “model strategy.” Use it alongside **`nvidia-demo`** NIM inference and **`benchmark_session7.py`** when you later compare checkpoints.

**Prerequisites**

- **NVIDIA GPU** with a recent driver (Linux bare-metal, **Linux cloud VM**, or **WSL2 + Docker Desktop** with GPU on Windows).
- **Docker** with GPU access (`docker run --gpus all` works).
- **NGC** account and API key: [NGC](https://ngc.nvidia.com/) → create key → `docker login nvcr.io` as in [NGC login](https://docs.nvidia.com/ngc/ngc-private-registry-user-guide/index.html#login).
- Enough **VRAM** for the tutorial you pick (8 GB = smoke only; **24 GB+** is more comfortable for small LLM runs).

---

## 1. Why NeMo vs this repo’s Python venv

| Location | Use |
|----------|-----|
| **`nvidia-demo` `.venv`** | Agent, NIM client, eval, benchmark — **inference** only. |
| **NeMo Docker image or NeMo conda env** | **Training** notebooks and recipes — separate from `requirements-session0.txt`. |

Keep NeMo installs **out of** the triage app venv unless you enjoy dependency conflicts; prefer **official NeMo containers** for reproducibility.

---

## 2. Track A — NeMo in Docker (recommended first touch)

Image names and tags change. Always copy the **current** tag from:

- [NeMo Framework — installation / containers](https://docs.nvidia.com/nemo/) (use the doc’s **version picker**).

Template (replace `IMAGE` with the tag from docs):

```bash
# Example shape only — verify IMAGE on NVIDIA docs
docker pull IMAGE

docker run --gpus all --rm -it \
  -p 8888:8888 \
  -v "$PWD:/workspace" \
  IMAGE \
  bash -lc "jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root"
```

Open the printed Jupyter URL, then:

1. Run **`00_NeMo_Primer.ipynb`** from the NeMo GitHub tutorials (clone the repo or open [NeMo Primer on GitHub](https://github.com/NVIDIA/NeMo/blob/main/tutorials/00_NeMo_Primer.ipynb) and copy cells into a notebook in `/workspace`).
2. Work through **one** additional notebook from the **LLM / Framework** section of the [NeMo documentation hub](https://docs.nvidia.com/nemo/) (pick “Getting started” or “Fine-tuning” for your GPU size).

**Goal:** finish at least the Primer + one LLM-oriented tutorial end-to-end so you’ve seen data loading, trainer-style loops, and checkpoints on disk.

---

## 3. Track B — pip / conda NeMo (optional)

If you prefer a local Python env:

- Follow the **install** section for **`nemo-toolkit`** on the [NeMo docs hub](https://docs.nvidia.com/nemo/) for your OS and CUDA version.
- Use a **dedicated conda env** (e.g. `conda create -n nemo python=3.10`) — do **not** install into `nvidia-demo/.venv`.

Use this track if Docker is awkward but you accept more install troubleshooting.

---

## 4. Megatron-Bridge (modern LLM stack)

For **current** LLM training docs aligned with recent releases, skim:

- [Megatron-Bridge documentation](https://docs.nvidia.com/nemo/megatron-bridge/latest/index.html)

You do not need to master it on day one; treat it as the **next** reading step after the Primer.

---

## 5. “Play” ideas that build experience (pick one)

| Exercise | What you learn |
|----------|----------------|
| Run **Primer** + save a checkpoint path | Where NeMo writes weights, how configs look. |
| Run a **small official fine-tuning** or **PEFT** example from NeMo recipes | Data format, loss curves, eval hooks. |
| Log **GPU memory** and **steps/sec** in a spreadsheet | Trade-offs for your hardware. |

Avoid starting from a huge multi-node recipe until single-GPU runs feel familiar.

---

## 6. Connecting experiments back to this repo (later)

When you have a checkpoint served as **OpenAI-compatible** inference:

1. Point **`.env`** at that endpoint / **`OPENAI_MODEL`**.
2. Run **`scripts/benchmark_session7.py`** and compare **`data/session7_nim_report.json`** to a baseline.

If you keep NeMo training in a **separate repo** (for example a sibling **`nvidia-nemo`** checkout), use that repo for checkpoints and Jupyter; use **`nvidia-demo`** only for the agent, **`eval_cases.jsonl`**, and **`benchmark_session7.py`** — see **`nvidia-nemo/README.md`** § “Triage demo and benchmarks” for the same loop in one place.

Training data that resembles incidents should be **redacted** (reuse ideas from **`src/redaction.py`**); do not commit secrets or raw production logs.

Optional local artifacts in this repo: use **`training/experiments/`** (see **`training/README.md`**); that directory is gitignored.

---

## 7. If something fails

| Symptom | What to try |
|---------|-------------|
| **OOM** | Smaller model, shorter sequence length, gradient checkpointing (per tutorial), or **cloud GPU**. |
| **CUDA / driver** | Match CUDA toolkit to driver; prefer **Linux** or cloud for NeMo long-term. |
| **Windows native** | Prefer **WSL2 + Docker GPU** or a **Linux** box for NeMo; fewer edge-case installs. |

---

## 8. Bookmark list (order)

1. [NeMo documentation hub](https://docs.nvidia.com/nemo/)
2. [NeMo Primer notebook](https://github.com/NVIDIA/NeMo/blob/main/tutorials/00_NeMo_Primer.ipynb)
3. [Megatron-Bridge](https://docs.nvidia.com/nemo/megatron-bridge/latest/index.html)
4. [NeMo GitHub](https://github.com/NVIDIA/NeMo) — tutorials and recipes source of truth

URLs move; use NVIDIA’s version picker when a link 404s.
