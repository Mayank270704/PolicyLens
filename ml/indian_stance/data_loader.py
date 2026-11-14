"""Source-aware loader for ADJUDICATED HUMAN stance labels. Refuses everything else.

Expected CSV columns (one row per annotation item):
    item_id, source, text, stance, label_source, adjudication_status, annotator_ids, text_group_id
optional:
    author_group_id   leakage group (tweets: pseudonymous author)
    split             'locked_test' for rows of a pre-registered locked test set, else blank
    unclear_reason
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from ml.indian_stance.annotation_schema import SENTIMENT_LIKE_VALUES, STANCE_LABELS

REQUIRED_COLUMNS = ["item_id", "source", "text", "stance", "label_source", "adjudication_status", "annotator_ids",
                    "text_group_id"]
ALLOWED_SOURCES = ("mygov", "tweets")
CONTEXT_ONLY_SOURCES = re.compile(r"civis|lok.?sabha|sentiment140|hinglish|sentimix|hinemo|policylens_sentiment", re.I)
HUMAN_LABEL_SOURCE = "human_adjudicated"
NON_HUMAN_MARKERS = re.compile(r"weak|pseudo|model|predict|ai\b|ai_|llm|gpt|heuristic|sentiment|auto|synthetic|silver", re.I)
ALLOWED_ADJUDICATION = ("adjudicated", "agreed")


class LabelValidationError(ValueError):
    pass


def load_labelled(path: Path, allow_multi_source: bool = False, merge_justification: str = "") -> pd.DataFrame:
    path = Path(path)
    if not path.is_file():
        raise LabelValidationError(f"label file not found: {path}")
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise LabelValidationError(f"missing required columns {missing}; a blank annotation template is not a label file")
    if df.empty:
        raise LabelValidationError("label file has no rows")
    for c in ("author_group_id", "split", "unclear_reason"):
        if c not in df.columns:
            df[c] = ""
    df = df.apply(lambda s: s.str.strip())
    problems: list[str] = []
    blank = df.stance == ""
    if blank.any():
        problems.append(f"{int(blank.sum())} rows have no stance label (genuine human labels are absent)")
    sent = df.stance.str.lower().isin(SENTIMENT_LIKE_VALUES)
    if sent.any():
        problems.append(f"{int(sent.sum())} rows carry sentiment/polarity values {sorted(set(df.stance[sent]))}; "
                        "sentiment is never stance ground truth")
    bad = ~df.stance.isin(STANCE_LABELS) & ~blank & ~sent
    if bad.any():
        problems.append(f"invalid stance labels {sorted(set(df.stance[bad]))}; allowed {list(STANCE_LABELS)}")
    nonhuman = (df.label_source != HUMAN_LABEL_SOURCE) | df.label_source.str.contains(NON_HUMAN_MARKERS)
    if nonhuman.any():
        problems.append(f"{int(nonhuman.sum())} rows have label_source other than '{HUMAN_LABEL_SOURCE}': "
                        f"{sorted(set(df.label_source[nonhuman]))[:5]} (weak, pseudo, model or sentiment labels are refused)")
    adj = ~df.adjudication_status.isin(ALLOWED_ADJUDICATION)
    if adj.any():
        problems.append(f"{int(adj.sum())} rows are not adjudicated/agreed: {sorted(set(df.adjudication_status[adj]))[:5]}")
    n_ann = df.annotator_ids.map(lambda s: len({x for x in s.split(";") if x}))
    if (n_ann < 2).any():
        problems.append(f"{int((n_ann < 2).sum())} rows have fewer than two distinct annotator_ids")
    ctx = df.source.str.contains(CONTEXT_ONLY_SOURCES)
    if ctx.any():
        problems.append(f"context/sentiment-only sources are never stance examples: {sorted(set(df.source[ctx]))}")
    unknown = ~df.source.isin(ALLOWED_SOURCES) & ~ctx
    if unknown.any():
        problems.append(f"unknown sources {sorted(set(df.source[unknown]))}; allowed {list(ALLOWED_SOURCES)}")
    if (df.text == "").any():
        problems.append(f"{int((df.text == '').sum())} rows have empty text")
    if df.item_id.duplicated().any():
        problems.append("duplicate item_id")
    if (df.text_group_id == "").any():
        problems.append("text_group_id is required for every row (duplicate/near-duplicate leakage control)")
    if df.source.nunique() > 1 and not (allow_multi_source and len(merge_justification.split()) >= 5):
        problems.append(f"multiple sources {sorted(df.source.unique())}: merging requires --allow-multi-source and a "
                        "written --merge-justification (>= 5 words); evaluation is then reported per source")
    if problems:
        raise LabelValidationError("training data refused:\n  - " + "\n  - ".join(problems))
    return df
