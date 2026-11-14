# MyGov permission — clearance record (RECEIVED, CONDITIONAL)

**Decision:** MyGov has **no objection** to the use of the 2016 "Government Open Data Use License – India" consultation comments for **non-commercial academic research**, subject to seven conditions.

**Status:** `rights_permission` = **CLEARED WITH CONDITIONS** (recorded 2026-11-14).
**Do not re-request this permission.** The draft request letter ([MYGOV_PERMISSION_REQUEST.md](MYGOV_PERMISSION_REQUEST.md)) is superseded.

**Institutional ethics is a separate decision and is still PENDING.** Comment text stays blocked until it is documented ([ETHICS_REVIEW_PACKAGE.md](ETHICS_REVIEW_PACKAGE.md)).

Machine-readable record: [CLEARANCE_RECORD.json](CLEARANCE_RECORD.json).

## 1. Evidence

| Item | Value |
|---|---|
| Evidence form | Text of MyGov's reply email, supplied by the researcher in the PolicyLens working session of 2026-11-14 |
| Decision sentence (verbatim) | "Based on the details you've shared, we have no objection to their use for non-commercial academic research, subject to the following conditions." |
| Scope described to MyGov | Internal blinded annotation, anonymised labels, and research/ML experiments |
| Sender name | **Not supplied** |
| Sender office / designation | **Not supplied** |
| Sender email address | **Not supplied** |
| Email date | **Not supplied** |
| Reference / ticket number | **Not supplied** |
| Original email file | **Not supplied.** No copy was found in either workspace (searched 2026-11-14 for the decision sentence and for `.eml`/`.msg` files). |

None of these fields has been inferred or filled in. The PI should save the original email (for example as `.eml` or PDF) in access-controlled storage **outside git**, then enter the actual date and reference into `CLEARANCE_RECORD.json`.

## 2. Conditions (exact wording as supplied)

1. Removal of names, usernames, email IDs and other identifiers before annotation.
2. Aggregate-only publication; no verbatim or identifiable comments.
3. MyGov/NIC attribution.
4. No implication of government endorsement.
5. No third-party sharing of raw or re-identifiable data.
6. Sending MyGov a copy of the resulting paper/report.
7. Prior written approval for any scope change.

## 3. How each condition is met

| # | Condition | Existing control | Still to do | Owner |
|---|---|---|---|---|
| 1 | Identifiers removed before annotation | Usernames are not in the annotation sheets. The regex redaction covers emails, phones, ID numbers and URLs. The 14 sign-off items are withheld. **New:** `materialize_text.py` now refuses to add text unless a steward has supplied reviewed text for **every** item, because names in running text cannot be detected automatically (`full_identifier_review_required: true`). | A named data steward reviews all 541 items, not only the 14 flagged ones, and supplies the `--steward-redactions` CSV. | Data steward |
| 2 | Aggregate-only publication | Published outputs are counts, agreement and metrics only. The error-analysis templates use IDs, not text. | Strip any quoted comment from drafts. Pre-publication check (see [MENTOR_REVIEW_CHECKLIST.md](MENTOR_REVIEW_CHECKLIST.md)). | PI / mentor |
| 3 | MyGov/NIC attribution | — | Add an attribution sentence to every paper, report and slide deck. | PI |
| 4 | No implied endorsement | — | Add a disclaimer: "MyGov/NIC permitted use; they do not endorse the findings." Do not use the MyGov logo or branding. | PI |
| 5 | No third-party sharing | Data and annotation folders are gitignored. Nothing has been published. | Do not share the raw data, the text-bearing sheets or a model trained on text with anyone outside the named team. Check the OneDrive sharing settings. | PI |
| 6 | Copy to MyGov | — | Send the final paper/report to MyGov and record the date sent. | PI |
| 7 | Scope changes need prior written approval | The scope is recorded in `CLEARANCE_RECORD.json`. | **Anything beyond the described scope needs MyGov's prior written approval:** releasing labels with text, adding new sources, sharing a model trained on text, commercial use, or using the comments beyond this research. | PI |

## 4. What this does and does not unblock

| Activity | Status |
|---|---|
| Local processing of IDs, counts and flags | Permitted (as before) |
| Adding comment text to annotation sheets | **Blocked.** Needs the ethics decision, the email date, and the full steward review. |
| Annotation | **Blocked** for the same reasons. Codebook decisions D1–D6 are also still open. |
| Training on MyGov labels | **Blocked.** No human labels exist yet. |
| Publication | Aggregate only, after conditions 3, 4 and 6 are met |
| Tweets, CIVIS, Lok Sabha | **Not covered.** This permission is for MyGov comments only. |
