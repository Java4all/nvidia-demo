"""
Session 0 — verify Python, (optional) PyTorch+CUDA, agent stack, optional LLM endpoints.

Run from repo root:
  python scripts/check_env.py
  SESSION0_EC2=1 python scripts/check_env.py    # EC2 inference node: skip PyTorch
  python scripts/check_env.py --ec2             # same

Optional:
  OLLAMA_BASE=http://127.0.0.1:11434
  NIM_OPENAI_BASE=http://127.0.0.1:8000/v1
  OPENAI_BASE_URL=http://127.0.0.1:8000/v1   # also probed for /v1/models when set
"""
from __future__ import annotations

import argparse
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
    ap = argparse.ArgumentParser(description="Session 0 environment check")
    ap.add_argument(
        "--ec2",
        action="store_true",
        help="Inference-only EC2: skip PyTorch/CUDA checks (use with requirements-ec2-inference.txt)",
    )
    args = ap.parse_args()
    ec2 = args.ec2 or os.environ.get("SESSION0_EC2", "").strip() in ("1", "true", "yes")

    print(f"Python: {sys.version.split()[0]} ({sys.executable})")
    if ec2:
        print("Mode: EC2 inference (PyTorch check skipped)")

    # PyTorch + CUDA (optional on EC2 when only NIM + Session 1 run in Docker)
    if not ec2:
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
    else:
        warn("PyTorch check skipped (--ec2 / SESSION0_EC2=1).")

    # Agent stack (Session 1+)
    for mod in ("pydantic", "langchain_core", "langgraph"):
        try:
            __import__(mod)
            ok(f"import {mod}")
        except ImportError as e:
            fail(f"missing {mod}; pip install -r requirements-session0.txt (or requirements-ec2-inference.txt)", e)

    try:
        import httpx
    except ImportError:
        warn("httpx not installed — skipping endpoint checks.")
        print("\nSession 0 env check done.")
        return 0

    ollama = os.environ.get("OLLAMA_BASE", "http://127.0.0.1:11434").rstrip("/")
    try:
        r = httpx.get(f"{ollama}/api/tags", timeout=3.0)
        if r.status_code == 200:
            ok(f"Ollama reachable at {ollama}")
        else:
            warn(f"Ollama at {ollama} returned HTTP {r.status_code}")
    except Exception as e:
        warn(f"Ollama not reachable at {ollama} (optional). {e}")

    nim = os.environ.get("NIM_OPENAI_BASE", "").strip()
    if not nim:
        nim = os.environ.get("OPENAI_BASE_URL", "").strip()

    if nim:
        try:
            u = nim.rstrip("/")
            models_url = u + "/models" if u.endswith("/v1") else u + "/v1/models"

            r = httpx.get(models_url, timeout=5.0)
            if r.status_code == 200:
                ok(f"OpenAI-compatible /v1/models OK ({models_url})")
            else:
                warn(f"{models_url} returned HTTP {r.status_code}")
        except Exception as e:
            warn(f"Could not GET /v1/models from {nim}: {e}")
    else:
        print("     Set NIM_OPENAI_BASE or OPENAI_BASE_URL to test /v1/models (optional).")

    print("\nSession 0 env check done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
