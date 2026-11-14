# Indian stance project — baseline (2026-11-14)

**Status:** COMPLETE. This file contains no comment or tweet text.

## 1. Workspaces

| | NEW workspace (this repository) | OLD workspace (source data, read-only) |
|---|---|---|
| Location | `PolicyLens/` | `../dataset/` (sibling folder); Indian sources in `../dataset/indian/` |
| Git HEAD | `b00a615` (2026-11-08, "Update PolicyLens project") | `37642a3` (2026-10-30) |
| State before this work | Uncommitted Canadian-project work: `.gitignore`, `requirements.txt` modified; 13 untracked files (protocol proposals v1–v6, Level 1 error analysis, three stance experiments and their tests) | 0 tracked files modified, 19 untracked entries. Only 18 code files under `indian/` are tracked; **all Indian data is untracked**. |
| Role | All new code, reports and derived outputs | Read only. No file was written. `git status` was run with `--no-optional-locks`, so no index write. |

**How sources are found:** code locates `indian/` through `--source-root`, or the environment variable `POLICYLENS_INDIAN_SOURCE_ROOT`, or the default `../dataset/indian` relative to this repository. No absolute path is hard-coded. Manifests label files `OLD:<path>` and `NEW:<path>`.

**Environment:** Python 3.13.7; pandas 3.0.5; pyarrow 24.0.0; scikit-learn 1.9.0; numpy 2.5.3. No language-identification library is installed. 8 GB RAM.

**Disk space:** only **8.4 GB free** on C: (98% used). Nothing large was copied, and `dataset.zip` was not extracted.

**Existing tests before any change:** 342 passed.

## 2. Indian sources located

All paths are relative to `OLD:indian/`.

| Source | Role | Key files |
|---|---|---|
| MyGov (2016 Government Open Data Use License consultation) | Consultation comments; the only Indian comment source | `processed/mygov_comments_{raw,clean}.csv`, `mygov_pii_review_flags.csv`, `mygov_page_inventory.csv`, `mygov_extraction_summary.json`, `processed/mygov/annotation_v1/*`, `reports/mygov_annotation_codebook_v1.md` |
| Kaggle Indian politics tweets | Social-media posts; a separate source | `kaggle/.../tweets.csv`, `processed/kaggle_indian_politics_tweets_clean.csv`, `processed/tweets/annotation_v1/*`, `reports/tweets_annotation_guidelines_v1.md` |
| Weak tweet sentiment predictions | **Quarantined** model output | `processed/tweets/weak_labels_sentiment140_v1/*` |
| CIVIS | Policy documents and summaries; retrieval/context only | `huggingface_datasets/civis_consultation_summaries/*.json`, `processed/civis_policy_documents_clean.csv`, `processed/retrieval/civis_v1/*` |
| Lok Sabha Q&A | Parliamentary Q&A; retrieval/context only | `huggingface_datasets/lok-sabha-qa/*.parquet`, `processed/lok_sabha_qa_clean.parquet`, `processed/lok_sabha_qa_metadata.csv` |
| Sentiment140 | **Quarantined**, sentiment only | `OLD:trainingandtestdata/*.csv` |
| Rights and provenance evidence | Phase F input | `reports/source_rights_corpus_freeze_audit_v1/source_rights_audit.md`, `reports/institutional_review_package_v1/*` |

Counts are verified in [INDIAN_DATASET_VERIFICATION.csv](INDIAN_DATASET_VERIFICATION.csv): 56 checks, of which 53 VERIFIED, 3 RECORDED (no expected value) and 0 discrepancies. All recorded SHA-256 hashes that exist match.
- **Superseded first run:** an earlier run, kept as `INDIAN_DATASET_VERIFICATION_run1_superseded.csv`, showed one false discrepancy. My check had defined "normalised tweet text" differently from the audit. I fixed the check, not the expectation, and now report both definitions: 49,530 distinct texts using whitespace and case only, and 47,486 once @mentions and URLs are also removed.

## 3. Existing assets reused

| Asset | How it is reused |
|---|---|
| OLD clean MyGov and tweet files, page inventory, extraction summary | Read-only inputs for every new calculation |
| OLD personal-information and truncation regexes (`process_indian_datasets.py`, `extract_mygov_comments.py`) | Copied verbatim into `ml/indian_stance/common.py`. Recomputed flags agree with the recorded flags for 550/550 comments. |
| OLD MyGov annotation templates v1 | `annotation_batch` (pilot_50/main) and `clause_numbers_detected` are carried into the new batch as metadata |
| OLD MyGov codebook v1 and tweet guidelines v1 | Reviewed in full; the basis for the proposed v2 codebook (unchanged originals) |
| OLD tweet sampling algorithm (`run_tweets_analysis_v1.py:annotation`) | Re-implemented and **reproduced exactly**: same 1,500 IDs, order, splits and batches. Its locked test set is kept unchanged. |
| OLD source-rights audit and institutional review package | Primary evidence for the rights report |
| OLD retrieval evaluation audit | Source of the CIVIS and Lok Sabha retrieval-quality issues |
| NEW Canadian-project lessons | No stop-word removal, since it deletes negations; group-aware splits; validation-only selection; single-use test; confidence recorded separately from needs-review |

**Not reused, and why:**
- **The PolicyLens annotation GUI** (`scripts/annotation/gui.py`): it writes resume, timing and audit state into the *Canadian* experiment's files, which would contaminate them.
- **The OLD agreement script** (`scripts/analyze_annotation_agreement.py`): it can be adapted for MyGov kappa once labels exist (not started).
