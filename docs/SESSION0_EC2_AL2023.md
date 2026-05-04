# Session 0 — EC2 + Amazon Linux 2023 (quick checklist)

Use this when **NIM + Session 1** run on **the same EC2 instance** (no Windows Docker Desktop).

---

## A. Instance + driver

1. [ ] Instance type with enough GPU VRAM for your NIM (e.g. **`g6e.xlarge`** = 1× L40S 48 GB).
2. [ ] **Amazon Linux 2023** (GPU / DLAMI recommended so **`nvidia-smi`** works immediately).
3. [ ] After boot: `nvidia-smi` shows GPU + driver.

If `nvidia-smi` fails, install the driver per [NVIDIA drivers for AL2023](https://docs.aws.amazon.com/linux/al2023/ug/nvidia-drivers.html) or use a **GPU AMI**, then **reboot**.

---

## B. Docker + NVIDIA Container Toolkit

1. [ ] `sudo dnf install -y docker && sudo systemctl enable --now docker`
2. [ ] `sudo usermod -aG docker ec2-user` → **log out and back in**
3. [ ] Add NVIDIA repo + install toolkit:

   ```bash
   curl -fsSL https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | \
     sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo
   sudo dnf install -y nvidia-container-toolkit
   sudo nvidia-ctk runtime configure --runtime=docker
   sudo systemctl restart docker
   ```

4. [ ] Test: `docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubi8 nvidia-smi`

If you see **`libnvidia-ml.so.1`**: the **host driver** is missing or broken — fix **A** before **B**.

---

## C. NGC + NIM

1. [ ] `echo "$NGC_API_KEY" | docker login nvcr.io --username '$oauthtoken' --password-stdin`
2. [ ] Run your NIM `docker run ...` (cache volume, `-p 8000:8000`, etc.)
3. [ ] On the instance: `curl -s http://127.0.0.1:8000/v1/models`

### C.0 Which port is NIM on? (e.g. g6.xlarge)

**Default in NVIDIA quickstarts:** map **host `8000` → container `8000`** (`-p 8000:8000`). Your **OpenAI base URL** is then `http://127.0.0.1:8000/v1` when running Python **on the same EC2 host**.

**If you are not sure what you used:**

```bash
# Running container and published ports (look at PORTS, e.g. 0.0.0.0:8000->8000/tcp)
docker ps

# List listening TCP ports (find 8000 or another port bound by docker-proxy)
sudo ss -tlnp
```

Then test the API (replace `8000` if your `docker ps` shows another host port):

```bash
curl -s http://127.0.0.1:8000/v1/models
```

**From your laptop** (NIM only on the instance): either open the EC2 **security group** for that **TCP port** to your IP, or use an **SSH tunnel** and keep using `127.0.0.1` in `.env` on the laptop (see **README** SSH example: `-L 8000:127.0.0.1:8000`).

**LLM image used in this track (Llama 3.1 8B Instruct NIM):** `nvcr.io/nim/meta/llama-3.1-8b-instruct:2.0.3` — use **`OPENAI_MODEL`** = the `id` returned by `/v1/models` for this container (often `meta/llama-3.1-8b-instruct` or similar). Pair **§ C.1** with `--tool-call-parser llama3_json` for this family.

### C.1 vLLM: `--enable-auto-tool-choice` and `--tool-call-parser` (NIM)

vLLM only accepts OpenAI **`tool_choice: auto`** if the server is started with **both** flags. NIM passes extra vLLM args through **`NIM_PASSTHROUGH_ARGS`** (see [NIM advanced configuration](https://docs.nvidia.com/nim/large-language-models/latest/reference/advanced-configuration.html) and [tool calling](https://docs.nvidia.com/nim/large-language-models/latest/advanced-use-cases/tool-calling-and-mcp.html)).

Add to your **`docker run`** (alongside cache, port, GPU, `NIM_MAX_MODEL_LEN`, etc.):

```bash
-e NIM_PASSTHROUGH_ARGS="--enable-auto-tool-choice --tool-call-parser llama3_json"
```

Pick **`--tool-call-parser`** to match the **model family** (must align with vLLM — see [vLLM tool calling](https://docs.vllm.ai/en/latest/features/tool_calling.html)). Examples:

| Model family (typical NIM) | Parser (example) |
|----------------------------|------------------|
| Llama 3.1 / 3.3 Instruct | `llama3_json` |
| Mistral / Mixtral-style | `mistral` |
| Many “GPT-OSS”–style | `openai` |

If the parser is wrong, you get malformed tool calls or errors — switch parser to match your image’s model card.

**Optional VRAM cap** (same `docker run`): e.g. `-e NIM_MAX_MODEL_LEN=24832` if you saw memory warnings.

---

## D. Python 3.12 on Amazon Linux 2023

AL2023 keeps **`/usr/bin/python3`** on **Python 3.9** for OS tools (`dnf`, `cloud-init`, etc.). **Do not** replace that symlink. Install **3.12** alongside and call it explicitly.

### Install

```bash
sudo dnf install -y python3.12 python3.12-pip
```

Optional (only if you build C extensions / some wheels):

```bash
sudo dnf install -y python3.12-devel gcc
```

### Use 3.12

```bash
python3.12 --version
python3.12 -m pip --version
```

Install packages with:

```bash
python3.12 -m pip install ...
# or, if the shim exists:
pip3.12 install ...
```

### venv (recommended for this repo)

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
```

After `activate`, `python` and `pip` inside `.venv` are 3.12.

**Official doc:** [Python in AL2023](https://docs.aws.amazon.com/linux/al2023/ug/python.html) (multiple versions, `python3.12`, and why system `python3` stays 3.9).

---

## E. Python venv for **this repo** (inference only — no PyTorch)

From the cloned `nvidia-demo` root (after **D**):

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements-ec2-inference.txt
```

Or: `bash scripts/setup_ec2_venv.sh` (set `PYTHON=python3.12` if your default `python3` is not 3.12).

1. [ ] `export SESSION0_EC2=1` then `python scripts/check_env.py` (skips PyTorch; checks agent libs + optional NIM URL).

---

## F. Session 1 on EC2

1. [ ] Copy `.env.example` → `.env` with `OPENAI_BASE_URL=http://127.0.0.1:8000/v1` (same host as NIM) and **`OPENAI_MODEL`** from `/v1/models`.
2. [ ] `source .venv/bin/activate && python scripts/run_session1.py`

If the agent fails with **`"auto" tool choice requires --enable-auto-tool-choice and --tool-call-parser`**, either:

- **Server (fix at the LLM):** set **`NIM_PASSTHROUGH_ARGS`** as in **§ C.1** and restart the container.
- **Client (default in this repo):** Session 1 strips `tool_choice` in two places: a `ChatOpenAI` hook on the LangChain payload, and a **one-time patch of the OpenAI Python SDK** (`chat.completions.create` / async `create`) so requests still work if LangChain bypasses that hook. Pull the latest `src/session1.py`. If something sets `OPENAI_STRIP_TOOL_CHOICE=0`, try **`SESSION1_FORCE_STRIP_TOOL_CHOICE=1`**. For OpenAI cloud, set **`OPENAI_STRIP_TOOL_CHOICE=0`** so `tool_choice` is sent. The SDK patch affects **all** chat completion calls in the same Python process after Session 1 builds an LLM.

If you see **400** *`This model only supports single tool-calls at once`*, the OpenAI client was asking for **parallel** tool calls (LangChain’s default). Session 1 sets **`parallel_tool_calls: false`** by default; use **`SESSION1_PARALLEL_TOOL_CALLS=1`** only if you use a server that supports batched tool calls (e.g. OpenAI) and want that behavior.

**Security group:** only open **8000** to your IP if you must hit NIM from outside; for **localhost-only**, default SG is fine.

---

## G. Add NeMo (training) on the same instance (optional)

Keep **`nvidia-demo`** for inference + benchmarks. Use a separate clone **`nvidia-nemo`** for **NeMo in Docker** (Jupyter on **8888**; NIM stays on **8000**). On a **single-GPU** instance, **stop NIM** while running heavy NeMo training, then start NIM again.

See **`nvidia-nemo/docs/EC2_WITH_NIM.md`** in your **`nvidia-nemo`** clone (NeMo Jupyter **8888**, NIM **8000**, GPU sharing notes).

---

## Link to Windows laptop path

[SESSION0_LLM_WINDOWS.md](SESSION0_LLM_WINDOWS.md) — PowerShell + Docker Desktop when developing on Windows.
