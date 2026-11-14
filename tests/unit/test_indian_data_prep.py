"""Indian data preparation: deduplication, provenance, annotation schema/validator, tweet split
leakage, and the clearance-gated text materialiser. Synthetic fixtures only."""
import json
from pathlib import Path

import pandas as pd
import pytest

from ml.indian_stance import annotation_schema as S
from ml.indian_stance import build_batches, materialize_text, mygov_quality, tweets_split, validate_annotations
from ml.indian_stance.common import norm_text, norm_tweet, sha256_text, token_set

LONG_CUT = "open data " * 50  # 500 chars, no terminal punctuation


def _write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)


@pytest.fixture
def source_root(tmp_path):
    root = tmp_path / "dataset" / "indian"
    P = root / "processed"
    texts = {"101": "I support the licence. Contact me at someone@example.org",
             "102": "Withdraw this licence, it is harmful.",
             "103": "  WITHDRAW this licence,   it is harmful. ",
             "104": LONG_CUT,
             "105": "Good initiative.\nRegards, Ravi"}
    clean = [{"comment_id": k, "consultation_title": "Draft licence", "comment_text": v, "has_attachment": "False",
              "word_count": str(len(v.split())), "script_detected": "Latin",
              "exact_text_duplicate_group": "G1" if k in ("102", "103") else ""} for k, v in texts.items()]
    _write(P / "mygov_comments_clean.csv", clean)
    _write(P / "mygov_comments_raw.csv", [{"comment_id": r["comment_id"], "comment_text": r["comment_text"],
                                           "is_duplicate_id": "False"} for r in clean]
           + [{"comment_id": "101", "comment_text": texts["101"], "is_duplicate_id": "True"}])
    _write(P / "mygov_pii_review_flags.csv", [{"comment_id": k, "any_flag": str(k in ("101", "105"))} for k in texts])
    _write(P / "mygov" / "annotation_v1" / "mygov_annotation_template_v1_annotator_A.csv",
           [{"comment_id": k, "annotation_batch": "pilot_50" if k == "101" else "main", "clause_numbers_detected": ""}
            for k in texts])
    tweets = [{"tweet_row_id": str(i), "created_at_utc": "2023-01-0%d 10:00:00+00:00" % (1 + i % 3),
               "author_pseudo_id": f"U{i % 4}", "tweet_text": t, "tweet_text_masked": t.replace("@raj", "@[user]"),
               "script_detected": "Latin", "exact_text_duplicate_group": ""}
              for i, t in enumerate(["@raj great budget", "the budget is bad", "@raj great budget!",
                                     "farm laws must go", "who decides the budget", "support the new metro"])]
    _write(P / "kaggle_indian_politics_tweets_clean.csv", tweets)
    return root


# ---- deduplication ---------------------------------------------------------

def test_dedup_groups_normalise_whitespace_case_and_pick_smallest_id():
    df = pd.DataFrame({"comment_id": ["20", "3", "11"], "comment_text": ["Same  TEXT", "same text", "other"]})
    groups = mygov_quality.dedup_groups(df)
    multi = [g for g in groups if g["group_size"] > 1]
    assert len(groups) == 2 and len(multi) == 1
    assert multi[0]["member_comment_ids"] == "3;20" and multi[0]["representative_comment_id"] == "3"
    assert multi[0]["distinct_exact_variants"] == 2


def test_norm_text_applies_nfkc():
    assert norm_text("ﬁle  Data") == norm_text("file data")


def test_mygov_quality_outputs_no_text_and_flags_truncation(source_root, tmp_path):
    out = tmp_path / "q"
    s = mygov_quality.run(source_root, out)
    assert s["normalised_text_groups"] == 4 and s["rows_in_multi_member_groups"] == 2
    assert s["truncation"]["likely_truncated_no_terminal_punctuation"] == 1
    assert s["personal_information"]["by_category"]["email"] == 1
    assert s["personal_information"]["proposed_handling"] == {"AUTO_REDACT": 1, "MANUAL_REVIEW": 1}
    for f in out.iterdir():
        body = f.read_text(encoding="utf-8")
        assert "someone@example.org" not in body and "harmful" not in body


# ---- provenance-preserving batch + validator --------------------------------

def _mygov_batch(source_root, tmp_path):
    q = tmp_path / "q"
    mygov_quality.run(source_root, q)
    out = tmp_path / "batch"
    build_batches.build_mygov(source_root, q, out)
    return out


def test_batch_partitions_source_ids_and_contains_no_text(source_root, tmp_path):
    out = _mygov_batch(source_root, tmp_path)
    items = pd.read_csv(out / "mygov_batch_v2_items.csv", dtype=str, keep_default_na=False)
    members = [m for s in items.member_comment_ids for m in s.split(";")]
    assert sorted(members) == ["101", "102", "103", "104", "105"] and len(items) == 4
    assert not any("harmful" in open(p, encoding="utf-8").read() for p in out.iterdir())
    assert json.loads((out / "manifest.json").read_text(encoding="utf-8"))["summary"]["text_included"] is False


def test_validator_passes_blank_sheet_and_counts_zero_annotations(source_root, tmp_path):
    out = _mygov_batch(source_root, tmp_path)
    res = validate_annotations.validate(out / "mygov_batch_v2_annotator_A.csv", source_root)
    assert res["ok"] and res["annotated_rows"] == 0 and res["provenance_checked"]


def test_validator_detects_tampered_provenance(source_root, tmp_path):
    out = _mygov_batch(source_root, tmp_path)
    p = out / "mygov_batch_v2_annotator_A.csv"
    df = pd.read_csv(p, dtype=str, keep_default_na=False)
    df.loc[0, "normalised_text_sha256"] = "0" * 64
    bad = tmp_path / "bad.csv"
    df.to_csv(bad, index=False)
    res = validate_annotations.validate(bad, source_root)
    assert not res["ok"] and any("does not match source text" in e for e in res["errors"])


def test_validator_detects_comment_in_two_items(source_root, tmp_path):
    out = _mygov_batch(source_root, tmp_path)
    df = pd.read_csv(out / "mygov_batch_v2_annotator_A.csv", dtype=str, keep_default_na=False)
    df.loc[1, "member_comment_ids"] = df.loc[1, "member_comment_ids"] + ";" + df.loc[0, "representative_comment_id"]
    bad = tmp_path / "bad.csv"
    df.to_csv(bad, index=False)
    res = validate_annotations.validate(bad, None)
    assert not res["ok"] and any("more than one item" in e for e in res["errors"])


# ---- annotation schema ------------------------------------------------------

def _row(**kw):
    base = {f: "" for f in S.label_fields("tweets")}
    base.update(kw)
    return base


@pytest.mark.parametrize("row,expect", [
    (_row(stance="Support", confidence="3", needs_review="no", annotator_id="annotator_A", stance_target="metro"), None),
    (_row(stance="Mixed", confidence="2", needs_review="no", annotator_id="a", stance_target="x"), "Mixed"),
    (_row(stance="positive", confidence="2", needs_review="no", annotator_id="a", stance_target="x"), "sentiment"),
    (_row(stance="Unclear", confidence="1", needs_review="no", annotator_id="a", stance_target="x",
          rationale="two readings both plausible"), "unclear_reason"),
    (_row(stance="Support", exclusion_code="OFF_TOPIC", confidence="2", needs_review="no", annotator_id="a",
          stance_target="x", rationale="not about the policy at all"), "exactly one"),
    (_row(stance="Neutral", confidence="2", needs_review="yes", annotator_id="a", stance_target="x",
          rationale="annotator unsure of target"), "needs_review_reason"),
    (_row(stance="Neutral", confidence="2", needs_review="no", annotator_id="a"), "stance_target"),
    (_row(stance="Oppose", confidence="3", needs_review="no", annotator_id="a", stance_target="x"), "rationale"),
    (_row(stance="Support", confidence="5", needs_review="no", annotator_id="a", stance_target="x"), "confidence"),
])
def test_label_row_rules(row, expect):
    problems = S.validate_label_row(row, "tweets")
    if expect is None:
        assert problems == []
    else:
        assert any(expect in p for p in problems), problems


def test_blank_row_is_not_an_annotation():
    assert not S.is_annotated(_row(), "tweets")
    assert S.validate_label_row(_row(), "tweets") == []


# ---- tweet split leakage ----------------------------------------------------

def _frame(rows):
    df = pd.DataFrame(rows, columns=["tweet_row_id", "author_pseudo_id", "tweet_text", "study_split", "annotation_batch",
                                     "month", "exact_text_duplicate_group", "created_at_utc", "script_detected"])
    df["masked_group"] = df.tweet_text.map(lambda t: sha256_text(norm_tweet(t))[:16])
    df["tokens"] = df.tweet_text.map(lambda t: token_set(norm_tweet(t)))
    return df


def test_propose_v2_removes_crossings_and_keeps_locked_test():
    plan = _frame([
        ("1", "A", "the budget is great", "locked_test_300", "test", "m", "", "", "Latin"),
        ("2", "A", "farm laws must go", "train_dev", "main", "m", "", "", "Latin"),          # same author
        ("3", "B", "@x the budget is great", "train_dev", "pilot_200", "m", "", "", "Latin"),  # same masked text
        ("4", "C", "metro line opens soon", "train_dev", "main", "m", "", "", "Latin"),
    ])
    cand = _frame([("5", "D", "who pays for the new bridge", "", "", "m", "", "", "Latin"),
                   ("6", "E", "schools need more teachers now", "", "", "m", "", "", "Latin")])
    assert tweets_split.leakage(plan)["train_dev_rows_affected"] == 2
    v2, changes = tweets_split.propose_v2(plan, cand)
    assert tweets_split.leakage(v2) == {"authors_crossing": 0, "masked_text_groups_crossing": 0,
                                        "near_duplicate_pairs_crossing": 0, "train_dev_rows_affected": 0}
    assert set(v2[v2.study_split == "locked_test_300"].tweet_row_id) == {"1"}
    assert len(v2) == 4 and len(changes) == 2
    assert v2[v2.replaces_tweet_row_id == "3"].annotation_batch.iloc[0] == "pilot_200"


def test_original_selection_is_deterministic(source_root):
    d = tweets_split.load_clean(source_root / "processed" / "kaggle_indian_politics_tweets_clean.csv")
    a, _ = tweets_split.original_selection(d, size=4, test=1, pilot=1)
    b, _ = tweets_split.original_selection(d, size=4, test=1, pilot=1)
    assert a.tweet_row_id.tolist() == b.tweet_row_id.tolist()


# ---- clearance-gated text materialiser ---------------------------------------

TEMPLATE = Path(__file__).resolve().parents[2] / "docs" / "annotation" / "CLEARANCE_RECORD_TEMPLATE.json"
# Synthetic test records only: these values describe no real decision.
FAKE = {"status": "CLEARED", "source": "mygov", "permitted_activities": ["internal_annotation"],
        "decided_by": "Synthetic Test Office", "decision_date": "2000-01-01", "evidence_reference": "synthetic test record"}


def _records(tmp_path, **override):
    paths = []
    for name, dtype in (("rights.json", "rights_permission"), ("ethics.json", "ethics_exemption")):
        p = tmp_path / name
        p.write_text(json.dumps({**FAKE, "decision_type": dtype, **override.get(dtype, {})}), encoding="utf-8")
        paths.append(p)
    return paths


def test_repository_template_is_refused(source_root, tmp_path):
    out = _mygov_batch(source_root, tmp_path)
    with pytest.raises(materialize_text.ClearanceError):
        materialize_text.materialize(out / "mygov_batch_v2_annotator_A.csv", [TEMPLATE, TEMPLATE], tmp_path / "m", source_root)
    tmpl = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    assert tmpl["status"] == "NOT_CLEARED" and not tmpl["decided_by"] and not tmpl["evidence_reference"]


@pytest.mark.parametrize("keep", ["rights_permission", "ethics_exemption"])
def test_materialiser_requires_both_rights_and_ethics_records(source_root, tmp_path, keep):
    out = _mygov_batch(source_root, tmp_path)
    rights, ethics = _records(tmp_path)
    only = rights if keep == "rights_permission" else ethics
    with pytest.raises(materialize_text.ClearanceError, match="ethics" if keep == "rights_permission" else "rights_permission"):
        materialize_text.materialize(out / "mygov_batch_v2_annotator_A.csv", [only], tmp_path / "m", source_root)


def test_materialiser_refuses_uncleared_ethics_or_unknown_type(source_root, tmp_path):
    out = _mygov_batch(source_root, tmp_path)
    paths = _records(tmp_path, ethics_exemption={"status": "PENDING"})
    with pytest.raises(materialize_text.ClearanceError, match="not CLEARED"):
        materialize_text.materialize(out / "mygov_batch_v2_annotator_A.csv", paths, tmp_path / "m", source_root)
    paths = _records(tmp_path, rights_permission={"decision_type": "self_declared"})
    with pytest.raises(materialize_text.ClearanceError, match="decision_type"):
        materialize_text.materialize(out / "mygov_batch_v2_annotator_A.csv", paths, tmp_path / "m", source_root)


def test_materialiser_refuses_placeholder_and_non_ignored_dir(source_root, tmp_path):
    out = _mygov_batch(source_root, tmp_path)
    paths = _records(tmp_path, rights_permission={"decided_by": "TODO"})
    with pytest.raises(materialize_text.ClearanceError, match="placeholder"):
        materialize_text.materialize(out / "mygov_batch_v2_annotator_A.csv", paths, tmp_path / "m", source_root)
    with pytest.raises(materialize_text.ClearanceError, match="gitignored"):
        materialize_text.materialize(out / "mygov_batch_v2_annotator_A.csv", _records(tmp_path), tmp_path / "m", source_root)


def test_materialiser_redacts_and_withholds_manual_items(source_root, tmp_path, monkeypatch):
    out = _mygov_batch(source_root, tmp_path)
    monkeypatch.setattr(materialize_text, "is_gitignored", lambda p: True)
    s = materialize_text.materialize(out / "mygov_batch_v2_annotator_A.csv", _records(tmp_path), tmp_path / "m", source_root)
    df = pd.read_csv(tmp_path / "m" / "mygov_batch_v2_annotator_A_with_text.csv", dtype=str, keep_default_na=False)
    joined = " ".join(df.display_text)
    assert "someone@example.org" not in joined and "[EMAIL]" in joined
    assert s["text_status"]["WITHHELD_PENDING_STEWARD_REDACTION"] == 1
    assert "Ravi" not in joined


RECORD = TEMPLATE.parent / "CLEARANCE_RECORD.json"
MYGOV_CONDITIONS = [
    "Removal of names, usernames, email IDs and other identifiers before annotation.",
    "Aggregate-only publication; no verbatim or identifiable comments.",
    "MyGov/NIC attribution.",
    "No implication of government endorsement.",
    "No third-party sharing of raw or re-identifiable data.",
    "Sending MyGov a copy of the resulting paper/report.",
    "Prior written approval for any scope change.",
]


def test_mygov_record_preserves_conditions_and_invents_no_metadata():
    rec = json.loads(RECORD.read_text(encoding="utf-8"))
    assert rec["decision_type"] == "rights_permission" and rec["status"] == "CLEARED" and rec["source"] == "mygov"
    assert rec["conditions"] == MYGOV_CONDITIONS
    assert rec["full_identifier_review_required"] is True
    assert rec["decision_date"] == "NOT_SUPPLIED"
    assert "internal_annotation" in rec["permitted_activities"]


def test_mygov_record_alone_or_with_ethics_cannot_unblock_text(source_root, tmp_path, monkeypatch):
    out = _mygov_batch(source_root, tmp_path)
    monkeypatch.setattr(materialize_text, "is_gitignored", lambda p: True)
    sheet = out / "mygov_batch_v2_annotator_A.csv"
    with pytest.raises(materialize_text.ClearanceError):
        materialize_text.materialize(sheet, [RECORD], tmp_path / "m", source_root)
    _, ethics = _records(tmp_path)   # even with a (synthetic) ethics record, the missing email date blocks it
    with pytest.raises(materialize_text.ClearanceError, match="decision_date"):
        materialize_text.materialize(sheet, [RECORD, ethics], tmp_path / "m", source_root)


def test_full_identifier_review_requires_steward_text_for_every_item(source_root, tmp_path, monkeypatch):
    out = _mygov_batch(source_root, tmp_path)
    monkeypatch.setattr(materialize_text, "is_gitignored", lambda p: True)
    sheet = out / "mygov_batch_v2_annotator_A.csv"
    paths = _records(tmp_path, rights_permission={"full_identifier_review_required": True})
    ids = pd.read_csv(sheet, dtype=str, keep_default_na=False).item_id.tolist()
    partial = tmp_path / "partial.csv"
    pd.DataFrame({"item_id": ids[:1], "redacted_text": ["Synthetic reviewed text."]}).to_csv(partial, index=False)
    with pytest.raises(materialize_text.ClearanceError, match="identifiers before annotation"):
        materialize_text.materialize(sheet, paths, tmp_path / "m", source_root, partial)
    full = tmp_path / "full.csv"
    pd.DataFrame({"item_id": ids, "redacted_text": [f"Synthetic reviewed text {i} contact a@b.org" for i in range(len(ids))]}
                 ).to_csv(full, index=False)
    s = materialize_text.materialize(sheet, paths, tmp_path / "m2", source_root, full)
    df = pd.read_csv(tmp_path / "m2" / "mygov_batch_v2_annotator_A_with_text.csv", dtype=str, keep_default_na=False)
    assert s["items"] == len(ids) and "WITHHELD_PENDING_STEWARD_REDACTION" not in s["text_status"]
    assert all("steward_reviewed" in a for a in df.redaction_applied) and "a@b.org" not in " ".join(df.display_text)
