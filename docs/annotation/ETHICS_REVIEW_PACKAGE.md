# Ethics review package — PolicyLens: stance annotation of MyGov consultation comments

**For:** the institutional ethics body (and its data protection or legal office, if it requires one).
**Prepared:** 2026-11-14.
**Status:** READY FOR SUBMISSION. **Not submitted, not decided.**
**What we ask for:** an ethics **approval** or **exemption** decision, with any conditions, for the activities in §3.

Fields in `[square brackets]` are for the PI to complete. Nothing has been filled in by assumption.

## 1. Project summary

| Item | Detail |
|---|---|
| Project | PolicyLens: automatic stance classification of public comments on government policy proposals |
| PI / supervisor | [name, department] / [mentor name] |
| Funding | [none / funder]. Non-commercial. |
| Research question | Can a classifier reliably label whether a public comment supports, opposes, is neutral towards, or takes an unclear position on a specific policy proposal? |
| Data in scope | 550 unique public comments (541 after normalisation) on the MyGov consultation "Government Open Data Use License – India" (2016). They were saved from the public static archive in May 2026 and cover about 48.6% of the 1,132 displayed submissions. |
| Out of scope for this application | Kaggle Indian politics tweets, CIVIS, Lok Sabha Q&A and sentiment corpora. These are not cleared and not covered here. |

## 2. Rights-holder decision already obtained

MyGov replied with **no objection** to use for non-commercial academic research, subject to seven conditions. Full record: [MYGOV_PERMISSION_CLEARANCE.md](MYGOV_PERMISSION_CLEARANCE.md).

1. Removal of names, usernames, email IDs and other identifiers before annotation.
2. Aggregate-only publication; no verbatim or identifiable comments.
3. MyGov/NIC attribution.
4. No implication of government endorsement.
5. No third-party sharing of raw or re-identifiable data.
6. Sending MyGov a copy of the resulting paper/report.
7. Prior written approval for any scope change.

**Known gap in the evidence:** the reply's sender, date and reference number were not supplied with the transcribed text. The PI will provide the original email to the committee: [attach email / location].

MyGov's permission addresses use of the platform content. **It does not decide the ethical questions in §5.**

## 3. Activities for which a decision is requested

| # | Activity | Who | Data seen |
|---|---|---|---|
| A | Local processing (cleaning, counting, de-duplication, quality flags) | PI | Raw saved pages (already done; disclosed in §6) |
| B | Identifier review and redaction of **all** comments before annotation | Named data steward [name] | Raw comment text |
| C | Blinded stance annotation by two independent annotators, then adjudication | [annotator A], [annotator B], [adjudicator] | Steward-redacted text only |
| D | Training and evaluating research models internally on anonymised labels | PI | Redacted text and labels |
| E | Publishing aggregate results (counts, agreement, metrics) with attribution and a non-endorsement statement | PI | — |

**Not requested:** publishing comments or excerpts; releasing data, labels with text, or models trained on the text; commercial use; adding other sources. Each would need MyGov's prior written approval (condition 7) and fresh ethics review.

## 4. Participants and data subjects

- **Data subjects:** members of the public who commented on MyGov in 2016. They are not contacted, and no new data is collected from them.
- **Consent:** commenters did not consent to this research. The 2016 submission terms are unverified.
- **Personal data present:**
  - usernames in the raw pages (483);
  - possible personal information in 23 comments: 2 emails, 3 phone-like numbers, 11 URLs and 14 sign-offs or "on behalf of" lines;
  - names possibly elsewhere in running text, which cannot be detected automatically.
- **Sensitive categories:** none expected (the topic is a data-licence policy). The steward will flag any that appear.
- **Re-identification:** the full text is searchable in the public archive, so any verbatim quote identifies its author. No quotes will be published.
- **Annotators:** members of the research team. The work is low risk, the content is a policy topic, and there is no distressing material expected.

## 5. Questions for the committee

1. Is this human-subjects research or personal-data processing that needs approval? Or does it qualify for exemption?
2. Is MyGov's permission, together with the safeguards below, sufficient without notifying commenters or obtaining their consent?
3. Is OneDrive-synced storage acceptable? If not, where must the data be held?
4. What retention period applies to the raw pages, the extracted text, the annotations and the models? What deletion procedure, including for the 4.1 GB `dataset.zip` backup?
5. May labels and models derived from the text be kept after the text is deleted?
6. Is any remedial step needed for the processing already done (§6)?
7. Are there conditions beyond MyGov's on publication? For example, a minimum cell size for aggregate tables.

## 6. Processing already done (disclosed)

- **Done:** pages were saved in May 2026 and text extracted offline. Counts, de-duplication, quality and personal-information flags were produced, and an exploratory topic-grouping experiment was run in the earlier workspace.
- **Not done:** **no comment has been annotated, published or shared.** The PolicyLens repository holds IDs, flags and hashes only. All annotation sheets are metadata-only.

## 7. Safeguards

| Area | Safeguard | Enforced by |
|---|---|---|
| Gate | No comment text reaches an annotation sheet without two recorded decisions: (1) MyGov's rights permission and (2) this committee's approval or exemption. A missing record, an uncleared status, a placeholder or an invalid date is refused. | `ml/indian_stance/materialize_text.py` (tested) |
| Identifiers (MyGov condition 1) | A steward reviews **every** item. The tool refuses unless reviewed text covers all items. Automatic placeholders are then also applied for emails, phones, ID numbers and URLs. | Code and steward |
| Minimisation | No usernames or author fields in annotation sheets. Pseudonymous item IDs. | Code |
| Blinding | Annotators see no model outputs, clusters, weak labels or each other's sheets. | Procedure and sheet design |
| Access | Named team only, under confidentiality undertakings [to be signed] | Procedure |
| Version control | Text-bearing outputs may only be written to gitignored folders | Code |
| Labels for training | Only human-adjudicated labels. Never AI, weak or pseudo labels. | `ml/indian_stance/data_loader.py` (tested) |
| Publication | Aggregate only. MyGov/NIC attribution. A non-endorsement statement. A copy sent to MyGov. A mentor pre-publication check ([MENTOR_REVIEW_CHECKLIST.md](MENTOR_REVIEW_CHECKLIST.md)). | Procedure |
| Incidents | Report to [ethics office contact] and the PI within [period set by the institution] | Procedure |

## 8. Attachments

- [MYGOV_PERMISSION_CLEARANCE.md](MYGOV_PERMISSION_CLEARANCE.md), plus the original MyGov email [PI to attach]
- [ETHICS_REVIEW_CHECKLIST.md](ETHICS_REVIEW_CHECKLIST.md): item-by-item controls
- [reports/INDIAN_DATA_PROVENANCE_AND_RIGHTS.md](../../reports/INDIAN_DATA_PROVENANCE_AND_RIGHTS.md)
- [reports/MYGOV_DATA_QUALITY_REPORT.md](../../reports/MYGOV_DATA_QUALITY_REPORT.md) (counts only, no text)
- [PROPOSED_INDIAN_STANCE_CODEBOOK_v2.md](PROPOSED_INDIAN_STANCE_CODEBOOK_v2.md) (proposed, not adopted)
- An annotator confidentiality undertaking [institution template]

## 9. Recording the decision (internal)

When the written decision arrives, transcribe it into a **new** clearance record with:

- `decision_type` = `ethics_approval` or `ethics_exemption`;
- `decided_by` = the committee;
- `decision_date` and `evidence_reference` = the actual date and reference;
- `conditions` = the committee's conditions, verbatim.

Store the record outside git. Never fill these fields in advance.
