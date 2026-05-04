"""
Session 5 -- batch eval from JSONL cases (incident + optional expectations).

  python scripts/run_eval.py --cases data/eval_cases.jsonl
  python scripts/run_eval.py --cases data/eval_cases.jsonl --session 3 --out eval_report.json

Each JSONL line is one object:

- ``id`` (recommended): case name in reports.
- ``skip`` (optional): if true, skip the case.
- ``incident`` OR ``incident_path`` (relative to repo root): input incident JSON.
- ``expect`` (optional): rules for ``src.eval_harness.check_expectations`` (see there).

Uses ``run_triage_for_session`` (default session **3** = RAG + redaction).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    p = argparse.ArgumentParser(
        description="Session 5 eval harness (eval_cases.jsonl)",
    )
    p.add_argument(
        "--cases",
        default=str(ROOT / "data" / "eval_cases.jsonl"),
        metavar="PATH",
        help="JSONL file of eval cases (default: data/eval_cases.jsonl)",
    )
    p.add_argument(
        "--session",
        type=int,
        choices=(1, 2, 3),
        default=3,
        help="Triage profile (default: 3 = RAG)",
    )
    p.add_argument(
        "--out",
        default="",
        metavar="PATH",
        help="Write JSON report to this path",
    )
    p.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first failure or error",
    )
    args = p.parse_args()

    from src.eval_harness import check_expectations, load_eval_cases, resolve_incident
    from src.triage_profile import run_triage_for_session

    cases_path = Path(args.cases)
    if not cases_path.is_file():
        print(f"error: cases file not found: {cases_path}", file=sys.stderr)
        return 1

    cases = load_eval_cases(cases_path)
    results: list[dict[str, object]] = []
    passed = 0
    failed = 0
    skipped = 0

    for case in cases:
        cid = case.get("id", "(no id)")
        if case.get("skip"):
            skipped += 1
            results.append({"id": cid, "ok": None, "skipped": True, "failures": [], "error": None})
            continue

        t0 = time.perf_counter()
        row: dict[str, object] = {
            "id": cid,
            "ok": False,
            "skipped": False,
            "failures": [],
            "error": None,
            "duration_ms": 0.0,
        }
        try:
            incident = resolve_incident(case, repo_root=ROOT)
            triage, _trace = run_triage_for_session(incident, session=args.session)
            failures = check_expectations(triage, case.get("expect"))
            row["failures"] = failures
            row["ok"] = len(failures) == 0
            if row["ok"]:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            row["error"] = f"{type(e).__name__}: {e}"
            failed += 1
            traceback.print_exc()
        row["duration_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        results.append(row)

        status = "PASS" if row["ok"] else "FAIL"
        if row.get("error"):
            status = "ERROR"
        print(f"[{status}] {cid}  ({row['duration_ms']} ms)")
        if row["failures"]:
            for f in row["failures"]:
                print(f"        - {f}")
        if row.get("error"):
            print(f"        {row['error']}", file=sys.stderr)

        if args.fail_fast and not row.get("ok") and not case.get("skip"):
            if row.get("error") or row.get("failures"):
                break

    summary = {
        "cases_total": len(cases),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "session": args.session,
        "cases_file": str(cases_path),
        "results": results,
    }

    tail = f"Eval summary: passed={passed} failed={failed} skipped={skipped} (session {args.session})"
    print(tail)

    if args.out:
        Path(args.out).write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
