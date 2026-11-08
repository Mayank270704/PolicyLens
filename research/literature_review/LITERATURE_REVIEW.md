# PolicyLens — Literature Review

**Status:** research document. Every entry below was located via live web
search conducted for this review (WebSearch, this session) — **no
citation, author list, DOI, dataset, or finding in this document was
reconstructed from memory or invented.** Where a bibliographic detail
(a DOI, an exact author list, a venue, a specific reported number) could
not be confirmed directly from a primary source (the paper's own page —
arXiv, ACL Anthology, publisher DOI page) within this search pass, it is
explicitly marked **"not independently verified"** rather than presented
as fact. Several entries below are preprints (arXiv) with no confirmed
peer-reviewed publication; these are labeled as preprints throughout, not
silently treated as equivalent to peer-reviewed work.

This review does not claim to be exhaustive. It aims for 3–5 solid, real
papers per topic area, prioritizing foundational/benchmark papers and
papers structurally closest to PolicyLens's own design.

---

## 1. Public consultation and citizen participation analysis

**Cardie, Farina, Rawding, Aijaz (2008) — "An eRulemaking Corpus:
Identifying Substantive Issues in Public Comments."** LREC 2008,
Marrakech. [aclanthology.org/L08-1107](https://aclanthology.org/L08-1107/).
Problem: sentence-level identification of substantive rule-specific
issues in e-rulemaking public comments. Dataset: an original annotated
eRulemaking comment corpus. Method: corpus construction + six-annotator
agreement study (primarily a resource/methodology paper). Metrics:
inter-annotator agreement. Findings: e-rulemaking text has domain-specific
properties that make issue-categorization harder than typical text
classification. Limitations: small, domain-specific, pre-dates
embedding/transformer methods entirely. **Relevance to PolicyLens:** a
direct, 15-years-prior precedent for "classify/categorize public comments
against government rule text" — establishes that annotation difficulty
and agreement measurement were recognized problems in this exact domain
long before this project.

**Cardie, Farina, Aijaz, Rawding, Purpura (2008) — "A Study in
Rule-Specific Issue Categorization for e-Rulemaking."** 9th Annual
International Digital Government Research Conference (dg.o 2008),
Montreal. URL found via a CORE repository mirror
([core.ac.uk/download/73974883.pdf](https://core.ac.uk/download/73974883.pdf));
**DOI not independently verified.** Problem: automating issue
categorization of public comments by rule-specific topic. Method: standard
vs. hierarchical text-categorization methods on e-rulemaking data.
Findings: automated categorization shows promise for reducing manual
review effort, though the task remains harder than generic categorization.
**Relevance:** same research lineage as above; motivates PolicyLens's
separate semantic-grouping component (grouping by issue/concern, not just
stance).

**GWU Regulatory Studies Center methodology note (Thevenard, Feb 2026)**
— LLMs as research assistants for studying public participation in
regulatory consultations, using Brazilian telecom regulator (ANATEL)
consultation data (suggestions labeled accepted/partially-accepted/
rejected), spanning TF-IDF/embeddings through supervised classifiers.
**Not peer-reviewed** — a practitioner methodology note, not independently
verified beyond the search snippet. **Relevance:** a close structural
analog (labeled consultation responses vs. a regulatory decision) worth
tracking, flagged explicitly as non-peer-reviewed.

**U.S. Chief Data Officer Council — Public Comment Analysis Pilot**
(pilot concluded ~2021; [cdo.gov/news/public-comment-analysis-pilot](https://cdo.gov/news/public-comment-analysis-pilot)).
A U.S. federal government pilot (not an academic publication) building
cross-agency reusable NLP tooling for public comment analysis; reported
(self-described, not independently audited) an HHS projection of
&gt;300,000 employee-hours/year saved on one agency's comment-review
process. **Relevance:** real institutional (not just academic) demand for
this problem space — and a documented counterpoint exists too: a cited
Sunlight Foundation analyst view (found via secondary search results, not
independently fetched) noted NLP added little value for one FCC
consultation specifically because its comment interface was already
highly structured. **This context-dependence of benefit is directly
relevant to this project's own limitations framing** — comment-analysis
tooling is not uniformly useful across every consultation design.

---

## 2. Stance detection in natural language processing

**Mohammad, Kiritchenko, Sobhani, Zhu, Cherry (2016) — "SemEval-2016
Task 6: Detecting Stance in Tweets."** SemEval-2016, pp. 31–41, San
Diego. **DOI 10.18653/v1/S16-1003 (verified, consistent across ACL
Anthology mirrors).** [aclanthology.org/S16-1003](https://aclanthology.org/S16-1003/).
Problem: the first benchmark shared task for stance detection
(favor/against/none toward a target), explicitly distinguished from
sentiment. Dataset: tweets across six targets (five supervised + one
zero-shot "Donald Trump" subtask); per the companion dataset page,
2,914 training / 1,249 test pairs across five targets. Metrics:
macro-averaged F1 over Favor/Against. Findings: established stance
detection as a distinct, tractable task and catalyzed a large body of
follow-on research. Limitations: Twitter-only, short-text, English-only,
a fixed small target set — does not transfer directly to long-form policy
comments. **Relevance:** the foundational benchmark defining the task
PolicyLens's stance classifier performs, in a very different text domain.

**Küçük &amp; Can (2020) — "Stance Detection: A Survey."** ACM Computing
Surveys 53(1). **DOI 10.1145/3369026 (verified).**
[doi.org/10.1145/3369026](https://www.doi.org/10.1145/3369026).
Comprehensive survey of stance-detection task definitions, methods,
datasets, and application areas across social media and general online
text. **Relevance:** general grounding reference for the taxonomy and
method landscape behind PolicyLens's own four-label design.

**AlDayel &amp; Magdy (2021) — "Stance detection on social media: State
of the art and trends."** Information Processing &amp; Management 58(4),
article 102597. **DOI 10.1016/j.ipm.2021.102597 (verified via arXiv
cross-link).** [arxiv.org/abs/2006.03644](https://arxiv.org/abs/2006.03644).
State-of-the-art survey spanning NLP, web science, and social computing
approaches; reviews target types, feature sets, classical-ML vs. neural
approaches, and downstream applications. **Relevance:** useful for
comparing classical feature-engineering approaches (PolicyLens's TF-IDF
baselines) against neural approaches within a single reviewed source.

**Zhang, Dai, Niu, Yin, Fan, et al. (2024) — "A Survey of Stance
Detection on Social Media: New Directions and Perspectives."** arXiv
preprint, submitted Sept 2024, revised Nov 2024.
[arxiv.org/abs/2409.15690](https://arxiv.org/html/2409.15690v2).
**Not confirmed as peer-reviewed/published in a venue** — cited here
explicitly as a preprint. Note: v1 and v2 of this preprint list different
author counts (two authors were added between versions); flagged rather
than silently resolved. **Relevance:** the most recent survey located,
useful for current (2024-era) directions once its preprint status is kept
in mind.

**Xie, Zhang, Zhao, Wang, Zou, Tian, Zhou, Tan (2023) — "Adversarial
Learning-based Stance Classifier for COVID-19-related Health Policies."**
DASFAA 2023; arXiv:2209.04631 (v3, camera-ready, Jan 2023).
[arxiv.org/abs/2209.04631](https://arxiv.org/pdf/2209.04631). Problem:
cross-target/zero-shot stance classification across different COVID-19
health policies. Method: each policy is a "target," text is paired with a
policy description as a sentence pair, with adversarial domain adaptation
for cross-policy transfer. **Relevance: the closest match found in this
review to "policy-aware stance classification"** — it directly pairs
comment text with a policy-description target, structurally analogous to
PolicyLens conditioning stance on `policy_context`.

---

## 3. Policy-aware / context-aware stance classification

*(Xie et al. 2023, above, is the strongest direct match and is
cross-referenced here.)*

**Burnham (2023) — "Stance Detection: A Practical Guide to Classifying
Political Beliefs in Text."** arXiv:2305.01723.
[arxiv.org/abs/2305.01723](https://arxiv.org/abs/2305.01723v2).
**Not confirmed published in a peer-reviewed venue** — a preprint.
Argues that stance detection requires precisely defining what context a
classifier actually needs to infer stance correctly, and that without
sufficient context, accurate inference may be structurally impossible.
**Relevance:** directly supports this project's own design decision
(`STANCE_LABEL_DEFINITIONS.md` rule D6) that policy context must be
supplied to the annotator (and, for a future classifier, the model),
never inferred from comment text alone. *Correction logged during
research:* the title "Sentiment is Not Stance" was initially,
incorrectly associated with this author during search; that paper is
actually Bestvater &amp; Monroe (see Section 4) — recorded here so the
correction is traceable, not silently absorbed.

**Ji, Ning, Zhang, Liu, Lin (2025) — introduces a context-aware
attention architecture for zero-/few-shot stance detection (LLM-driven
implicit target augmentation + a dynamic context-aware attention
network).** EMNLP 2025, pp. 5872–5884, Suzhou.
[aclanthology.org/2025.emnlp-main.299](https://aclanthology.org/anthology-files/pdf/emnlp/2025.emnlp-main.299.pdf).
Method: a two-stage framework that augments implicit targets via an LLM,
then jointly encodes text–target pairs with an attention mechanism that
adapts to context. **Caveat:** a secondary conference-index listing names
the architecture differently than the component name found elsewhere;
**this naming discrepancy was not resolved** from search snippets alone
and would need a direct read of the full PDF to settle — flagged rather
than guessed. **Relevance:** a current (2025) architecture for jointly
encoding text with its context/target, the same structural problem as
conditioning stance classification on `policy_context`/`policy_section`.

---

## 4. Aspect-based sentiment analysis (ABSA) versus stance detection

**Bestvater &amp; Monroe (2022/2023) — "Sentiment is Not Stance:
Target-Aware Opinion Classification for Political Text Analysis."**
Political Analysis 31(2), pp. 235–256 (published online Apr 2022,
print-dated 2023 — both years appear across listings). **DOI
10.1017/pan.2022.10 (verified).**
[doi.org/10.1017/pan.2022.10](https://dx.doi.org/10.1017/pan.2022.10).
Argues sentiment and stance are not interchangeable for political text,
and that using sentiment as a stance proxy introduces measurement bias.
**Relevance:** directly supports `STANCE_LABEL_DEFINITIONS.md` rule D1
("direction over tone") at the level of a peer-reviewed
political-science-methodology argument — a comment's emotional register
and its evaluative stance can diverge, exactly as PolicyLens's own
taxonomy insists.

**ABSA-vs-stance, general finding (synthesized across multiple search
results, not a single paper):** ABSA assigns polarity toward
explicitly-mentioned aspect terms within a text; stance detection assigns
evaluative alignment toward a target that may not even appear in the
text, and is explicitly meant to be tone-independent. An upcoming
SemEval-2026 task (DimABSA, arXiv number 2604.07066 per search snippet,
**not independently verified beyond title**) reportedly treats stance
targets as a kind of aspect, suggesting the two research communities are
converging rather than staying fully separate — noted as a trend, not a
settled fact.

---

## 5. Short-text semantic similarity

**Reimers &amp; Gurevych (2019) — "Sentence-BERT: Sentence Embeddings
using Siamese BERT-Networks."** EMNLP-IJCNLP 2019, pp. 3982–3992. **DOI
10.18653/v1/D19-1410; also arXiv:1908.10084.** Problem: raw BERT/RoBERTa
require quadratic pairwise passes to compare sentences, making semantic
search/clustering over large sets impractical (the authors estimate
~65 hours to find the most similar pair among 10,000 sentences with BERT,
vs. ~5 seconds with SBERT). Method: siamese/triplet-network fine-tuning
of BERT to produce fixed-size, cosine-comparable sentence embeddings.
Findings: matches or beats prior sentence-embedding methods while being
orders of magnitude faster for pairwise/clustering use cases.
**Relevance:** the exact embedding family `SEMANTIC_GROUPING_EXPERIMENT_PLAN.md`
and `STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md` specify
(`all-MiniLM-L6-v2` is an SBERT-family model) — this paper is the direct
justification for using frozen sentence embeddings rather than raw BERT.

**Gao, Yao, Chen (2021) — "SimCSE: Simple Contrastive Learning of
Sentence Embeddings."** EMNLP 2021, pp. 6894–6910.
[arxiv.org/abs/2104.08821](https://arxiv.org/abs/2104.08821),
[ACL Anthology 2021.emnlp-main.552](https://aclanthology.org/2021.emnlp-main.552/).
Method: unsupervised variant uses dropout-as-noise for positive pairs
from the same sentence; supervised variant adds NLI entailment/
contradiction pairs. Findings (STS benchmarks, Spearman's correlation):
BERT-base reaches 76.3% (unsupervised) / 81.6% (supervised) average
correlation. **Relevance:** a documented, verified state-of-the-art
alternative to SBERT if `all-MiniLM-L6-v2` proves insufficient for
separating nuanced concern groups later.

**Semantic Textual Similarity Benchmark (STS-B) / SemEval STS shared
tasks (2012–2016).** Part of the GLUE benchmark suite; originates from
the SemEval STS shared-task series. **A primary SemEval/GLUE source page
could not be reached directly in this search pass; pair-count figures
(commonly cited as 8,628 total pairs) come from secondary sources and are
marked not fully primary-source-verified.** **Relevance:** the standard
benchmark family any embedding-model choice is validated against —
relevant as a methodological anchor, not as PolicyLens's own data.

---

## 6. Semantic clustering of public comments

**EU stakeholder-consultation clustering study.** *Artificial
Intelligence and Law* (Springer). **DOI 10.1007/s10506-024-09426-6.**
Data: 830 stakeholder responses across three EU legislative proposals
(AI Act, Digital Markets Act, Digital Services Act). Method: described as
combining lexical and semantic analysis — **the specific technique pairing
could not be confirmed as exactly "TF-IDF + BERT" from the abstract-level
search snippet; that is a reasonable inference, not a verified direct
quote, and is flagged as such.** Findings: argues the European
Commission's current opinion-clustering process is non-standardized/
case-by-case, and that NLP tooling could support it; reports that NGO and
large-company positions on the DSA consultation clustered similarly
across the methods tried. **Relevance: the closest real precedent found
for PolicyLens's own task** — clustering genuine government-consultation
responses by concern — and direct evidence for this project's own
research-gap framing (this is an active, not-yet-standardized applied
problem).

**Regulations.gov rulemaking comment analysis (LDA + sentiment).** ECPR
conference paper. **Author name not retrievable from the search snippet;
not independently verified.** Data: 5,547 comments scraped from
regulations.gov via its API. Method: LDA topic modeling with a
sentiment-analysis layer, compared against the agency's final rule text.
Findings: identifies areas where the final rule diverged from
comment-derived themes/sentiment. **Relevance:** an analogous (U.S.
federal, not Canadian open-government) use case showing comment-topic-
modeling as an established evaluative technique — included as a
real, if weakly-sourced, lead, not a fully confirmed citation.

**Lower-confidence leads found but not independently verified** (recorded
for future follow-up, not relied upon here): a 2026 arXiv preprint on an
LLM pipeline for EU Digital Fairness Act consultation analysis
(arxiv.org/pdf/2605.30995 — found via search summary only, not fetched
directly); a U.S. CDO Council pilot report describing a neural comment-
grouping tool with self-reported, preliminary time-savings estimates; a
trucking-rulemaking topic-modeling study; a WOTUS (EPA docket) LDA +
sentiment project. None of these are cited as established facts above —
listed only as leads a deeper follow-up search should verify directly.

---

## 7. Topic modelling and density-based clustering

**Blei, Ng, Jordan (2003) — "Latent Dirichlet Allocation."** Journal of
Machine Learning Research 3, pp. 993–1022.
[jmlr.org/papers/v3/blei03a.html](https://jmlr.org/papers/v3/blei03a.html).
The foundational generative topic-model framework nearly all later
"classic" topic modeling builds on (variational inference + EM).
**Relevance:** the classic baseline that embedding-based methods (below)
are explicitly compared against in later literature.

**Grootendorst (2022) — "BERTopic: Neural topic modeling with a
class-based TF-IDF procedure."** arXiv:2203.05794. Method: (1) SBERT
document embeddings, (2) cluster the embeddings, (3) derive topic-word
representations via a class-based TF-IDF variant. Findings: competitive,
coherent topics vs. both classical and other clustering-based topic
models. **Relevance: structurally the closest published pipeline to
`SEMANTIC_GROUPING_EXPERIMENT_PLAN.md`'s own design** (embed → cluster →
extract representative terms/comments) — a direct architectural precedent.

**HDBSCAN — three linked references, each verified:**
- Campello, Moulavi, Sander (2013), PAKDD — original algorithm.
- Campello, Moulavi, Zimek, Sander (2015), *ACM Transactions on Knowledge
  Discovery from Data* 10(1), pp. 1–51 — extended journal version, adds
  the GLOSH outlier-detection measure.
- McInnes, Healy, Astels (2017), "hdbscan: Hierarchical density based
  clustering," *Journal of Open Source Software* 2(11):205. **DOI
  10.21105/joss.00205** — the standard citation for the Python `hdbscan`
  package already installed in this project's environment.
- McInnes &amp; Healy (2017), "Accelerated Hierarchical Density
  Clustering," ICDMW 2017, arXiv:1705.07321 (pagination pp. 33–42 per one
  repository citation, **not independently confirmed beyond that one
  source**).

**Relevance:** the exact algorithm `SEMANTIC_GROUPING_EXPERIMENT_PLAN.md`
specifies as the primary clustering method, chosen specifically for its
native noise category and no-fixed-k property — directly justified by
these papers.

---

## 8. Abstractive and extractive summarization

**See, Liu, Manning (2017) — "Get To The Point: Summarization with
Pointer-Generator Networks."** ACL 2017, Vol. 1, pp. 1073–1083.
[arxiv.org/abs/1704.04368](https://arxiv.org/abs/1704.04368),
[ACL Anthology P17-1099](https://aclanthology.org/P17-1099/). Problem:
standard seq2seq abstractive summarizers reproduce facts inaccurately and
repeat themselves. Method: a hybrid pointer-generator network (copy
source words or generate new ones) plus a coverage mechanism against
repetition. Findings: ≥2 ROUGE points over prior abstractive SOTA on
CNN/Daily Mail. Limitations (commonly cited): the copy mechanism biases
output toward extractive-like behavior; coverage is a heuristic penalty,
not a faithfulness guarantee. **Relevance:** illustrates the classic
abstractive-summarization faithfulness failure this project's extractive-
first design choice is explicitly avoiding.

**Liu &amp; Lapata (2019) — "Text Summarization with Pretrained Encoders"
(BERTSUM).** EMNLP-IJCNLP 2019, arXiv:1908.08345. Method: a document
encoder built on BERT (multiple `[CLS]` tokens + interval segment
embeddings), feeding either an extractive sentence classifier
(BertSumExt) or a randomly-initialized Transformer decoder (BertSumAbs).
Findings: reported SOTA ROUGE on CNN/DailyMail, NYT, and XSum for both
variants. **Relevance:** supports an extractive, pretrained-encoder-based
sentence-ranking approach as a realistic, CPU-tractable building block for
PolicyLens's representative-comment selection — distinct from full
generative summarization.

**Zhang, Zhao, Saleh, Liu (2020) — "PEGASUS: Pre-training with
Extracted Gap-sentences for Abstractive Summarization."** ICML 2020
(PMLR vol. 119), arXiv:1912.08777. Method: masks whole "principal"
sentences from a document and trains the model to generate them from the
rest. Findings: SOTA across 12 downstream datasets; strong low-resource
performance (good results from as few as ~1,000 fine-tuning examples);
human evaluators rated outputs comparable to human-written summaries on
several datasets. **Relevance:** the "~1,000 examples" finding is a useful
reference point for judging whether PolicyLens's own small, single-
annotator-scale dataset could ever support abstractive summarization —
directly informs the plan's choice to default to extractive summaries.

**Dong (2018) — "A Survey on Neural Network-Based Summarization
Methods."** arXiv:1804.04589. **Preprint; not confirmed peer-reviewed
published beyond arXiv.** Surveys ten neural summarizers (five
extractive, five abstractive). **Relevance:** a single-paper map of the
extractive/abstractive design space.

---

## 9. Evidence-grounded summarization

**Kryściński, McCann, Xiong, Socher (2020) — "Evaluating the Factual
Consistency of Abstractive Text Summarization" (FactCC).** EMNLP 2020,
[aclanthology.org/2020.emnlp-main.750](https://aclanthology.org/2020.emnlp-main.750),
arXiv:1910.12840. Problem: standard metrics (ROUGE) don't measure factual
consistency with the source. Method: a BERT-based classifier trained on
synthetic consistency-violation examples (entity/number/pronoun swaps,
negation, repetition/removal), with an auxiliary span-extraction task
locating the supporting source span. Findings: the auxiliary span task
measurably helps; dataset/code/weights released. **Relevance:** directly
validates the "evidence span" idea at the heart of PolicyLens's
extractive-first design — a summary built from the comment itself is
inherently traceable, sidestepping the exact problem FactCC was built to
detect.

**Laban, Schnabel, Bennett, Hearst (2022) — "SummaC: Re-Visiting
NLI-Based Models for Inconsistency Detection in Summarization."** TACL
10, pp. 163–177. [aclanthology.org/2022.tacl-1.10](https://aclanthology.org/2022.tacl-1.10),
arXiv:2111.09525. Problem: prior NLI-based consistency detectors operate
at sentence granularity while inconsistency detection is really a
document-level problem. Method: segment into sentence units, compute
pairwise NLI-style entailment scores, aggregate (zero-shot or via a
learned convolutional layer). Findings: state-of-the-art balanced
accuracy (~74.4%) on a six-dataset benchmark the authors assembled.
**Relevance:** a concrete, reusable automatic faithfulness check
PolicyLens could apply if it ever moves beyond extractive summaries.

**Ji, Lee, Frieske, et al. (2023) — "Survey of Hallucination in Natural
Language Generation."** ACM Computing Surveys 55(12), pp. 1–38. **DOI
10.1145/3571730 (confirmed).** arXiv:2202.03629. Scope: hallucination
across NLG tasks including abstractive summarization; organizes
mitigation approaches (data-, training-, inference-related). **Relevance:**
a well-cited, peer-reviewed umbrella reference for *why* this project
defaults to extractive, evidence-traceable summaries.

**Faithfulness-evaluation survey, RANLP 2025.**
[aclanthology.org/2025.ranlp-1.74](https://aclanthology.org/2025.ranlp-1.74).
Author list surfaced in search as "Lamsiyah, Nourbakhsh, Schommer" but
**not independently re-confirmed from the primary page.** Reviews 40+
faithfulness-evaluation studies (2020–2025). **Relevance:** the most
current survey located; cite venue/scope with confidence, author list
with the caveat above.

---

## 10. Human annotation reliability and evaluation

**Landis &amp; Koch (1977) — "The Measurement of Observer Agreement for
Categorical Data."** *Biometrics* 33(1), pp. 159–174. **DOI 10.2307/2529310
(confirmed).** The foundational statistical framework for categorical
observer-agreement studies (kappa-type statistics, marginal-homogeneity
tests for bias), illustrated with a clinical diagnosis example.
**Important caveat:** the widely-used "0.61–0.80 = substantial"
interpretation bands commonly attributed to this paper were **not
directly re-confirmed in the retrieved content during this search** — the
attribution is extremely standard field convention (and this project's
own `REPEAT_ANNOTATION_PROCEDURE.md` already uses it), but it is flagged
here rather than silently re-asserted as something this review itself
verified word-for-word. **Relevance:** the foundational citation behind
every kappa-interpretation statement in this project's repeat-annotation
documentation.

**Artstein &amp; Poesio (2008) — "Inter-Coder Agreement for Computational
Linguistics."** *Computational Linguistics* 34(4), pp. 555–596. **DOI
10.1162/coli.07-034-R2 (confirmed).**
[aclanthology.org/J08-4004](https://aclanthology.org/J08-4004/). Survey of
agreement-coefficient methods used in corpus annotation (kappa, Scott's
π, Krippendorff's α) and task-specific guidance; argues alpha-like
coefficients may be under-used relative to kappa-like ones. **Relevance:**
the standard NLP-specific reference for agreement-metric choice —
relevant context for why this project chose Cohen's kappa (simplicity/
interpretability) over the alternatives this survey discusses.

**Sandri et al. (2023) — disagreement-taxonomy paper for subjective
annotation tasks.** EACL 2023.
[aclanthology.org/2023.eacl-main.178](https://aclanthology.org/2023.eacl-main.178).
**Full author list not independently re-confirmed from the primary PDF
in this search pass.** Proposes a taxonomy of *why* annotators disagree on
subjective tasks and argues disagreement should inform guideline
improvement rather than be adjudicated away as noise. **Relevance:**
directly supports this project's own existing position
(`STANCE_ANNOTATION_GUIDELINES.md` section 6: "disagreement is not an
error state") with a genuine, citable academic basis.

**Mohammad, Sobhani, Kiritchenko (2016/2017) — "Stance and Sentiment in
Tweets."** Companion paper to SemEval-2016 Task 6 (Section 2, above).
Dataset: 2,914 train / 1,249 test tweet-stance pairs across five targets,
plus a sixth zero-shot "Trump" target. Reported performance figures
differ across the shared-task slide deck (best system ≈67.82 F1) and the
companion paper's own simpler system (≈70.3 F1) — **these two numbers come
from different sources and are reported as such, not merged into one
figure.** **Relevance:** the canonical "stance ≠ sentiment, stance is
target-dependent" benchmark — grounds why PolicyLens treats
policy-directed stance classification as its own task, distinct from
generic sentiment analysis.

**Recent (2026) preprints on subjective-task reliability, noted but not
relied upon:** an arXiv preprint (2604.17022) arguing that collapsing
annotator judgments into one gold label obscures *why* disagreement
occurred, proposing an audit framework; and an arXiv guide (2603.06865)
surveying agreement-metric choice broadly. **Author details not
independently re-verified for either; included only as "recent work
extending the disagreement-as-signal line," not as load-bearing
citations.**

---

## Comparative Analysis

*(Phase 2 of the research task — built on the literature above, not a
separate search.)*

### Traditional ML vs. transformer-based stance detection

| | Traditional ML (TF-IDF + linear classifier) | Transformer-based |
|---|---|---|
| Representative work | Mohammad et al. 2016 shared task (most entrants were SVM/feature-engineered) | Xie et al. 2023; Ji et al. 2025 |
| Strength | Fast, interpretable, works with little data | Captures context/semantics beyond lexical overlap |
| Weakness | Misses contextual/implicit stance cues | Needs more data; CPU training is slow at scale (see `HARDWARE_FEASIBILITY_REPORT.md`) |
| Where appropriate for PolicyLens | First-pass baseline at pilot (~250-item) scale — `STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md` experiments 1–2 | Worth revisiting once annotated data and/or GPU hardware grow — experiments 3–4 |

### Sentiment analysis vs. stance detection

| | Sentiment analysis | Stance detection |
|---|---|---|
| Measures | Emotional polarity of the text itself | Evaluative alignment toward a target, which may not even appear in the text |
| Key reference | — | Bestvater &amp; Monroe 2022/2023 ("Sentiment is Not Stance") |
| Risk of conflating them | Using sentiment as a stance proxy introduces measurement bias (shown empirically in political text) | — |
| PolicyLens's position | Explicitly rejected as a substitute — `STANCE_LABEL_DEFINITIONS.md` rule D1 ("direction over tone") requires looking past emotional register to the comment's actual evaluative direction | This is the task PolicyLens performs |

### Topic modelling vs. semantic clustering

| | Classic topic modeling (LDA) | Embedding-based clustering (BERTopic-style / SBERT + HDBSCAN) |
|---|---|---|
| Representation | Bag-of-words, generative mixture model | Dense contextual sentence embeddings |
| Needs fixed topic count? | Yes | HDBSCAN: no; K-Means: yes (used only as PolicyLens's comparison run) |
| Captures synonymy/paraphrase | Weakly (word co-occurrence only) | Well (semantic similarity) |
| Where appropriate for PolicyLens | Not chosen as primary — see `SEMANTIC_GROUPING_EXPERIMENT_PLAN.md`'s rationale | Primary method, directly following the BERTopic-style pipeline shape (embed → cluster → represent) |

### HDBSCAN vs. K-Means

| | HDBSCAN | K-Means |
|---|---|---|
| Requires choosing *k* in advance | No | Yes |
| Native noise/outlier handling | Yes (`-1` label) | No |
| Assumption about cluster shape | Variable-density, non-spherical | Roughly spherical, similar-size |
| PolicyLens's role for each | Primary method | Comparison run only — see `SEMANTIC_GROUPING_EXPERIMENT_PLAN.md` |

### Extractive vs. abstractive summarization

| | Extractive | Abstractive |
|---|---|---|
| Output | Verbatim source sentences/spans | Newly generated text |
| Faithfulness risk | Low by construction | Real and well-documented (See et al. 2017; Ji et al. 2023 hallucination survey) |
| Traceability to source | Direct (the text *is* the evidence) | Requires a separate faithfulness check (FactCC, SummaC) to even approximate |
| PolicyLens's choice | **Default for the current plan** | Explicitly out of scope until faithfulness evaluation is separately scoped — see `SYSTEM_ARCHITECTURE.md` component 9 |

### Generic vs. evidence-grounded summarization

| | Generic summarization | Evidence-grounded summarization |
|---|---|---|
| Validated by | ROUGE (surface overlap with a reference summary) | FactCC / SummaC-style consistency checks, or (PolicyLens's current approach) summaries that are extractive by construction |
| Guarantees traceability? | No | Yes, when evidence spans/comment IDs are recorded (`Summary.evidence_comment_ids` in `DATA_MODEL.md`) |
| PolicyLens's requirement | Not sufficient on its own | Required — every summary must carry non-empty evidence references |

---

## Search process summary

Three parallel literature searches were conducted (via WebSearch,
this session), one per cluster of related topics (stance-detection
cluster: topics 1–4; clustering/similarity cluster: topics 5–7;
summarization/annotation cluster: topics 8–10). Each search prioritized
primary sources (arXiv abstract pages, ACL Anthology, publisher DOI
pages) over secondary/aggregator pages, and every entry above states
explicitly which bibliographic details were confirmed this way versus
which could not be and are therefore flagged. No paper, author, DOI,
dataset, or finding anywhere in this document was invented or
reconstructed from unverified memory.

**Known gaps in this pass** (candidates for a follow-up search, not
claimed as covered here): primary verification of the SemEval/GLUE STS-B
page directly; pre-BERT extractive-summarization classics (TextRank,
LexRank, MMR) and BART (Lewis et al. 2019); a direct fetch of the 2026 EU
Digital Fairness Act consultation-analysis preprint; resolution of the
DyMCA/FiCAN naming discrepancy in the Ji et al. 2025 entry; direct
primary-source re-confirmation of the RANLP 2025 and EACL 2023 author
lists.
