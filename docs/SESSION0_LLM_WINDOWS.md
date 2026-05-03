# Session 0.4 — LLM endpoint on Windows 11 (Ollama or NIM)

NIM quickstarts often show **Linux/bash** (`curl`, `$NGC_API_KEY`, `/opt/...` paths). On **Windows** you do the same things with **PowerShell** and **Docker Desktop** (containers are still **Linux**; you do not need a separate Ubuntu install for this step, though WSL2 is what Docker uses under the hood).

---

## A) Ollama (simplest on Windows)

1. Install: [Ollama for Windows](https://ollama.com/download).
2. Open **PowerShell** (or `cmd`):

   ```powershell
   ollama pull llama3.2:3b
   ollama serve
   ```

   (Often `serve` is already running as a background app after install.)

3. Test the API (Windows includes `curl.exe`):

   ```powershell
   curl.exe -s http://127.0.0.1:11434/api/tags
   ```

4. For your **Python** code, use OpenAI-compatible base URL:

   - `http://127.0.0.1:11434/v1`

5. Optional: set env for `check_env.py` in the **same** PowerShell window:

   ```powershell
   $env:OLLAMA_BASE = "http://127.0.0.1:11434"
   python scripts\check_env.py
   ```

---

## B) NIM with Docker Desktop (Windows)

**Prerequisites**

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed, **WSL2** backend enabled if the installer asks.
- In Docker Desktop: **Settings → Resources → GPU** (or “Use WSL 2 based engine”): ensure your **NVIDIA** GPU is available to Linux containers (wording varies by version).
- [NGC](https://ngc.nvidia.com/) account and **API key** (many `nvcr.io` images need it).

**Log in to the registry (PowerShell)**

```powershell
docker login nvcr.io
# Username: $oauthtoken
# Password: <your NGC API key>
```

(Exact `Username` may be documented for NGC; if the doc says `$oauthtoken`, type it literally.)

**Translate Linux `docker run` examples**

From [NIM LLMs Quickstart](https://docs.nvidia.com/nim/large-language-models/latest/get-started/quickstart.html), replace:

| Linux/bash habit | Windows equivalent |
|------------------|-------------------|
| `$NGC_API_KEY` | `$env:NGC_API_KEY = "your-key"` before `docker run`, or `-e NGC_API_KEY=$env:NGC_API_KEY` in PowerShell |
| `$LOCAL_NIM_CACHE` | Pick a folder, e.g. `$cache = "$env:USERPROFILE\nim-cache"; New-Item -ItemType Directory -Force $cache` |
| `-v "$LOCAL_NIM_CACHE:/opt/nim/.cache"` | `-v "${env:USERPROFILE}\nim-cache:/opt/nim/.cache"` (Docker Desktop accepts this path style) |
| `--gpus all` | Same flag works in PowerShell with Docker Desktop + NVIDIA Container Toolkit path |

**Example pattern (placeholder — copy image/env from current NVIDIA doc)**

```powershell
$env:NGC_API_KEY = "<paste-from-ngc>"
$cache = "$env:USERPROFILE\nim-cache"
New-Item -ItemType Directory -Force -Path $cache | Out-Null

docker pull <IMAGE_FROM_NIM_DOC>

docker run --gpus all --rm -it `
  -e NGC_API_KEY=$env:NGC_API_KEY `
  -v "${cache}:/opt/nim/.cache" `
  -p 8000:8000 `
  <IMAGE_FROM_NIM_DOC>
```

Use **backtick** `` ` `` at line end for PowerShell line continuation (as shown). Adjust **port** and **image name** to match the official quickstart.

**Verify (PowerShell)**

```powershell
curl.exe -s http://localhost:8000/v1/models
```

Or:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/v1/models" -Method Get
```

**Point `check_env.py` at NIM**

```powershell
$env:NIM_OPENAI_BASE = "http://127.0.0.1:8000/v1"
python scripts\check_env.py
```

---

## C) If NIM fails on your GPU (e.g. 8 GB VRAM)

Use **Ollama** for Sessions 1–5 locally; run **NIM on a cloud GPU** later. Your agent code stays the same if the endpoint is **OpenAI-compatible**.

---

## D) When people say “use Ubuntu” for NeMo/NIM

- **NIM via Docker Desktop:** you are already running a **Linux container**; Windows hosts it.
- **NeMo training / heavy notebooks:** NVIDIA docs often assume **Linux**. Easiest paths on your PC: **WSL2 Ubuntu** with GPU pass-through, or a **Linux cloud GPU** machine—same as our Session 0 + 7 checklist.

---

## Quick reference — PowerShell vs bash env vars

| bash | PowerShell (session only) |
|------|---------------------------|
| `export FOO=bar` | `$env:FOO = "bar"` |
| `$FOO` | `$env:FOO` |

Permanent user env: Windows **Settings → System → About → Advanced system settings → Environment Variables** (usually unnecessary for learning).
