"""
Session 7 -- NIM-only benchmark: latency + schema validity + eval expectations.

Point ``.env`` at your NIM OpenAI-compatible endpoint (same as ``run_session3.py``).

  python scripts/benchmark_session7.py
  python scripts/benchmark_session7.py --cases data/eval_cases.jsonl --out data/session7_nim_report.json

Reports include per-case ``duration_ms``, ``schema_valid`` (TriageOutput produced),
``expect_ok`` (eval rules), and aggregate mean / p50 / p95 latency.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _percentile(sorted_vals: list[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Session 7 NIM benchmark (latency + schema + eval expectations)",
    )
    p.add_argument(
        "--cases",
        default=str(ROOT / "data" / "eval_cases.jsonl"),
        metavar="PATH",
        help="JSONL eval cases (default: data/eval_cases.jsonl)",
    )
    p.add_argument(
        "--session",
        type=int,
        choices=(1, 2, 3),
        default=3,
        help="Triage profile (default 3 = RAG)",
    )
    p.add_argument(
        "--out",
        default=str(ROOT / "data" / "session7_nim_report.json"),
        metavar="PATH",
        help="Write JSON report (default: data/session7_nim_report.json)",
    )
    args = p.parse_args()

    from src.eval_harness import check_expectations, load_eval_cases, resolve_incident
    from src.triage_profile import run_triage_for_session

    cases_path = Path(args.cases)
    if not cases_path.is_file():
        print(f"error: cases file not found: {cases_path}", file=sys.stderr)
        return 1

    base_url = os.environ.get("OPENAI_BASE_URL", "").strip() or "(not set)"
    model = os.environ.get("OPENAI_MODEL", "").strip() or "(not set)"

    cases = load_eval_cases(cases_path)
    results: list[dict[str, object]] = []
    durations: list[float] = []
    schema_ok = 0
    expect_ok = 0
    errors = 0
    skipped = 0
    ran = 0

    for case in cases:
        cid = case.get("id", "(no id)")
        if case.get("skip"):
            skipped += 1
            results.append(
                {
                    "id": cid,
                    "skipped": True,
                    "schema_valid": None,
                    "expect_ok": None,
                    "duration_ms": None,
                    "failures": [],
                    "error": None,
                }
            )
            continue

        t0 = time.perf_counter()
        row: dict[str, object] = {
            "id": cid,
            "skipped": False,
            "schema_valid": False,
            "expect_ok": False,
            "duration_ms": 0.0,
            "failures": [],
            "error": None,
        }
        try:
            incident = resolve_incident(case, repo_root=ROOT)
            triage, _trace = run_triage_for_session(incident, session=args.session)
            row["schema_valid"] = True
            schema_ok += 1
            failures = check_expectations(triage, case.get("expect"))
            row["failures"] = failures
            row["expect_ok"] = len(failures) == 0
            if row["expect_ok"]:
                expect_ok += 1
            ran += 1
        except Exception as e:
            row["error"] = f"{type(e).__name__}: {e}"
            row["schema_valid"] = False
            errors += 1
            traceback.print_exc()
        row["duration_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        if row["duration_ms"] is not None and not case.get("skip"):
            durations.append(float(row["duration_ms"]))
        results.append(row)

    durations.sort()
    summary = {
        "backend": "nim",
        "note": "Configure OPENAI_BASE_URL and OPENAI_MODEL in .env to point at your NIM container.",
        "openai_base_url_preview": base_url[:120],
        "openai_model": model,
        "session_profile": args.session,
        "cases_file": str(cases_path),
        "cases_total": len(cases),
        "cases_run": ran,
        "skipped": skipped,
        "schema_valid_count": schema_ok,
        "expect_pass_count": expect_ok,
        "error_count": errors,
        "latency_ms": {
            "mean": round(statistics.mean(durations), 1) if durations else 0.0,
            "min": round(min(durations), 1) if durations else 0.0,
            "max": round(max(durations), 1) if durations else 0.0,
            "p50": round(_percentile(durations, 50), 1) if durations else 0.0,
            "p95": round(_percentile(durations, 95), 1) if durations else 0.0,
        },
        "results": results,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Session 7 NIM benchmark (OPENAI_* from .env -> your NIM)")
    print(f"  cases file:     {cases_path}")
    print(f"  session:        {args.session}")
    print(f"  model (env):    {model}")
    print(f"  base URL:       {base_url[:80]}{'...' if len(base_url) > 80 else ''}")
    print(f"  ran / total:    {ran} / {len(cases)}  (skipped: {skipped})")
    print(f"  schema valid:   {schema_ok}/{ran}" if ran else "  schema valid:   n/a")
    print(f"  expect pass:    {expect_ok}/{ran}" if ran else "  expect pass:    n/a")
    print(f"  errors:         {errors}")
    if durations:
        print(
            f"  latency_ms:     mean={summary['latency_ms']['mean']}  "
            f"p50={summary['latency_ms']['p50']}  p95={summary['latency_ms']['p95']}  "
            f"min={summary['latency_ms']['min']}  max={summary['latency_ms']['max']}"
        )
    print(f"  report written: {out_path}")

    # Non-zero only on runtime failures (LLM/API errors), not on expect mismatches.
    return 1 if errors > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
