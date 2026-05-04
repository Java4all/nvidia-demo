"""
Session 3 — RAG over ``data/docs`` runbooks (lexical retrieval, no embedding API).

  python scripts/run_session3.py
  python scripts/run_session3.py --incident samples/incident_01.json --trace trace.json
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
    p = argparse.ArgumentParser(description="Session 3 log triage (RAG runbooks)")
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
    from src.tools_rag import TOOLS_SESSION3

    triage, trace = triage_from_incident_path(
        args.incident,
        prompt_file="session3_system.txt",
        redact=True,
        tools=TOOLS_SESSION3,
    )
    print(triage.model_dump_json(indent=2))
    if args.trace:
        Path(args.trace).write_text(json.dumps(trace, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
