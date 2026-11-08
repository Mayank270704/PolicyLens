"""Phase B — annotation time tracking, *if* reliable timestamps are
available.

Every save in the GUI appends one row to annotation_events.csv
(timestamp_utc, batch_file, comment_id, action). This module turns that
log into an approximate per-item annotation-time estimate.

This is a rough proxy, not a measurement of actual reading/thinking time,
and the limitations below are reported alongside every result rather than
left implicit -- see `LIMITATIONS` and the `limitations` field on the
returned report.

Run directly:
    python scripts/annotation/timing.py
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts.annotation import schema
else:
    from . import schema

DEFAULT_BREAK_THRESHOLD_SECONDS = 20 * 60  # gaps longer than this are treated as a break, not active work

LIMITATIONS = [
    "Elapsed time between consecutive saves is a proxy for 'time spent on the previous item', "
    "not a direct measurement -- it also includes any time the annotator spent away from the "
    "keyboard between saves.",
    "A gap longer than the break threshold is excluded from the 'active annotation time' "
    "estimate (treated as a pause/break), but the threshold is a heuristic, not a certainty.",
    "If the annotator reorders work (e.g. jumps around via Previous/filters) rather than working "
    "straight through, gaps no longer correspond to 'time on the item that was just saved' in a "
    "simple way -- interpret per-item estimates as approximate, not exact.",
    "The very first save in a session has no preceding event and contributes no timing estimate.",
    "Overwrite saves (the annotator revisiting and changing an already-labeled item) are recorded "
    "with action='overwrite' and are excluded from fresh per-item timing, since the elapsed time "
    "reflects a correction revisit, not first-pass judgment time.",
]


def load_events(path: Path = schema.TIMING_LOG_PATH) -> list[dict]:
    if not path.exists():
        return []
    return schema.read_rows(path)


def analyze_timing(
    events: list[dict],
    break_threshold_seconds: float = DEFAULT_BREAK_THRESHOLD_SECONDS,
) -> dict:
    if not events:
        return {
            "status": "no_data",
            "detail": "No annotation_events.csv entries yet -- no saves have been recorded.",
            "limitations": LIMITATIONS,
        }

    parsed = sorted(
        ({**e, "_ts": schema.parse_iso(e["timestamp_utc"])} for e in events),
        key=lambda e: e["_ts"],
    )

    gaps = []  # (seconds, is_fresh_item)
    for prev, cur in zip(parsed, parsed[1:]):
        seconds = (cur["_ts"] - prev["_ts"]).total_seconds()
        is_fresh_item = cur.get("action") != "overwrite"
        gaps.append((seconds, is_fresh_item))

    active_gaps = [s for s, fresh in gaps if fresh and 0 <= s <= break_threshold_seconds]
    break_gaps = [s for s, fresh in gaps if fresh and s > break_threshold_seconds]
    negative_gaps = [s for s, _ in gaps if s < 0]  # clock skew / out-of-order writes

    n_items_with_estimate = len(active_gaps)

    report = {
        "status": "ok",
        "n_save_events": len(parsed),
        "n_distinct_comment_ids": len(set(e["comment_id"] for e in parsed)),
        "first_event_utc": parsed[0]["timestamp_utc"],
        "last_event_utc": parsed[-1]["timestamp_utc"],
        "break_threshold_seconds": break_threshold_seconds,
        "n_items_with_active_time_estimate": n_items_with_estimate,
        "n_gaps_classified_as_breaks": len(break_gaps),
        "n_negative_or_out_of_order_gaps": len(negative_gaps),
        "active_time_per_item_seconds": {
            "median": round(statistics.median(active_gaps), 1) if active_gaps else None,
            "mean": round(statistics.mean(active_gaps), 1) if active_gaps else None,
            "min": round(min(active_gaps), 1) if active_gaps else None,
            "max": round(max(active_gaps), 1) if active_gaps else None,
        },
        "estimated_total_active_seconds": round(sum(active_gaps), 1) if active_gaps else 0.0,
        "estimated_total_break_seconds": round(sum(break_gaps), 1) if break_gaps else 0.0,
        "limitations": LIMITATIONS,
    }

    if n_items_with_estimate < 10:
        report["low_sample_warning"] = (
            f"Only {n_items_with_estimate} timed item(s) available -- per-item timing estimates "
            "are not statistically meaningful yet at this sample size."
        )

    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Analyze annotation timing from annotation_events.csv.")
    parser.add_argument("--events", type=Path, default=schema.TIMING_LOG_PATH)
    parser.add_argument("--break-threshold-seconds", type=float, default=DEFAULT_BREAK_THRESHOLD_SECONDS)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    events = load_events(args.events)
    report = analyze_timing(events, break_threshold_seconds=args.break_threshold_seconds)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        if report["status"] == "no_data":
            print(report["detail"])
        else:
            print(f"Save events: {report['n_save_events']} "
                  f"({report['n_distinct_comment_ids']} distinct comments)")
            print(f"Window: {report['first_event_utc']} -> {report['last_event_utc']}")
            at = report["active_time_per_item_seconds"]
            print(f"Active time/item (s): median={at['median']} mean={at['mean']} "
                  f"min={at['min']} max={at['max']}")
            print(f"Breaks excluded: {report['n_gaps_classified_as_breaks']} "
                  f"(> {report['break_threshold_seconds']}s gap)")
            if "low_sample_warning" in report:
                print(f"\nWARNING: {report['low_sample_warning']}")
        print("\nLimitations:")
        for l in report["limitations"]:
            print(f"  - {l}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
