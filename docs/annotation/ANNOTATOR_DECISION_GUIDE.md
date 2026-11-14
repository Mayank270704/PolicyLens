# Annotator decision guide — Indian stance (PROPOSED — NOT ADOPTED)

A one-page companion to [PROPOSED_INDIAN_STANCE_CODEBOOK_v2.md](PROPOSED_INDIAN_STANCE_CODEBOOK_v2.md) (MyGov) and [PROPOSED_TWEET_STANCE_GUIDE_v1.md](PROPOSED_TWEET_STANCE_GUIDE_v1.md) (tweets). All examples are **SYNTHETIC**.

## The four questions, in order

```
1. Can anyone read it, and does it have content?
     no  -> exclusion: UNREADABLE / ATTACHMENT_ONLY / NON_SUBSTANTIVE
     can't read the language yourself -> leave labels blank, needs_review = yes (LANGUAGE)
2. Is any part about the stance target?          (MyGov: the draft licence; tweets: the stance_target you name)
     no  -> exclusion: OFF_TOPIC
3. Can you point to a position on that target?
     no  -> Neutral
4. Can its direction be resolved?
     yes -> Support / Oppose
     no  -> Unclear + one unclear_reason
```

Then set **confidence** (how clear your decision is) and, **separately**, **needs_review** (whether someone else should look at it).

## Hard cases

| Case | Do this | SYNTHETIC example |
|---|---|---|
| **Missing context** | Has a position that depends on something you can't see → Unclear / `MISSING_CONTEXT`. No position of its own ("agreed", "+1") → `NON_SUBSTANTIVE`. | "Exactly what the previous speaker said about attribution." → Unclear / MISSING_CONTEXT |
| **Sarcasm** | Clear intended direction → that label. Can't tell sincere from ironic → Unclear / `SARCASM_UNRESOLVED`, confidence 1. | "Wonderful, another licence nobody will read." → Oppose if clearly mocking the licence |
| **Mixed positions** | Use the commenter's own overall verdict, "minor" framing or dismissal. With none of these → Unclear / `MIXED`. Strong words alone never decide it. | "Great goals, terrible clauses — can't say which matters more." → Unclear / MIXED |
| **Conditional** | Core objection to the draft as written → Oppose. Minor, or already met → the underlying direction. Unknown whether met → Unclear / `CONDITIONAL_UNRESOLVED`. | "Acceptable only if commercial reuse stays free." (the draft is silent) → Unclear / CONDITIONAL_UNRESOLVED |
| **Irrelevant** | No part about the target → `OFF_TOPIC`, however strong the opinion. If part is relevant, label that part and say so in the rationale. | "Fix the railway timetable." → OFF_TOPIC |
| **Ambiguous target** | Can't tell whether it's about the target or something else, **and** it has a position → Unclear / `AMBIGUOUS_TARGET`. | "This scheme is useless." (which scheme?) → Unclear / AMBIGUOUS_TARGET |
| **Criticism with a fix** | Criticises a clause but asks for it to be improved → Support. | "Simplify clause 3 so small firms can comply." → Support |
| **Distrust only** | No position on the target → Neutral. | "Government always hides things." → Neutral if no position on the licence |
| **Negation** | Counts only when it negates a position. Negation inside a description or fact is not a cue. | "Many people don't know data.gov.in exists." → Neutral |

## Confidence vs needs-review (different things)

| | `confidence` | `needs_review` |
|---|---|---|
| Meaning | How clear the decision is (1 low / borderline, 2 medium, 3 high) | Someone else should check this item |
| Example | A clear Oppose → 3 | A clear Oppose where the guide has no rule for the case → confidence 3, `needs_review = yes, GUIDELINE_GAP` |
| Example | Truly torn between Neutral and Unclear → 1 | The same item → `needs_review = yes, BORDERLINE` |

## Never

- Use tone or sentiment as the label: "angry" is not Oppose, and "polite" is not Support.
- Copy names, emails, phone numbers or URLs into any field.
- Look at model predictions, clusters, weak labels or the other annotator's sheet.
- Look at or discuss the tweet **locked test** items before the main batch is complete.
