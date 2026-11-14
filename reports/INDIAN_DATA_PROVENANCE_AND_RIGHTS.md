# Indian data — provenance and rights (2026-11-14)

**Status:** COMPLETE, as a record of evidence. This is not legal advice, and no permission is assumed.

> **Update 2026-11-14 — MyGov rights permission received.** MyGov has no objection to non-commercial academic research, under seven conditions ([docs/annotation/MYGOV_PERMISSION_CLEARANCE.md](../docs/annotation/MYGOV_PERMISSION_CLEARANCE.md)). MyGov's status below changes from BLOCKED to **RIGHTS CLEARED (conditional); ETHICS PENDING**. Every other source is unchanged and **not cleared**.

**Evidence base:**
- local files;
- the project's own `OLD:indian/reports/source_rights_corpus_freeze_audit_v1/source_rights_audit.md` (checked 2026-10-15, including the primary pages it reviewed online);
- `OLD:indian/reports/institutional_review_package_v1/*`;
- the MyGov page inventory and extraction summary;
- licence files found locally.

**No new external verification was done today.** Anything not evidenced locally or in that audit is **UNVERIFIED**. The machine-readable checklist is [INDIAN_SOURCE_RIGHTS_CHECKLIST.csv](INDIAN_SOURCE_RIGHTS_CHECKLIST.csv).

## 1. Source by source

### MyGov comments — status: **RIGHTS CLEARED WITH CONDITIONS (2026-11-14); ETHICS PENDING; text still blocked**
- **MyGov decision:** "no objection to their use for non-commercial academic research, subject to the following conditions":
  1. removal of identifiers before annotation;
  2. aggregate-only publication;
  3. MyGov/NIC attribution;
  4. no implied endorsement;
  5. no third-party sharing;
  6. a copy to MyGov;
  7. prior written approval for scope changes.

  The exact wording is in the clearance document. The sender, date and reference were not supplied.
- *The pre-decision evidence below is kept for the record.*
- **Origin:** MyGov.in consultation "Government Open Data Use License – India" (2016). The saved pages point to the static archive `static.mygov.in/archive/mygov/en/public/group-issue/public-consultation-government-open-data-use-license-india/`.
- **Collection:** an HTTrack mirror of 56 HTML pages (page indices 0–54 plus one duplicate file), mirrored **2026-05-06/08**. 560 records were extracted offline, giving 550 unique comments. Pages 55 onward were never saved.
- **Licence / terms evidence:**
  - The current MyGov Terms prohibit copying or republishing without permission.
  - The current MyGov copyright policy **excludes user-submitted content** from its general reproduction permission.
  - The GODL-India licence (Gazette dated 2017-02-10) covers eligible government data and excludes personal information. It does **not** license these 2016 comments.
  - The terms in force in 2016, and any consent notice shown to submitters, are **UNVERIFIED**.
- **Can it be redistributed?** **No evidence of permission.** Treat it as not permitted.
- **Is research use supported?** **UNVERIFIED.** The audit lists confirmation that research processing *and blinded annotation* are permitted as *needed*.
- **Privacy:** the comments are third-party; the raw files include 483 usernames; 23 comments flag possible personal information (2 emails, 3 phone-like numbers, 11 URLs, 14 sign-offs).

### Kaggle Indian politics tweets — status: **BLOCKED**
- **Origin:** probably Kaggle `adritpal08/dataset-of-indian-politics-tweets-and-reactions`, but only the folder name and a third-party reference support this. The content belongs to X/Twitter users.
- **Collection:** a downloaded CSV. The collection method, Kaggle version, retrieval date and licence field were **not recorded**. Tweet dates run 2022-10-15 to 2023-03-29. There are no tweet IDs.
- **Licence / terms evidence:** no dataset licence was verified (the Kaggle page's licence metadata was unreadable during the audit). The current X terms prohibit scraping without consent, and users retain rights to their posts. **UNVERIFIED.**
- **Can it be redistributed?** No evidence of permission.
- **Is research use supported?** **UNVERIFIED.**
- **Privacy:** the raw file holds user handles. The clean file uses pseudonymous IDs but still keeps the original text. Deletion requests can't be honoured without tweet IDs.

### CIVIS documents and summaries — status: **BLOCKED** (context source only)
- **Origin:** probably Hugging Face `gaurikapse/civis-consultation-summaries` (listing updated 2022-09-04). Item-level publishers are not identified.
- **Collection:** JSON files downloaded locally (136 train + 34 test). There is no card, revision, or download record.
- **Licence / terms evidence:** the HF metadata says `other`, with no readable terms. Who wrote the summaries, and under what rights, is unknown. **UNVERIFIED.**
- **Can it be redistributed?** Not evidenced. **Research use?** UNVERIFIED.
- **Privacy:** government documents, with incidental content unreviewed.

### Lok Sabha Q&A — status: **PARTIAL EVIDENCE, NOT CLEARED** (context source only)
- **Origin:** probably Hugging Face `opensansad/lok-sabha-qa` (Sammit Jain / OpenSansad), sourced from Digital Sansad PDFs.
- **Collection:** five downloaded Parquet shards, 150,808 rows, dated 2015-07-21 to 2026-04-02. The exact revision is not pinned.
- **Licence / terms evidence:** the current HF card declares **CC BY 4.0** for the dataset. The Digital Sansad terms give no explicit reuse licence for the underlying text, so the rights chain is UNVERIFIED.
- **Can it be redistributed?** CC BY 4.0 if the declaration covers the text. **Research use?** Plausible under CC BY, but not confirmed.
- **Integration:** the OLD integration manifest shows the gate failed (`integration_blocked_pending_rights_review`). It is not a stance source in any case.
- **Privacy:** MPs' names appear in their public roles.

### Sentiment140 — status: **QUARANTINED** (not a project source)
- **Origin:** the Sentiment140 corpus (2009 English tweets, polarity 0/4), in `OLD:trainingandtestdata/`. There is no local licence or README, so the terms are **UNVERIFIED**.
- **Role:** sentiment only; **never** stance ground truth. The weak tweet predictions derived from it are quarantined too.

### Other sentiment and emotion sets — status: **QUARANTINED**
- **HinEmo-9** (`OLD:hinemo9-v1.0.1/`):
  - What it is: 30,436 YouTube comments labelled for nine *emotions*.
  - Licence: a local LICENSE file contains **CC BY 4.0**. This is the only source with a local licence file.
  - Role: emotion, not stance.
- **SentiMix-Hindi-English** (`OLD:SentiMix-Hindi-English-main/`):
  - What it is: a third-party repository built for a Kaggle sentiment competition.
  - Licence: no local licence, so **UNVERIFIED**.
  - Role: sentiment only.
- **`PolicyLens_Hindi_English_Hinglish_Sentiment.csv`**:
  - What it is: 2,500 generic Devanagari sentences with sentiment labels; 2 sentences carry conflicting labels.
  - Licence: **provenance unknown**.
  - Role: sentiment only.

## 2. What this work did under these constraints

- **Read, didn't copy.** Local files were read for counts, hashes and flags only. **No comment or tweet text was copied** into this workspace, and every derived output is IDs, flags and hashes in gitignored folders.
- **Batches are metadata-only.** Redacted text is added only by `materialize_text.py`, and only against **two** recorded CLEARED decisions: a `rights_permission` and an `ethics_approval`/`ethics_exemption` (template: `docs/annotation/CLEARANCE_RECORD_TEMPLATE.json`; see `docs/annotation/MYGOV_PERMISSION_REQUEST.md` and `docs/annotation/ETHICS_REVIEW_CHECKLIST.md`).
- **Nothing published.** Nothing was published, shared or sent, and no permission request was made.

## 3. Evidence needed to unblock

| Source | Needed |
|---|---|
| MyGov | ~~Written confirmation from MyGov~~ **received 2026-11-14.** Still needed:<br>• an institutional ethics approval or exemption ([ETHICS_REVIEW_PACKAGE.md](../docs/annotation/ETHICS_REVIEW_PACKAGE.md));<br>• the original email's date and reference, stored outside git;<br>• a steward identifier review of all 541 items;<br>• storage and retention decisions. |
| Tweets | A snapshot of the Kaggle page showing the owner, version and licence; the uploader's authority to distribute X content; the applicable X terms or research agreement; a retention/deletion plan. |
| CIVIS | The pinned HF revision matching the local hashes; readable terms behind `other`; the provenance of the summaries. Needed only if it is used beyond local retrieval. |
| Lok Sabha | The pinned HF revision and archived card; a rights-chain statement for the extracted PDF text. Needed only if it is used beyond local retrieval. |

**Decision owner:** the project owner, institution or ethics office. A completed clearance record is the only input that unblocks annotation.
