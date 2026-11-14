# Mentor review checklist — Indian (MyGov) strand

**For:** the project mentor or supervisor.
**Purpose:**
- check, before submission, that the ethics package is accurate and complete;
- before annotation starts, that every gate is satisfied;
- before publication, that MyGov's conditions are met.

Tick a box only after checking the evidence named beside it. No box is pre-ticked.

## Stage 1 — Before the ethics package is submitted

- [ ] The MyGov clearance record matches the original email. Check the decision sentence, the seven conditions and the described scope ([MYGOV_PERMISSION_CLEARANCE.md](MYGOV_PERMISSION_CLEARANCE.md)).
- [ ] The original email is stored outside git. Its date and any reference have been entered from it into `CLEARANCE_RECORD.json`, not estimated.
- [ ] The scope in [ETHICS_REVIEW_PACKAGE.md](ETHICS_REVIEW_PACKAGE.md) §3 does not exceed what was described to MyGov.
- [ ] Disclosure of prior processing (§6) is complete and accurate.
- [ ] All `[bracketed]` fields are completed from real information: PI, steward, annotators and the incident contact.
- [ ] Out-of-scope sources (tweets, CIVIS, Lok Sabha, sentiment sets) are clearly excluded.
- [ ] Research question and methods are sound. The codebook is still marked PROPOSED, and decisions D1–D6 are listed as open.

## Stage 2 — Before any text is materialised or annotation starts

- [ ] An ethics **approval or exemption** exists in writing, and its record has a real date and reference.
- [ ] The committee's conditions have been added to the plan.
- [ ] A data steward is named, and has reviewed **all 541** items for names, usernames, email IDs and other identifiers (MyGov condition 1).
  - [ ] Spot-check a sample of the steward CSV against the redaction rules.
  - [ ] Confirm the redaction did not remove stance-bearing content.
- [ ] Annotators are named and have signed confidentiality undertakings.
- [ ] Storage and retention decisions are recorded: OneDrive, the backup zip, the deletion date.
- [ ] Codebook decisions D1–D6 are taken and logged in `ANNOTATION_CHANGELOG.md`, and the pilot plan is agreed.
- [ ] The output folder is gitignored, and `git status` shows no text-bearing files.

## Stage 3 — Before any paper, report, poster or slide is shared

- [ ] **Aggregate-only:** no verbatim comment, excerpt, paraphrase close enough to search, username, comment ID or screenshot (condition 2). Check the appendices, figure captions and error-analysis sections too.
- [ ] No small cells that could single out a commenter.
- [ ] MyGov/NIC attribution sentence present (condition 3).
- [ ] Non-endorsement statement present. No MyGov or government logos or branding (condition 4).
- [ ] No raw data, text-bearing files, row-level labels with text, or text-trained models are attached, linked or shared (condition 5).
- [ ] Limitations stated: partial coverage (48.6%), a single consultation, and the 2016 terms unverified.
- [ ] Any change from the approved scope has MyGov's **prior written approval** (condition 7), and ethics re-review if required.
- [ ] After publication: a copy has been sent to MyGov and the date recorded (condition 6).

## Sign-off

| Stage | Mentor | Date | Notes |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |
