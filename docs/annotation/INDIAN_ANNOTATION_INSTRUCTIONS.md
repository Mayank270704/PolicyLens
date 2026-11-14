# Indian annotation batches — instructions (PROPOSED — NOT ADOPTED)

## Current state: annotation cannot start yet

Both batches are **metadata-only**: no comment or tweet text has been copied.

**MyGov:** the **rights permission has been received** (2026-11-14). It is conditional; see [MYGOV_PERMISSION_CLEARANCE.md](MYGOV_PERMISSION_CLEARANCE.md) and [CLEARANCE_RECORD.json](CLEARANCE_RECORD.json). **The tweets remain blocked:** they have no permission evidence.

Before MyGov annotation can start:

1. **Ethics:** an institutional `ethics_approval` or `ethics_exemption` is recorded from a real written decision ([ETHICS_REVIEW_PACKAGE.md](ETHICS_REVIEW_PACKAGE.md)).
2. **Email metadata:** the MyGov email's actual date is entered in `CLEARANCE_RECORD.json`. The gate refuses `NOT_SUPPLIED`.
3. **Identifier review (MyGov condition 1):** a named data steward reviews **all 541** MyGov items, not only the 14 marked `MANUAL_REVIEW`, and supplies `--steward-redactions` covering every item. The gate refuses partial coverage.
4. **Codebook:** decisions D1–D6 (MyGov) or D5 (tweets) are taken.

Do not ask MyGov for the same permission again. Only a scope change needs new written approval.

## Batches (gitignored)

| Batch | Files | Items |
|---|---|---|
| MyGov | `data/annotations/indian/mygov_batch_v2/` with `mygov_batch_v2_annotator_{A,B}.csv`, `..._items.csv`, `manifest.json` | 541: pilot 49, then main 492 |
| Tweets | `data/annotations/indian/tweets_batch_v2/` with `tweets_batch_v2_annotator_{A,B}.csv`, `..._items.csv`, `manifest.json` | 1,500: pilot 200, main 1,000, locked test 300 |

Rows are already in annotation order (`annotation_order`). Do not re-sort.

## Steps once cleared

1. **Add redacted text** to an annotator's sheet:
   ```
   python -m ml.indian_stance.materialize_text --sheet <annotator sheet> \
       --clearance <rights_record.json> --clearance <ethics_record.json> \
       --out-dir data/annotations/indian/<new_folder> [--steward-redactions <reviewed.csv>]
   ```
   This refuses unless both records are CLEARED, and writes only to gitignored folders. `MANUAL_REVIEW` items stay withheld until the steward supplies reviewed text.
2. **Annotate** using the codebook and [ANNOTATOR_DECISION_GUIDE.md](ANNOTATOR_DECISION_GUIDE.md). Fill only the label columns. Never edit item or provenance columns.
3. **Validate** before handing in, and fix every error it reports:
   ```
   python -m ml.indian_stance.validate_annotations <sheet.csv>
   ```
4. **Compute agreement on the pilot**, revise the codebook (log it in `ANNOTATION_CHANGELOG.md`), then continue.
5. **Adjudicate** disagreements. Export **only** adjudicated or agreed labels, in the training format described in `docs/experiments/INDIAN_MODEL_TRAINING_PLAN.md`, with `label_source = human_adjudicated`.

Never share sheets with text outside the annotation team.
