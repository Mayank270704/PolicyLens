"""Add redacted display text to a metadata-only annotation sheet — ONLY against TWO recorded
written decisions: a rights_permission from the data provider / rights holder, and an
ethics_approval or ethics_exemption from the institution. Without both, this script refuses to run.

    python -m ml.indian_stance.materialize_text --sheet <annotator_sheet.csv> \
        --clearance <rights_record.json> --clearance <ethics_record.json> \
        --out-dir data/annotations/indian/<new_dir>

Redaction: emails, phone-like numbers, Aadhaar-/PAN-like numbers and URLs become typed placeholders.
MyGov items needing manual review (sign-offs, "on behalf of") are WITHHELD unless a steward supplies
reviewed text via --steward-redactions (CSV: item_id,redacted_text). Tweets use the masked text.
Output must go to a gitignored directory.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import pandas as pd

from ml.indian_stance.common import (AADHAAR_RE, EMAIL_RE, PAN_RE, PHONE_RE, REPO_ROOT, URL_RE, SourceError,
                                     new_output_dir, resolve_source_root, sha256_file, write_csv, write_manifest)

REQUIRED_CLEARANCE_KEYS = ("decision_type", "status", "source", "permitted_activities", "decided_by", "decision_date",
                           "evidence_reference")
PLACEHOLDER_RE = re.compile(r"todo|tbd|placeholder|example|<.*>|fill", re.I)
RIGHTS_TYPES = ("rights_permission",)                    # data provider / rights holder (e.g. MyGov/NIC)
ETHICS_TYPES = ("ethics_approval", "ethics_exemption")   # institutional ethics body


class ClearanceError(RuntimeError):
    pass


def check_clearance(path: Path, source: str) -> dict:
    if not path or not Path(path).is_file():
        raise ClearanceError("no clearance record supplied; text cannot be materialised")
    rec = json.loads(Path(path).read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED_CLEARANCE_KEYS if not rec.get(k)]
    if missing:
        raise ClearanceError(f"clearance record missing: {missing}")
    if rec["decision_type"] not in RIGHTS_TYPES + ETHICS_TYPES:
        raise ClearanceError(f"decision_type must be one of {list(RIGHTS_TYPES + ETHICS_TYPES)}")
    if rec["status"] != "CLEARED":
        raise ClearanceError(f"clearance status is '{rec['status']}', not CLEARED")
    if rec["source"] != source:
        raise ClearanceError(f"clearance covers '{rec['source']}', not '{source}'")
    if "internal_annotation" not in rec["permitted_activities"]:
        raise ClearanceError("clearance does not permit internal_annotation")
    for k in ("decided_by", "evidence_reference"):
        if PLACEHOLDER_RE.search(str(rec[k])):
            raise ClearanceError(f"clearance field '{k}' looks like a placeholder")
    try:
        date.fromisoformat(str(rec["decision_date"]))
    except ValueError as e:
        raise ClearanceError("decision_date must be an ISO date (YYYY-MM-DD)") from e
    return rec


def check_clearances(paths: list[Path], source: str) -> list[dict]:
    """Both written decisions are required: rights holder permission AND institutional ethics."""
    if not paths:
        raise ClearanceError("no clearance records supplied; text cannot be materialised")
    recs = [check_clearance(p, source) for p in paths]
    types = {r["decision_type"] for r in recs}
    if not types & set(RIGHTS_TYPES):
        raise ClearanceError("missing a CLEARED rights_permission record from the data provider / rights holder")
    if not types & set(ETHICS_TYPES):
        raise ClearanceError("missing a CLEARED ethics_approval or ethics_exemption record from the institution")
    return recs


def redact(text: str) -> tuple[str, list[str]]:
    applied = []
    for rx, token, name in ((EMAIL_RE, "[EMAIL]", "email"), (URL_RE, "[URL]", "url"), (PHONE_RE, "[PHONE]", "phone"),
                            (AADHAAR_RE, "[ID_NUMBER]", "aadhaar_like"), (PAN_RE, "[ID_NUMBER]", "pan_like")):
        text, n = rx.subn(token, text)
        if n:
            applied.append(f"{name}:{n}")
    return text, applied


def is_gitignored(path: Path) -> bool:
    probe = Path(path) / "probe.csv"
    r = subprocess.run(["git", "-C", str(REPO_ROOT), "check-ignore", "-q", str(probe)], capture_output=True)
    return r.returncode == 0


def materialize(sheet: Path, clearances: list[Path], out_dir: Path, source_root: Path, steward: Path | None = None) -> dict:
    df = pd.read_csv(sheet, dtype=str, keep_default_na=False)
    source = df.source.iloc[0]
    recs = check_clearances([Path(c) for c in clearances], source)
    if not is_gitignored(out_dir):
        raise ClearanceError(f"{out_dir} is not gitignored; refusing to write text where git could track it")
    P = source_root / "processed"
    reviewed = {}
    if steward:
        s = pd.read_csv(steward, dtype=str, keep_default_na=False)
        reviewed = {k: v for k, v in zip(s.item_id, s.redacted_text) if str(v).strip()}
    # A rights condition requiring removal of names and other identifiers BEFORE annotation cannot be met by
    # regexes alone (names in running text are undetectable), so every item needs steward-reviewed text.
    if any(r.get("full_identifier_review_required") for r in recs):
        missing = sorted(set(df.item_id) - set(reviewed))
        if missing:
            raise ClearanceError(
                f"rights conditions require removal of names and other identifiers before annotation: steward-reviewed "
                f"text covers {len(df) - len(missing)}/{len(df)} items; supply every item via --steward-redactions")
    texts, statuses, applied_col = [], [], []
    if source == "mygov":
        clean = pd.read_csv(P / "mygov_comments_clean.csv", dtype=str, keep_default_na=False).set_index("comment_id")
        for _, r in df.iterrows():
            if r.pii_handling == "MANUAL_REVIEW" and r.item_id not in reviewed:
                texts.append(""), statuses.append("WITHHELD_PENDING_STEWARD_REDACTION"), applied_col.append("")
                continue
            raw = reviewed.get(r.item_id, clean.comment_text[r.representative_comment_id])
            t, applied = redact(raw)
            texts.append(t), statuses.append("MATERIALISED_REDACTED" if applied else "MATERIALISED")
            applied_col.append(";".join(applied + (["steward_reviewed"] if r.item_id in reviewed else [])))
    else:
        clean = pd.read_csv(P / "kaggle_indian_politics_tweets_clean.csv", dtype=str, keep_default_na=False,
                            usecols=["tweet_row_id", "tweet_text_masked"]).set_index("tweet_row_id")
        for _, r in df.iterrows():
            t, applied = redact(reviewed.get(r.item_id, clean.tweet_text_masked[r.tweet_row_id]))
            texts.append(t), statuses.append("MATERIALISED_MASKED"), applied_col.append(";".join(["mentions_urls_masked"] + applied))
    out = df.copy()
    out["text_status"] = statuses
    out.insert(out.columns.get_loc("text_status") + 1, "display_text", texts)
    out.insert(out.columns.get_loc("display_text") + 1, "redaction_applied", applied_col)
    out_dir = new_output_dir(out_dir)
    write_csv(out_dir / sheet.name.replace(".csv", "_with_text.csv"), out.to_dict("records"), list(out.columns))
    inputs = {"sheet": sheet, **{f"clearance_{i}": Path(c) for i, c in enumerate(clearances, 1)}}
    if steward:
        inputs["steward_redactions"] = Path(steward)
    summary = {"items": len(out), "text_status": pd.Series(statuses).value_counts().to_dict()}
    write_manifest(out_dir, inputs, source_root, {
        "clearances": [{"sha256": sha256_file(Path(c)), **{k: r[k] for k in REQUIRED_CLEARANCE_KEYS}}
                       for c, r in zip(clearances, recs)],
        "summary": summary, "do_not_share": True})
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sheet", required=True)
    ap.add_argument("--clearance", required=True, action="append",
                    help="clearance record JSON; give twice: one rights_permission and one ethics_approval/exemption")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--steward-redactions")
    ap.add_argument("--source-root")
    a = ap.parse_args(argv)
    try:
        s = materialize(Path(a.sheet), [Path(c) for c in a.clearance], Path(a.out_dir), resolve_source_root(a.source_root),
                        Path(a.steward_redactions) if a.steward_redactions else None)
    except (ClearanceError, SourceError, FileExistsError) as e:
        print(f"[REFUSED] {e}", file=sys.stderr)
        return 2
    print(s)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
