"""Phase B — consolidated annotation quality analysis.

A single reusable report combining everything that can be said about
annotation quality at any point in the workflow: stance/exclusion/
confidence distributions, completion by stratum (via progress.py),
intra-annotator kappa/confusion matrix/per-class agreement/interpretation
(via repeat.py, only once both passes exist), and annotation-time
estimates (via timing.py, only once save events exist).

Works correctly with zero annotations (reports "no data yet" for each
section rather than crashing or fabricating placeholder numbers), and
continues to work unchanged once real annotations exist -- nothing here is
specific to any particular label values.

Run directly:
    python scripts/annotation/evaluate.py
    python scripts/annotation/evaluate.py --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts.annotation import progress, repeat, schema, timing
else:
    from . import progress, repeat, schema, timing


def build_full_report(
    batch_path: Path = schema.MAIN_BATCH_PATH,
    repeat_batch_path: Path = schema.REPEAT_PASS_BATCH_PATH,
    plan_path: Path = schema.REPEAT_PLAN_PATH,
    events_path: Path = schema.TIMING_LOG_PATH,
) -> dict:
    rows = schema.read_rows(batch_path)
    progress_report = progress.build_report(rows)

    repeat_section: dict
    if not plan_path.exists():
        repeat_section = {"status": "no_plan", "detail": f"{plan_path} not found."}
    else:
        status = repeat.check_passes_complete(batch_path, repeat_batch_path, plan_path)
        if not status["pass1_complete"]:
            repeat_section = {
                "status": "first_pass_incomplete",
                "detail": f"{len(status['pass1_incomplete_ids'])} repeat item(s) not yet labeled "
                          "in the main batch.",
                "pass1_incomplete_ids": status["pass1_incomplete_ids"],
            }
        elif not status["pass2_complete"]:
            repeat_section = {
                "status": "second_pass_incomplete",
                "detail": "Second (blind, time-gapped) pass not complete yet -- no kappa computed. "
                          "This is expected and correct: no consistency figure should exist until "
                          "a genuine second pass does.",
                "pass2_file_exists": status["pass2_file_exists"],
                "pass2_incomplete_ids": status["pass2_incomplete_ids"],
            }
        else:
            repeat_section = repeat.compute_consistency_report(batch_path, repeat_batch_path, plan_path)
            repeat_section["status"] = "computed"

    timing_report = timing.analyze_timing(timing.load_events(events_path))

    return {
        "generated_utc": schema.utcnow_iso(),
        "batch_path": str(batch_path),
        "annotation_progress": progress_report,
        "intra_annotator_consistency": repeat_section,
        "annotation_timing": timing_report,
        "notes": {
            "agreement_type": "intra-annotator (test-retest) only -- never inter-annotator; there "
                               "is exactly one human annotator in this experiment.",
            "gold_standard_claim": "NOT MADE. See docs/dataset/SINGLE_ANNOTATOR_PROTOCOL.md section 9.",
        },
    }


def format_report(report: dict) -> str:
    lines = []
    p = report["annotation_progress"]
    lines.append("=== Annotation progress ===")
    lines.append(progress.format_report(p))

    lines.append("\n=== Intra-annotator consistency ===")
    r = report["intra_annotator_consistency"]
    if r["status"] != "computed":
        lines.append(f"({r['status']}) {r.get('detail', '')}")
    else:
        sk = r["stance_kappa"]
        lines.append(f"Exclusion agreement rate: {r['exclusion_agreement']['agreement_rate']}")
        lines.append(f"Stance kappa: {sk['kappa']} ({sk['interpretation']}), "
                      f"n={sk['n_items_compared']}")
        if "low_sample_warning" in sk:
            lines.append(f"  WARNING: {sk['low_sample_warning']}")

    lines.append("\n=== Annotation timing ===")
    t = report["annotation_timing"]
    if t["status"] == "no_data":
        lines.append(t["detail"])
    else:
        at = t["active_time_per_item_seconds"]
        lines.append(f"{t['n_save_events']} save events; "
                      f"median active time/item = {at['median']}s")
        if "low_sample_warning" in t:
            lines.append(f"  WARNING: {t['low_sample_warning']}")

    lines.append(f"\n{report['notes']['agreement_type']}")
    lines.append(report['notes']['gold_standard_claim'])
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Consolidated annotation quality report.")
    parser.add_argument("--batch", type=Path, default=schema.MAIN_BATCH_PATH)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    report = build_full_report(batch_path=args.batch)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(format_report(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
