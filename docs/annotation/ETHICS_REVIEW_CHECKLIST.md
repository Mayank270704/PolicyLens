# Ethics review checklist — MyGov comment annotation (OPEN; ethics not yet decided)

> **Update 2026-11-14:** MyGov's **rights permission has been RECEIVED.** It grants no objection to non-commercial academic research, with seven conditions (see [MYGOV_PERMISSION_CLEARANCE.md](MYGOV_PERMISSION_CLEARANCE.md)). Those conditions are now **binding minimums** in sections C, F and G. **Institutional ethics approval or exemption is still PENDING.** The package for the ethics body is [ETHICS_REVIEW_PACKAGE.md](ETHICS_REVIEW_PACKAGE.md).
>
> **Status: OPEN.** No ethics item below is approved, exempted or waived. Each box is ticked only when a **written** decision exists, with its reference recorded. The "Current state" column describes what the code already does: it is a researcher control, not an approval.
>
> **Companion documents:**
> - [MYGOV_PERMISSION_CLEARANCE.md](MYGOV_PERMISSION_CLEARANCE.md) (rights holder decision, received). The earlier request draft [MYGOV_PERMISSION_REQUEST.md](MYGOV_PERMISSION_REQUEST.md) is superseded.
> - [reports/INDIAN_DATA_PROVENANCE_AND_RIGHTS.md](../../reports/INDIAN_DATA_PROVENANCE_AND_RIGHTS.md)
> - `OLD:indian/reports/institutional_review_package_v1/rights_and_privacy_questions.md` (earlier question set, reused)

## 1. Who decides what

| Party | Decides | Cannot decide | Recorded as |
|---|---|---|---|
| **MyGov / MeitY / NIC** (platform, publisher) | Whether its terms permit reuse of the 2016 submissions; whether it can authorise uses A–D; any conditions | Institutional ethics; whether commenters' own rights are satisfied, if MyGov says it can't authorise | Clearance record `decision_type = rights_permission` |
| **Institutional ethics body** (and data protection or legal office if the institution requires it) | Whether review is required; approval or exemption; conditions on redaction, access, retention, publication | Platform permission or copyright | Clearance record `decision_type = ethics_approval` or `ethics_exemption` |
| **Researchers** (PI, data steward, annotators) | Nothing on the above. They implement the controls, document them, and stop when a decision is missing. | Granting themselves permission or exemption | Researcher sign-off in §3, against the written decisions |

**Both clearance records are required** before `ml/indian_stance/materialize_text.py` will show any text. One without the other is refused, and so is a template or a record containing placeholders.

## 2. Checklist

### A. Review scope (ethics body)
- [ ] Decide whether stance annotation of public consultation comments is human-subjects research or personal-data processing requiring review, and record approval or exemption.
- [ ] Decide whether commenters must be notified, or whether the absence of their consent is acceptable for these uses.
- [ ] Decide whether the disclosed earlier processing (extraction, flagging, exploratory grouping) needs any remedial step.

### B. Internal blinded annotation
| Requirement | Current state | Approved? |
|---|---|---|
| Named annotators only (two, independent), plus a separate adjudicator | Annotator sheets for A and B exist; names are not yet recorded | [ ] |
| Confidentiality undertaking signed by each annotator | None exists | [ ] |
| Blinding: no model outputs, clusters, weak labels or the other annotator's sheet | Sheets contain none of these; the rule is in the decision guide | [ ] |
| Annotators see redacted text only | Enforced by `materialize_text.py` | [ ] |
| Annotators never copy names or contact details into fields | Rule in the codebook; free-text `rationale` only | [ ] |

### C. Personal-information redaction
| Requirement | Current state | Approved? |
|---|---|---|
| Automatic placeholders for emails, phone-like numbers, Aadhaar/PAN-like numbers and URLs | Implemented; 9 comments are fully handled this way | [ ] |
| Manual redaction of sign-offs / "on behalf of" (names, organisations) | 14 comments **withheld** until a steward supplies reviewed text | [ ] |
| **MyGov condition 1:** names, usernames, email IDs and other identifiers removed **before annotation**, in **all** items | `materialize_text.py` refuses to proceed unless steward-reviewed text covers all 541 items | [ ] |
| A named data steward who performs and checks the redactions | Not named | [ ] |
| A check that redaction does not remove stance-bearing content | Must be done by the steward; code can only report span positions | [ ] |
| Usernames excluded | The clean file and batches hold none; the **raw** OLD files still contain 483 usernames | [ ] |

### D. Access controls and storage
| Requirement | Current state | Approved? |
|---|---|---|
| Storage location acceptable | **All copies sit in OneDrive-synced folders:** the OLD workspace (`Desktop\dataset`), a 4.1 GB `dataset.zip` backup on the Desktop, and this repository. Third-party cloud sync is in effect. | [ ] |
| Text-bearing files kept out of version control | Enforced: outputs must be gitignored, and the batches are metadata-only | [ ] |
| Who may access the raw files | Not defined | [ ] |
| Encryption at rest, and device security | Not defined | [ ] |
| Incident response (loss or exposure) | Not defined | [ ] |

### E. Retention and deletion
| Requirement | Current state | Approved? |
|---|---|---|
| A retention period for raw HTML, extracted comments, annotations and derived models | None set | [ ] |
| Deletion procedure, including the backup zip and cloud copies | None set | [ ] |
| Whether labels and models trained on the text may be kept after the text is deleted | Not decided | [ ] |

### F. Anonymisation and pseudonymisation
| Requirement | Current state | Approved? |
|---|---|---|
| Recognise the limit: verbatim text is searchable in the public archive, so any quoted text is re-identifiable | Documented here; no quotes are planned | [ ] |
| Item IDs (`MYG2-…`) are pseudonymous, but the provenance columns map them to MyGov comment IDs | Mapping kept for traceability; restricted access needed | [ ] |
| Re-identification risk of aggregate tables (small cells) | Not assessed | [ ] |

### G. Publication restrictions
| Proposed restriction | Approved? |
|---|---|
| Publish aggregate statistics and methodology only | [ ] |
| No verbatim comments, excerpts, usernames, comment IDs or screenshots | [ ] |
| No release of row-level labels, text-bearing datasets, embeddings, or models trained on the text, unless separately approved (models can memorise text) | [ ] |
| Report the partial (48.6%, most recent half) and single-consultation limitations in every output | [ ] |
| **MyGov conditions 2–6 (binding):** aggregate-only; MyGov/NIC attribution; no implied endorsement; no third-party sharing of raw or re-identifiable data; send MyGov a copy | [ ] (researcher compliance) |

## 3. Researcher responsibilities (sign-off; not an approval)

The PI and steward confirm, in writing, that they will:
- [ ] Keep text materialisation blocked until **both** clearance records exist, each transcribed from a real written decision and stored outside git.
- [ ] Never enter invented or anticipated evidence, dates, decision-makers or references in any clearance record.
- [ ] Apply every condition imposed by either decision, and record it in `conditions`.
- [ ] Leave the original source files unmodified.
- [ ] Report any incident to the ethics body.
- [ ] Obtain MyGov's prior written approval before any scope change (MyGov condition 7), and re-seek ethics approval as the ethics body requires.

## 4. Decisions and outstanding approvals (updated 2026-11-14)

| # | Approval | From | Status |
|---|---|---|---|
| 1 | Permission for non-commercial academic research: internal blinded annotation, anonymised labels, research/ML experiments | MyGov | **RECEIVED: no objection, with 7 conditions** ([MYGOV_PERMISSION_CLEARANCE.md](MYGOV_PERMISSION_CLEARANCE.md)). Email date, sender and reference not supplied; original email to be stored outside git. **Do not re-request.** |
| 2 | Whether commenters' own authorisation is also required | Institutional ethics / legal | Pending; for the ethics body to consider alongside MyGov's permission |
| 3 | Ethics approval or exemption, with conditions | Institutional ethics body | **PENDING** (package ready: [ETHICS_REVIEW_PACKAGE.md](ETHICS_REVIEW_PACKAGE.md)) |
| 4 | Storage decision: is OneDrive-synced storage acceptable, or must data be moved? | Institution (ethics / data protection) | Pending |
| 5 | Retention and deletion schedule, including backups | Institution | Pending |
| 6 | Publication scope | MyGov has fixed it as **aggregate-only**; the institution may add to this | Minimum set by MyGov; any further institutional conditions pending |
| 7 | Named data steward; identifier review of **all 541** items (MyGov condition 1) | Researchers (after 3) | Not started |
| 8 | Annotator confidentiality undertakings | Researchers / institution | Not started |
