"""
Session 0 — verify Python, PyTorch+CUDA, agent stack, optional local LLM endpoint.

Run from repo root:
  .venv\\Scripts\\python scripts\\check_env.py

Optional:
  set OLLAMA_BASE=http://127.0.0.1:11434
  set NIM_OPENAI_BASE=http://127.0.0.1:8000/v1
"""
from __future__ import annotations

import os
import sys


def ok(msg: str) -> None:
    print(f"[OK] {msg}")


def warn(msg: str) -> None:
    print(f"[!!] {msg}")


def fail(msg: str, exc: BaseException | None = None) -> None:
    print(f"[NO] {msg}")
    if exc is not None:
        print(f"     ({exc})")


def main() -> int:
    print(f"Python: {sys.version.split()[0]} ({sys.executable})")

    # PyTorch + CUDA
    try:
        import torch

        ok(f"torch {torch.__version__}")
        if torch.cuda.is_available():
            ok(f"CUDA device: {torch.cuda.get_device_name(0)}")
            props = torch.cuda.get_device_properties(0)
            print(f"     VRAM total: {props.total_memory // (1024**2)} MiB")
        else:
            warn("CUDA not available — PyTorch CPU build or no NVIDIA driver.")
    except ImportError as e:
        fail("PyTorch not installed. Install from https://pytorch.org/get-started/locally/", e)

    # Agent stack (Session 1+)
    for mod in ("pydantic", "langchain_core", "langgraph"):
        try:
            __import__(mod)
            ok(f"import {mod}")
        except ImportError as e:
            fail(f"missing {mod}; pip install -r requirements-session0.txt", e)

    # Optional: ping OpenAI-compatible endpoints (no API key required for Ollama models list)
    try:
        import httpx
    except ImportError:
        warn("httpx not installed — skipping endpoint checks.")
        return 0

    ollama = os.environ.get("OLLAMA_BASE", "http://127.0.0.1:11434").rstrip("/")
    try:
        r = httpx.get(f"{ollama}/api/tags", timeout=3.0)
        if r.status_code == 200:
            ok(f"Ollama reachable at {ollama}")
        else:
            warn(f"Ollama at {ollama} returned HTTP {r.status_code}")
    except Exception as e:
        warn(f"Ollama not reachable at {ollama} (optional for Session 0). {e}")

    nim = os.environ.get("NIM_OPENAI_BASE", "").strip()
    if nim:
        try:
            # Many OpenAI-compatible servers expose GET /models or similar
            base = nim.rstrip("/").replace("/v1", "")
            r = httpx.get(f"{base}/v1/models", timeout=3.0)
            if r.status_code == 200:
                ok(f"NIM-style OpenAI base responds: {nim}")
            else:
                warn(f"{nim} returned HTTP {r.status_code}")
        except Exception as e:
            warn(f"NIM base not reachable ({nim}): {e}")
    else:
        print('     Set NIM_OPENAI_BASE=http://host:port/v1 to test NIM (optional).')

    print("\nSession 0 env check done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
