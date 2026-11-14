# Indian stance project — execution report (2026-11-14)

**Bottom line:** the project is ready to annotate as soon as rights clearance and the codebook decisions are recorded. **No stance label exists, and no model was trained.**

Every figure below comes from a script output or manifest in this repository.

> **Rights update (later on 2026-11-14):** the MyGov "BLOCKED" status in §8 and §12 is **superseded**. MyGov has granted no objection to non-commercial academic research, with seven conditions ([docs/annotation/MYGOV_PERMISSION_CLEARANCE.md](../docs/annotation/MYGOV_PERMISSION_CLEARANCE.md)). Institutional ethics is still pending. The materialiser now also requires steward-reviewed text for **every** MyGov item (condition 1). Tests: 394 passed.

## 1. Work completed

| Phase | Task | Status | Evidence |
|---|---|---|---|
| A | Baseline: workspaces, git state, environment | COMPLETE | `INDIAN_PROJECT_BASELINE.md` |
| A | Verify sources and audit counts | COMPLETE | `INDIAN_DATASET_VERIFICATION.csv`: 56 checks; 53 verified, 3 recorded, 0 discrepancies; all recorded hashes match |
| A | Read the codebook, tweet guidelines and sampling method in full; list reusable assets | COMPLETE | Baseline §3 |
| B | MyGov: duplicates, dedup report, truncation, personal-information review, redaction feasibility, single-consultation limit, pool assessment | COMPLETE | `MYGOV_DATA_QUALITY_REPORT.md`, `data/processed/indian/mygov_quality_v2/` |
| B | Tweets: duplicates, author overlap, reproduce the 1,500-row plan | COMPLETE | `TWEET_DATA_QUALITY_REPORT.md`; plan reproduced exactly |
| B | Tweets: leakage-safe split proposal, locked test unchanged | COMPLETE (PROPOSED) | `TWEET_SPLIT_LEAKAGE_REVIEW.md`; v2 has 0/0/0 crossings, 13 rows replaced |
| B | CIVIS / Lok Sabha kept as context; retrieval issues identified | COMPLETE | Baseline §2; rights report; the loader refuses them |
| C | Codebook review | COMPLETE | `docs/annotation/INDIAN_STANCE_CODEBOOK_REVIEW.md` (14 MyGov and 4 tweet findings) |
| C | Proposed codebook v2, decision guide, change log, tweet stance guide | COMPLETE (PROPOSED — NOT ADOPTED) | `docs/annotation/*` |
| D | MyGov annotation batch | PARTIAL: metadata-only | 541 items with provenance; text gated by rights |
| D | Tweet annotation batch | PARTIAL: metadata-only | 1,500 items from the v2 plan; text gated; needs D5 |
| D | Instructions, manifests and checksums, validator | COMPLETE | `INDIAN_ANNOTATION_INSTRUCTIONS.md`; validator passes all 4 sheets with provenance checked |
| D | Text materialisation with redaction | COMPLETE (code), BLOCKED (use) | `materialize_text.py` refuses without a CLEARED record |
| E | Loader, label validation, group splits, leakage checker, baselines, evaluation, config, versioning | COMPLETE | `ml/indian_stance/*`, `configs/indian_stance/baseline_v1.json` |
| E | Training plan | COMPLETE | `docs/experiments/INDIAN_MODEL_TRAINING_PLAN.md` |
| E | Train a model and report metrics | NOT STARTED (by design) | No adjudicated labels exist |
| F | Provenance and rights record, checklist | COMPLETE (record); all sources BLOCKED or not cleared | `INDIAN_DATA_PROVENANCE_AND_RIGHTS.md`, `INDIAN_SOURCE_RIGHTS_CHECKLIST.csv` |

## 2. Files created

**Code (13):** in `ml/indian_stance/`: `__init__`, `common`, `verify_sources`, `mygov_quality`, `tweets_split`, `annotation_schema`, `build_batches`, `validate_annotations`, `materialize_text`, `data_loader`, `splits`, `train`, `evaluate` (all `.py`).

**Configuration:** `configs/indian_stance/baseline_v1.json`.

**Tests:** `tests/unit/test_indian_data_prep.py`, `tests/unit/test_indian_training.py`.

**Documentation:**
- `docs/annotation/INDIAN_STANCE_CODEBOOK_REVIEW.md`
- `docs/annotation/PROPOSED_INDIAN_STANCE_CODEBOOK_v2.md`
- `docs/annotation/PROPOSED_TWEET_STANCE_GUIDE_v1.md`
- `docs/annotation/ANNOTATOR_DECISION_GUIDE.md`
- `docs/annotation/ANNOTATION_CHANGELOG.md`
- `docs/annotation/INDIAN_ANNOTATION_INSTRUCTIONS.md`
- `docs/annotation/CLEARANCE_RECORD_TEMPLATE.json`
- `docs/experiments/INDIAN_MODEL_TRAINING_PLAN.md`

**Reports:**
- `reports/INDIAN_PROJECT_BASELINE.md`
- `reports/INDIAN_DATASET_VERIFICATION.csv`
- `reports/MYGOV_DATA_QUALITY_REPORT.md`
- `reports/TWEET_DATA_QUALITY_REPORT.md`
- `reports/TWEET_SPLIT_LEAKAGE_REVIEW.md`
- `reports/INDIAN_DATA_PROVENANCE_AND_RIGHTS.md`
- `reports/INDIAN_SOURCE_RIGHTS_CHECKLIST.csv`
- this file

**Derived data (gitignored; IDs, flags and hashes only; each folder has a `manifest.json` with SHA-256 and row counts):**
- `data/processed/indian/mygov_quality_v2/`
- `data/processed/indian/tweets_split_v2/`
- `data/annotations/indian/mygov_batch_v2/`
- `data/annotations/indian/tweets_batch_v2/`

**Superseded runs** (kept, not deleted; each caused by my own bug, fixed before the next run):

| Kept as | Cause |
|---|---|
| `reports/INDIAN_DATASET_VERIFICATION_run1_superseded.csv` | Wrong normalisation definition in one check |
| `data/processed/indian/mygov_quality_v1/` | Truncation measured on cleaned text instead of raw |
| `data/processed/indian/tweets_split_v2_run1_superseded/` | One flag stored as a string |
| `data/annotations/indian/mygov_batch_v2_run1_incomplete_superseded/` | Manifest step failed |

## 3. Files modified

**None of the pre-existing files.** `.gitignore` and `requirements.txt` show as modified from earlier sessions and were not touched today. Nothing was committed.

## 4. Originals preserved

- **The OLD workspace was never written to.** No file under `../dataset` changed during this work (modification-time scan; git status unchanged at 19 untracked entries).
- **Original codebooks, plans and templates are unchanged:** the codebook, tweet guidelines, sampling plan, pilot templates, weak predictions and all source files.
- **Integrity holds:** the recorded hashes still match.

## 5. Tests

- **Before:** 342 passed.
- **After:** **388 passed**, the 46 new tests included. No existing test was modified.
- **Coverage of the new tests:**
  - deduplication and NFKC normalisation;
  - provenance preservation and tamper detection;
  - batch partitioning with no text;
  - schema and label rules (`Mixed`, sentiment values, `unclear_reason`, needs-review, rationale, tweet target);
  - tweet split leakage repair with the locked test kept;
  - deterministic sampling;
  - materialiser refusals and redaction;
  - loader refusals (absent labels, templates, sentiment labels, weak/pseudo/AI label sources, unadjudicated rows, context-only sources, unjustified merges);
  - group-aware splits and locked-test honouring;
  - text and near-duplicate leakage detection;
  - class-floor refusal;
  - reproducibility;
  - single-use test evaluation and data-change refusal;
  - Devanagari tokenisation.
- **Not run:** the OLD workspace's own tests, because running them would write caches into OLD.
- **Real-data checks:** training refused both the real blank MyGov sheet and the weak Sentiment140 predictions, and wrote nothing.
- **Privacy scan of all new tracked files:** no 7-word overlap with any source comment or tweet, apart from the consultation's official title. No emails or phone numbers.

## 6. Verified counts

| Source | Counts |
|---|---|
| MyGov | 560 raw records; 550 unique IDs; 542 exact / **541 normalised** texts; 98 at the 500-character limit; 49 likely truncated; 23 with possible personal information (9 auto-redactable, 14 manual); 1 consultation |
| Tweets | 50,000 rows; 49,569 exact / 49,530 whitespace-case / **48,163 masked** distinct texts; 35,109 authors; plan of 1,500 rows (300 locked test) reproduced exactly; 6 / 2 / 6 author / text / near-duplicate crossings in the original plan |
| CIVIS | 170 (136 + 34); 4 empty |
| Lok Sabha | 150,808 |
| Sentiment140 | 1,600,000 + 498 (quarantined) |
| Weak predictions | 50,000, all marked NOT ground truth (quarantined) |

## 7. Annotation readiness

**Structurally ready:**
- MyGov: 541 items; pilot 49, then main 492.
- Tweets: 1,500 items; pilot 200, main 1,000, locked test 300.
- Validated with provenance, checksummed, and in a fixed annotation order.

**Not yet annotatable:**
- no text has been materialised (rights);
- the codebook and tweet targets are not adopted;
- 14 MyGov items need a steward to redact them.

**Zero annotations exist.** Blank sheets are never counted.

## 8. Rights and provenance blockers

- **MyGov:** BLOCKED. No evidenced permission for research processing or blinded annotation.
- **Tweets:** BLOCKED. No dataset licence verified; X terms apply.
- **CIVIS:** BLOCKED; context use only.
- **Lok Sabha:** partial evidence (CC BY 4.0 declared), not cleared; context use only.

Evidence needed is listed per source in the rights report.

## 9. Training pipeline readiness

- **Executable now, refuses by design.** It runs end to end on synthetic data, and refuses on real data until a `human_adjudicated` label file exists.
- **No metrics exist**, and none are reported.

## 10. Tasks requiring human annotation

- MyGov: the pilot (49), agreement and revision, the main batch (492), and adjudication.
- Tweets: the same order, with the locked test last.
- Steward redaction of the 14 MyGov `MANUAL_REVIEW` items.

## 11. Decisions required from you

| ID | Decision |
|---|---|
| D1 | Four classes: fold `Mixed` into net direction or `Unclear / MIXED` |
| D2 | Off-topic comments become an exclusion, not `Neutral` |
| D3 | One representative per duplicate group |
| D4 | Drop `sentiment` from the stance batch |
| D5 | Tweet stance targets (policy/proposal/initiative/issue; person/party-only tweets excluded?) |
| D6 | Adopt the v2 codebook after the pilot |
| D7 | Adopt the v2 tweet sampling plan |
| D8 | The duplicate pair inside the locked test (tweet rows 6418 and 6545): leave or fix. Fixing changes locked evaluation data. |
| — | Whether to pursue rights clearance (and with whom), and whether merging MyGov with tweets is ever justified |

## 12. Remaining blockers

1. Rights and ethics clearance for MyGov (and tweets).
2. Decisions D1–D8.
3. No human labels.
4. MyGov is a single consultation of about 541 items, so any result is pilot-scale and specific to one policy.
5. No language-identification tool, so the Hinglish share is unknown.
6. Disk: only 8.4 GB free on C:.

## 13. Single highest-value next action

**Obtain and record a written rights and ethics determination that permits internal, blinded annotation of the MyGov comments**, using `docs/annotation/CLEARANCE_RECORD_TEMPLATE.json`.

It is the only external blocker between this prepared pipeline and the project's first genuine human stance labels. Decisions D1–D4 can be taken alongside it. Then materialise the text, run the 49-item MyGov pilot with two annotators, and measure agreement.
