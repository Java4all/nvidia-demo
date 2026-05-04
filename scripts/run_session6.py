"""
Session 6 -- optional multi-agent triage (research + synthesis).

  python scripts/run_session6.py
  python scripts/run_session6.py --incident samples/incident_01.json --trace session6_trace.json

Phase 1: ReAct agent with RAG tools; ends with ### Research summary.
Phase 2: Second LLM call produces TriageOutput JSON only (no tools).
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
    p = argparse.ArgumentParser(
        description="Session 6 multi-agent triage (research then synthesis)",
    )
    p.add_argument(
        "--incident",
        default=str(ROOT / "samples" / "incident_01.json"),
        help="Path to incident JSON",
    )
    p.add_argument(
        "--trace",
        default="",
        help="Optional path to write trace JSON (research previews + synthesis preview)",
    )
    args = p.parse_args()

    from src.session6 import triage_session6_from_incident_path

    triage, trace = triage_session6_from_incident_path(args.incident)
    print(triage.model_dump_json(indent=2))
    if args.trace:
        Path(args.trace).write_text(json.dumps(trace, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
