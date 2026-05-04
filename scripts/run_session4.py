"""
Session 4 -- CLI: --alert / --logs -> --out JSON (and optional trace).

Uses the Session 3 stack by default (RAG runbooks + redaction + session3 prompt).

Examples::

  python scripts/run_session4.py --alert "High error rate on checkout-api" \\
    --logs samples/sample_logs.txt --out triage.json

  type logs.txt | python scripts/run_session4.py --alert "DB failover" --logs - --out out.json

  python scripts/run_session4.py --alert-file alert_title.txt --logs logs.txt --out triage.json \\
    --service checkout-api --region eu-west-1 --env prod

"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _read_logs(paths: list[str] | None) -> str | None:
    if not paths:
        return None
    parts: list[str] = []
    for p in paths:
        if p == "-":
            parts.append(sys.stdin.read())
        else:
            parts.append(Path(p).read_text(encoding="utf-8"))
    return "\n".join(parts)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Session 4 triage CLI: alert + logs -> TriageOutput JSON",
    )
    ag = p.add_mutually_exclusive_group(required=True)
    ag.add_argument(
        "--alert",
        metavar="TEXT",
        help="Alert title (one line)",
    )
    ag.add_argument(
        "--alert-file",
        metavar="PATH",
        help="Read alert title from file (entire file trimmed, multi-line allowed)",
    )
    p.add_argument(
        "--logs",
        action="append",
        metavar="PATH",
        help="Log file path; use - for stdin. Repeat to concatenate files.",
    )
    p.add_argument(
        "--out",
        required=True,
        metavar="PATH",
        help="Write TriageOutput JSON here",
    )
    p.add_argument(
        "--trace",
        default="",
        metavar="PATH",
        help="Optional path to write message trace JSON",
    )
    p.add_argument(
        "--severity",
        default="P3",
        help="Alert severity (default P3)",
    )
    p.add_argument(
        "--env",
        "--environment",
        dest="environment",
        default="unknown",
        help="Context environment",
    )
    p.add_argument(
        "--region",
        default="unknown",
        help="Context region",
    )
    p.add_argument(
        "--service",
        default="unknown",
        help="Context service name",
    )
    p.add_argument(
        "--fired-at",
        default="",
        help="ISO timestamp for alert (default: now UTC)",
    )
    p.add_argument(
        "--source",
        default="cli",
        help="Alert source label (default cli)",
    )
    p.add_argument(
        "--session",
        type=int,
        choices=(1, 2, 3),
        default=3,
        help="Prompt/tools profile: 1=baseline, 2=redaction prompt, 3=RAG (default)",
    )
    args = p.parse_args()

    if args.alert_file:
        alert_title = Path(args.alert_file).read_text(encoding="utf-8").strip()
    else:
        alert_title = (args.alert or "").strip()
    if not alert_title:
        p.error("alert title is empty (use --alert or a non-empty --alert-file)")

    log_blob = _read_logs(args.logs)

    from src.cli_incident import build_incident
    from src.session1 import run_triage
    from src.tools_log import TOOLS as TOOLS_S1
    from src.tools_rag import TOOLS_SESSION3

    incident = build_incident(
        alert_title,
        log_blob,
        severity=args.severity,
        source=args.source,
        fired_at=args.fired_at or None,
        environment=args.environment,
        region=args.region,
        service=args.service,
    )

    if args.session == 1:
        triage, trace = run_triage(incident, prompt_file="session1_system.txt", redact=False, tools=TOOLS_S1)
    elif args.session == 2:
        triage, trace = run_triage(incident, prompt_file="session2_system.txt", redact=True, tools=TOOLS_S1)
    else:
        triage, trace = run_triage(
            incident,
            prompt_file="session3_system.txt",
            redact=True,
            tools=TOOLS_SESSION3,
        )

    Path(args.out).write_text(triage.model_dump_json(indent=2), encoding="utf-8")
    if args.trace:
        Path(args.trace).write_text(json.dumps(trace, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
