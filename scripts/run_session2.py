"""
Session 2 — same triage agent as Session 1 with:
  - system prompt in ``src/prompts/session2_system.txt`` (redaction-aware + strict JSON)
  - incident text redacted before the LLM (see ``src/redaction.py``)
  - JSON parse / repair in ``src/json_repair.py`` (shared with Session 1)

  python scripts/run_session2.py
  python scripts/run_session2.py --incident samples/incident_01.json --trace trace.json
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
    p = argparse.ArgumentParser(description="Session 2 log triage (redaction + prompts + repair)")
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

    triage, trace = triage_from_incident_path(
        args.incident,
        prompt_file="session2_system.txt",
        redact=True,
    )
    print(triage.model_dump_json(indent=2))
    if args.trace:
        Path(args.trace).write_text(json.dumps(trace, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
