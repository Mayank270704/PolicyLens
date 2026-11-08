"""Task 2 — annotation progress management.

Reports total/annotated/pending/excluded counts, stance and confidence
distributions, overall completion percentage, and completion broken down
by each of the 9 sampling strata (source_dataset x length_bucket).

Run directly:
    python scripts/annotation/progress.py
    python scripts/annotation/progress.py --json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts.annotation import schema
else:
    from . import schema


def _stratum_key(row: dict) -> str:
    ds = row.get("source_dataset", "unknown")
    try:
        wc = int(row.get("word_count", "0") or 0)
    except (TypeError, ValueError):
        wc = 0
    return f"{ds}|{schema.length_bucket(wc)}"


def build_report(rows: list[dict]) -> dict:
    total = len(rows)
    stance_counter: Counter = Counter()
    exclusion_counter: Counter = Counter()
    confidence_counter: Counter = Counter()
    annotated = 0
    excluded = 0
    pending = 0

    strata_totals: Counter = Counter()
    strata_done: Counter = Counter()

    for row in rows:
        label = (row.get("annotator_label") or "").strip()
        excl = (row.get("exclusion_code") or "").strip()
        conf = (row.get("annotation_confidence") or "").strip()
        stratum = _stratum_key(row)
        strata_totals[stratum] += 1

        if label:
            annotated += 1
            stance_counter[label] += 1
            strata_done[stratum] += 1
        elif excl:
            excluded += 1
            exclusion_counter[excl] += 1
            strata_done[stratum] += 1
        else:
            pending += 1

        if conf:
            confidence_counter[schema.CONFIDENCE_LABELS.get(conf, conf)] += 1

    completion_pct = round((annotated + excluded) / total * 100, 1) if total else 0.0

    completion_by_stratum = {
        stratum: {
            "done": strata_done.get(stratum, 0),
            "total": strata_totals[stratum],
            "pct": round(strata_done.get(stratum, 0) / strata_totals[stratum] * 100, 1)
            if strata_totals[stratum] else 0.0,
        }
        for stratum in sorted(strata_totals)
    }

    return {
        "total_comments": total,
        "annotated_comments": annotated,
        "pending_comments": pending,
        "excluded_comments": excluded,
        "excluded_by_reason": dict(sorted(exclusion_counter.items())),
        "stance_distribution": dict(sorted(stance_counter.items())),
        "confidence_distribution": dict(sorted(confidence_counter.items())),
        "completion_percentage": completion_pct,
        "completion_by_stratum": completion_by_stratum,
        "n_strata": len(strata_totals),
    }


def format_report(report: dict) -> str:
    lines = [
        f"Total comments:      {report['total_comments']}",
        f"Annotated (stance):  {report['annotated_comments']}",
        f"Excluded:            {report['excluded_comments']}",
        f"Pending:             {report['pending_comments']}",
        f"Completion:          {report['completion_percentage']}%",
        "",
        "Stance distribution:",
    ]
    for k, v in report["stance_distribution"].items():
        lines.append(f"  {k}: {v}")
    lines += ["", "Excluded by reason:"]
    for k, v in report["excluded_by_reason"].items():
        lines.append(f"  {k}: {v}")
    lines += ["", "Confidence distribution:"]
    for k, v in report["confidence_distribution"].items():
        lines.append(f"  {k}: {v}")
    lines += [
        "",
        f"Completion by stratum ({report['n_strata']} strata, source_dataset|length_bucket):",
    ]
    for stratum, info in report["completion_by_stratum"].items():
        lines.append(f"  {stratum}: {info['done']}/{info['total']} ({info['pct']}%)")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Report annotation progress for a batch CSV.")
    parser.add_argument("--batch", type=Path, default=schema.MAIN_BATCH_PATH)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text.")
    args = parser.parse_args(argv)

    rows = schema.read_rows(args.batch)
    report = build_report(rows)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(format_report(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
