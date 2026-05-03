"""
Session 1 — run log triage agent on a sample incident.

From repo root (with .env or env vars set):

  python scripts/run_session1.py
  python scripts/run_session1.py --incident samples/incident_01.json --trace trace.json

Requires:
  OPENAI_BASE_URL  (e.g. http://127.0.0.1:8000/v1 via SSH tunnel to EC2 NIM)
  OPENAI_API_KEY   (dummy ok for many local servers, e.g. "not-used")
  OPENAI_MODEL     (exact id from GET {base}/models)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    p = argparse.ArgumentParser(description="Session 1 log triage copilot")
    p.add_argument(
        "--incident",
        default=str(ROOT / "samples" / "incident_01.json"),
        help="Path to incident JSON",
    )
    p.add_argument(
        "--trace",
        default="",
        help="Optional path to write message trace JSON",
    )
    args = p.parse_args()

    from src.session1 import triage_from_incident_path

    triage, trace = triage_from_incident_path(args.incident)
    print(triage.model_dump_json(indent=2))
    if args.trace:
        Path(args.trace).write_text(json.dumps(trace, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
