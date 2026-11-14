"""Phase B: MyGov data-quality analysis (deduplication, truncation, personal-information review).

Outputs IDs, flags, counts and text hashes only. Comment text and detected personal values
are never written.

    python -m ml.indian_stance.mygov_quality --out-dir data/processed/indian/mygov_quality_v1
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

from ml.indian_stance.common import (AADHAAR_RE, EMAIL_RE, MENTION_RE, PAN_RE, PHONE_RE, SIGNOFF_RE, TERMINAL_RE,
                                     URL_RE, SourceError, new_output_dir, norm_text, resolve_source_root, sha256_text,
                                     write_csv, write_json, write_manifest)

PII_PATTERNS = {"email": EMAIL_RE, "phone_like": PHONE_RE, "aadhaar_like_12_digits": AADHAAR_RE, "pan_like": PAN_RE,
                "url": URL_RE, "signoff_or_on_behalf_of": SIGNOFF_RE}
# Proposed handling per category; applied only when text is materialised after clearance.
REDACTION_MODE = {"email": "AUTO_TYPED_PLACEHOLDER", "phone_like": "AUTO_TYPED_PLACEHOLDER",
                  "aadhaar_like_12_digits": "AUTO_TYPED_PLACEHOLDER", "pan_like": "AUTO_TYPED_PLACEHOLDER",
                  "url": "AUTO_PLACEHOLDER", "signoff_or_on_behalf_of": "MANUAL_REVIEW"}
TRUNCATION_MIN_CHARS = 490  # OLD project's near-limit threshold (MyGov limit is 500 characters)


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def dedup_groups(df: pd.DataFrame, id_col: str = "comment_id", text_col: str = "comment_text") -> list[dict]:
    """Group rows by normalised text; representative = numerically smallest ID (deterministic)."""
    groups: dict[str, list[str]] = defaultdict(list)
    exact: dict[str, set[str]] = defaultdict(set)
    for cid, text in zip(df[id_col], df[text_col]):
        key = norm_text(text)
        groups[key].append(cid)
        exact[key].add(text)
    out = []
    for key, ids in groups.items():
        ids_sorted = sorted(ids, key=lambda x: (len(x), x))
        out.append({"normalised_text_sha256": sha256_text(key), "group_size": len(ids),
                    "member_comment_ids": ";".join(ids_sorted), "representative_comment_id": ids_sorted[0],
                    "distinct_exact_variants": len(exact[key])})
    out.sort(key=lambda g: (len(g["representative_comment_id"]), g["representative_comment_id"]))
    for i, g in enumerate(out, 1):
        g["group_id"] = f"MYG-G{i:04d}"
    return out


def pii_review(cid: str, text: str) -> dict:
    """Categories, span counts and span zone only; never the matched values."""
    row = {"comment_id": cid, "char_count": len(text)}
    cats, body_hits = [], 0
    for cat, rx in PII_PATTERNS.items():
        src = EMAIL_RE.sub("", text) if cat == "at_mention" else text
        spans = list(rx.finditer(src))
        row[f"n_{cat}"] = len(spans)
        if spans:
            cats.append(cat)
            for m in spans:
                if m.start() < 0.8 * max(len(text), 1):
                    body_hits += 1
    row["n_at_mention"] = len(MENTION_RE.findall(EMAIL_RE.sub("", text)))
    row["categories"] = ";".join(cats)
    row["any_flag"] = bool(cats) or row["n_at_mention"] > 0
    auto = [c for c in cats if REDACTION_MODE[c].startswith("AUTO")]
    row["auto_redaction_chars"] = sum(len(m.group(0)) for c in auto for m in PII_PATTERNS[c].finditer(text))
    row["auto_redaction_share_of_text"] = round(row["auto_redaction_chars"] / max(len(text), 1), 4)
    row["spans_in_first_80pct_of_text"] = body_hits
    modes = {REDACTION_MODE[c] for c in cats}
    row["proposed_handling"] = ("MANUAL_REVIEW" if "MANUAL_REVIEW" in modes else
                                "AUTO_REDACT" if modes else "NONE")
    return row


def run(source_root: Path, out_dir: Path) -> dict:
    P = source_root / "processed"
    inputs = {"clean": P / "mygov_comments_clean.csv", "raw": P / "mygov_comments_raw.csv",
              "pii_flags": P / "mygov_pii_review_flags.csv",
              "template_A": P / "mygov" / "annotation_v1" / "mygov_annotation_template_v1_annotator_A.csv"}
    clean, raw, flags, tmpl = (read_csv(inputs[k]) for k in ("clean", "raw", "pii_flags", "template_A"))
    if clean.comment_id.duplicated().any():
        raise ValueError("clean file has duplicate comment_id")
    out_dir = new_output_dir(out_dir)

    # duplicate IDs in the raw extraction: verify duplicates carry identical text
    dup_raw = raw[raw.comment_id.duplicated(keep=False)]
    dup_id_text_identical = all(g.comment_text.nunique() == 1 for _, g in dup_raw.groupby("comment_id"))

    groups = dedup_groups(clean)
    multi = [g for g in groups if g["group_size"] > 1]
    legacy = clean[clean.exact_text_duplicate_group != ""].groupby("exact_text_duplicate_group").comment_id.apply(
        lambda s: ";".join(sorted(s, key=lambda x: (len(x), x)))).tolist()
    mine = sorted(g["member_comment_ids"] for g in multi)
    legacy_agrees = sorted(legacy) == mine
    write_csv(out_dir / "dedup_groups.csv", groups,
              ["group_id", "representative_comment_id", "group_size", "member_comment_ids", "distinct_exact_variants",
               "normalised_text_sha256"])

    # Truncation is judged on the RAW extracted text: the 500-character cap applies to the submission,
    # and whitespace cleaning shortened 133 texts (by up to 28 chars), hiding at-limit comments.
    raw_text = raw.drop_duplicates("comment_id").set_index("comment_id").comment_text
    trunc = []
    for cid in clean.comment_id:
        text = raw_text[cid]
        if len(text) >= TRUNCATION_MIN_CHARS:
            no_term = bool(text) and not TERMINAL_RE.search(text)
            trunc.append({"comment_id": cid, "char_count": len(text), "ends_without_terminal_punctuation": no_term,
                          "truncation_class": "LIKELY_TRUNCATED" if no_term else "AT_LIMIT_COMPLETE_ENDING"})
    write_csv(out_dir / "truncation_candidates.csv", trunc,
              ["comment_id", "char_count", "ends_without_terminal_punctuation", "truncation_class"])

    pii_rows = [pii_review(cid, t) for cid, t in zip(clean.comment_id, clean.comment_text)]
    pii_df = pd.DataFrame(pii_rows)
    recorded = flags.set_index("comment_id").any_flag.eq("True")
    agree = int((pii_df.set_index("comment_id").any_flag == recorded.reindex(pii_df.comment_id).values).sum())
    flagged = [r for r in pii_rows if r["any_flag"]]
    pii_cols = ["comment_id", "char_count", "categories", "proposed_handling", "auto_redaction_chars",
                "auto_redaction_share_of_text", "spans_in_first_80pct_of_text"] + [f"n_{c}" for c in PII_PATTERNS] + ["n_at_mention"]
    write_csv(out_dir / "pii_review.csv", flagged, pii_cols)

    reps = {g["representative_comment_id"] for g in groups}
    pool = clean[clean.comment_id.isin(reps)]
    trunc_ids = {t["comment_id"] for t in trunc if t["truncation_class"] == "LIKELY_TRUNCATED"}
    flagged_ids = {r["comment_id"] for r in flagged}
    manual_ids = {r["comment_id"] for r in flagged if r["proposed_handling"] == "MANUAL_REVIEW"}
    attach = clean[clean.has_attachment == "True"]
    summary = {
        "source": "MyGov — Public consultation on Government Open Data Use License - India (2016)",
        "rows_clean": len(clean), "rows_raw": len(raw), "unique_comment_ids": int(clean.comment_id.nunique()),
        "raw_duplicate_id_records": int(raw.is_duplicate_id.eq("True").sum()),
        "raw_duplicate_ids_have_identical_text": dup_id_text_identical,
        "distinct_texts_exact": int(clean.comment_text.nunique()),
        "normalised_text_groups": len(groups), "multi_member_groups": len(multi),
        "rows_in_multi_member_groups": sum(g["group_size"] for g in multi),
        "groups_with_non_identical_exact_variants": sum(g["distinct_exact_variants"] > 1 for g in multi),
        "grouping_matches_legacy_exact_text_duplicate_group": legacy_agrees,
        "truncation": {"at_or_above_490_chars": len(trunc), "likely_truncated_no_terminal_punctuation": len(trunc_ids),
                       "likely_truncated_in_candidate_pool": len(trunc_ids & reps)},
        "personal_information": {
            "flagged_comments": len(flagged), "agrees_with_recorded_any_flag": f"{agree}/{len(clean)}",
            "by_category": {c: int((pii_df[f"n_{c}"] > 0).sum()) for c in PII_PATTERNS},
            "at_mention": int((pii_df.n_at_mention > 0).sum()),
            "proposed_handling": {k: int(v) for k, v in pd.Series([r["proposed_handling"] for r in flagged]).value_counts().items()},
            "auto_redaction_share_of_text_max": float(max([r["auto_redaction_share_of_text"] for r in flagged] or [0])),
            "flagged_with_spans_in_first_80pct": sum(r["spans_in_first_80pct_of_text"] > 0 for r in flagged),
            "flagged_in_candidate_pool": len(flagged_ids & reps), "manual_review_in_candidate_pool": len(manual_ids & reps)},
        "attachments": {"has_attachment": len(attach),
                        "has_attachment_word_count_le_10": int((attach.word_count.astype(int) <= 10).sum()),
                        "note": "attachments were not saved; attachment-only comments cannot be read"},
        "script_detected_candidate_pool": {k: int(v) for k, v in pool.script_detected.value_counts().items()},
        "word_count_candidate_pool": {"min": int(pool.word_count.astype(int).min()), "median": float(pool.word_count.astype(int).median()),
                                      "max": int(pool.word_count.astype(int).max())},
        "legacy_annotation_batch_of_representatives": {k: int(v) for k, v in tmpl[tmpl.comment_id.isin(reps)].annotation_batch.value_counts().items()},
        "candidate_pool_size": len(reps),
        "consultations": int(clean.consultation_title.nunique()),
    }
    write_json(out_dir / "summary.json", summary)
    write_manifest(out_dir, inputs, source_root, {
        "script": "ml/indian_stance/mygov_quality.py", "privacy": "IDs, flags, counts and hashes only; no comment text or personal values",
        "normalisation": "NFKC + whitespace collapse + lowercase", "representative_rule": "numerically smallest comment_id per group",
        "truncation_basis": "raw extracted text length (>= 490 chars) and no terminal punctuation"})
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source-root")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    try:
        s = run(resolve_source_root(a.source_root), Path(a.out_dir))
    except (SourceError, FileExistsError, ValueError) as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2
    import json
    print(json.dumps(s, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
