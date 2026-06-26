# ATS Keyword Scoring — Today, the AI Shift, and How TrueMatch Should Self-Evolve

**Status:** Research synthesis / strategy reference
**Date:** 2026-06-25
**Scope:** How Applicant Tracking Systems score résumés today, where scoring is heading with AI/LLMs, the academic + regulatory backdrop, and whether (and how) TrueMatch can continuously self-improve while staying accurate, fair, and compliant.

> Sourcing discipline: claims are cited inline. Vendor-marketing figures are flagged as directional; the strongest anchors are peer-reviewed studies, primary regulatory/court documents, and self-critical industry sources. Regulatory dates move — re-verify against primary sources before any compliance decision.

---

## TL;DR

1. The "**75% of résumés auto-rejected by ATS**" claim is a **myth** (a 2012 marketing line from a now-defunct vendor). Real gatekeeping = **knockout questions + rigid human-set filters + a ~7-second human skim**. The defensible, evidence-backed problem is **false negatives** — Harvard's *Hidden Workers*: 88–94% of employers screen out qualified people on exact-criteria mismatch.
2. Scoring is shifting **keyword → semantic embeddings → LLM reasoning**, but most "AI" is **"agent washing"** (renamed keyword filters), and skills-based hiring is largely "in name only."
3. Independent evidence shows AI screeners are both **biased** (white-name preference ~85% vs ~9% Black-associated) and **barely accurate on real outcomes** (AUC ~0.55) — *this is TrueMatch's wedge*.
4. Regulation (EU AI Act high-risk, NYC LL144, GDPR Art. 22, Title VII) + litigation (*Mobley v. Workday*) make **silent model changes non-compliant by construction**.
5. TrueMatch **can** self-evolve and stay "most accurate at all times" — but as a **governed pipeline** (drift-triggered batch retraining + human-approved version bumps + fairness re-audit), **not** naive online self-learning. The hard limit is **hiring ground truth** (selective labels + delayed, biased outcomes).

---

## Part 1 — How ATS score keywords today

### The myth vs. the mechanism
- **Myth:** "75% of résumés are rejected before a human sees them." Traced to a 2012 claim by **Preptel** (a résumé-optimization vendor that folded in 2013); never substantiated; does not appear in the Harvard report it's often pinned to. [The Interview Guys](https://blog.theinterviewguys.com/ats-resume-rejection-myth/)
- **Reality:** ATS are **inverted-index databases** — they store and surface candidates to recruiter queries, not silently delete them. [Jobscan](https://www.jobscan.co/blog/8-things-you-need-to-know-about-applicant-tracking-systems/)

### What actually gatekeeps (in order of real impact)
1. **Knockout / screening questions** — binary form items (work authorization, license, minimum years) that auto-disposition *before* résumé review. The genuine "auto-reject." [Recruitee](https://support.recruitee.com/en/articles/6108676-set-up-knockout-questions-to-automatically-disqualify-candidates)
2. **Boolean / keyword search** over parsed fields (`Java AND (Spring OR Hibernate) NOT Junior`) — recruiter-driven.
3. **Rigid human-set filters → "hidden workers."** Harvard Business School / Accenture, *Hidden Workers: Untapped Talent* (2021): **88%** of employers admit qualified high-skill candidates get screened out on exact-criteria mismatch (**94%** middle-skill); **27M+** hidden workers in the US. [HBS](https://www.hbs.edu/managing-the-future-of-work/research/Pages/hidden-workers-untapped-talent.aspx)
4. **The ~7-second human skim** that follows. [Ladders eye-tracking, via HR Dive](https://www.hrdive.com/news/eye-tracking-study-shows-recruiters-look-at-resumes-for-7-seconds/541582/)

### Parsing & scoring mechanics
- Field extraction is strong for name/email (~0.99 F1) but **skills extraction is only ~0.75–0.85 F1**, worse on the hardest ~10%. [HireHub (self-critical parser vendor)](https://www.thehirehub.ai/blog/ai-resume-parsing-in-2026-how-it-works-how-accurate-it-actually-is-and-what-breaks-it)
- Breakage comes from **multi-column layouts, tables, graphical skill-bars, headers/footers** (parsers read only the body layer) — not PDFs per se. Legacy **Taleo** is the strict holdout; modern Workday/Greenhouse handle clean PDFs.
- Academic prototypes combine **TF-IDF cosine + Jaccard skill overlap + missing-keyword detection**; commercial semantic matchers normalize skills to a taxonomy via embeddings. [JETIR](https://www.jetir.org/papers/JETIR2504D27.pdf) · [Textkernel](https://developer.textkernel.com/SkillsIntelligence/master/)
- **Title-line over-weighting is real** (job title is among the highest-weighted signals) — exact magnitudes ("10.6× interviews") are vendor-proprietary/unverifiable, but the mechanism is well-attested. *(Validated in our own Roblox GM case: a "Chief AI Officer" headline tanks a keyword score despite strong capability fit.)*
- **Keyword stuffing / white-text is detected and counterproductive** — Greenhouse finds white-text in ~1% of résumés; ManpowerGroup ~10%. 2025 evolution: **prompt injection** — Greenhouse reports **22% of hiring managers found injected prompts**. [Built In](https://builtin.com/articles/hidden-ai-prompts-in-resume) · [Greenhouse](https://www.greenhouse.com/newsroom/an-ai-trust-crisis-70-of-hiring-managers-trust-ai-to-make-faster-and-better-hiring-decisions-only-8-of-job-seekers-call-it-fair)

### Vendor state (2024–2026): away from "% match"
Most vendors abandoned the raw 0–100 score for **grades / bands / verdicts + explanations, human-in-the-loop** — convergent with TrueMatch's framing:

| Vendor | Output | AI feature |
|---|---|---|
| Workday (HiredScore) | A/B/C/D letter grade | "Spotlight"; HiredScore acquired 2024 |
| Oracle Recruiting | Real 0–5 + NL rationale | 24A release |
| iCIMS | Internal rank (not surfaced %) | Copilot; bias-audited under LL144 |
| Greenhouse | 5-level band, **markets against black-box scoring** | "Talent Matching" 2025; excludes PII |
| Lever | Ranked shortlist + binary verdict | "Talent Fit" 2025; anonymized |
| Ashby | **No score/rank** — "Meets / Does not Meet" per criterion | AI-Assisted Review 2024 |
| Jobvite | **Explicitly ranks + scores** | Smart Screening |

---

## Part 2 — Where scoring is heading with AI

### The scoring primitive is shifting
| Era | How it scores |
|---|---|
| Traditional ATS | Boolean / TF-IDF exact-keyword overlap |
| Semantic (mainstream now) | **Cosine similarity of embeddings** + ANN vector search. LinkedIn runs a production **two-tower** retriever. [LinkedIn Eng](https://www.linkedin.com/blog/engineering/platform-platformization/using-embeddings-to-up-its-match-game-for-job-seekers) |
| Skills ontologies | Entity-link to **ESCO / O\*NET / Lightcast**; infer adjacent skills |
| LLM / cross-encoder | Joint reasoning over résumé+JD → fit verdict + rationale. Academic SOTA e.g. **ConFit v2** (2025). [arXiv:2502.12361](https://arxiv.org/html/2502.12361v1) |

### Two reality checks the marketing hides
- **"Agent washing":** Gartner estimates ~130 of thousands of "agent" vendors are real; **~9 in 10 HR leaders report no business value yet** from AI bought. Most "semantic AI" is undisclosed and may be a renamed keyword filter. [CIO Dive](https://www.ciodive.com/news/AI-agent-washing-claims-vetting-technology-vendors/753621/)
- **Skills-based hiring is aspirational:** Harvard Kennedy School + Burning Glass — the shift delivered opportunity in **"not even 1 in 700 hires"**; ~45% of firms dropped degree language with no behavioral change. [HKS/Burning Glass](https://pw.hks.harvard.edu/post/skills-based-hiring-the-long-road-from-pronouncements-to-practice)

### Two failure modes = TrueMatch's wedge
1. **AI screeners are biased.** Wilson & Caliskan, **AIES 2024**: embedding-based résumé retrieval favored white-associated names **85.1%** vs Black-associated **8.6%**; female **11.1%**; **Black-male names 0%**. The bias is in the mechanism. [arXiv:2407.20371](https://arxiv.org/abs/2407.20371) · [Brookings](https://www.brookings.edu/articles/gender-race-and-intersectional-bias-in-ai-resume-screening-via-language-model-retrieval/)
2. **AI screeners are barely accurate on outcomes.** GPT scores résumés near-randomly (**AUC ~0.55**), over-indexing on pedigree. [interviewing.io](https://interviewing.io/blog/refuting-bloombergs-analysis-chatgpt-isnt-racist) — and LLM screeners are **adversarially hijackable**, prompt-injection success **>80%** in one benchmark. [arXiv:2512.20164](https://arxiv.org/abs/2512.20164)

### The two-sided arms race + fraud
- Candidates auto-apply at scale: LinkedIn processes **~11,000 applications/minute (+45% YoY)**. [eWeek](https://www.eweek.com/news/ai-job-applications-linkedin/)
- A Dartmouth/Princeton study found AI-polished applications made candidates **less distinguishable** → hiring rates and wages *dropped*. [CNN](https://www.cnn.com/2025/12/21/economy/ai-hiring-complication)
- Fraud is real: Gartner forecasts **1 in 4 fake profiles by 2028** (a forecast); FBI-documented North Korean fake-worker rings; **Amazon blocked 1,800+** suspected operatives; **LinkedIn restricted 84M fake accounts** in H1 2025. [TechCrunch](https://techcrunch.com/2025/12/18/linkedins-profile-verification-push-is-accelerating-and-india-is-leading-the-charge-in-2025/)

### Academic matching lineage (for reference)
Person-Job Fit neural line: **PJFNN** (2018, [arXiv:1810.04040](https://arxiv.org/abs/1810.04040)), **APJFNN** (SIGIR 2018, [arXiv:1812.08947](https://arxiv.org/abs/1812.08947)), **IPJF** (CIKM 2019), **conSultantBERT** (2021, [arXiv:2109.06501](https://arxiv.org/pdf/2109.06501)), **ConFit/ConFit v2** (ACL 2025). Public benchmarks are thin (XING RecSys 2016/2017; one Chinese dataset) — limiting generalization.

---

## Part 3 — Regulatory & legal backdrop (why this is sharpening)

- **EU AI Act (2024/1689):** hiring AI is explicitly **high-risk** (Annex III §4); provider obligations (risk mgmt, data governance, logging, human oversight, conformity assessment). High-risk obligations bind **2026-08-02** (a proposed "Digital Omnibus" delay to 2027-12-02 is **not yet law** — treat Aug 2026 as operative). [Annex III](https://artificialintelligenceact.eu/annex/3/) · [Art. 113](https://artificialintelligenceact.eu/article/113/) · [Gibson Dunn (proposed delay)](https://www.gibsondunn.com/eu-ai-act-omnibus-agreement-postponed-high-risk-deadlines-and-other-key-changes/)
- **NYC Local Law 144:** independent **bias audit** within prior year + **public impact ratios** (sex / race / **intersectional**) + **≥10-day candidate notice** (enforced 2023-07-05). A Dec 2025 NY Comptroller audit called enforcement "ineffective." [NYC DCWP](https://www.nyc.gov/site/dca/about/automated-employment-decision-tools.page)
- **GDPR Art. 22:** right not to be subject to solely-automated significant decisions; CJEU **SCHUFA (C-634/21, 2023-12-07)** holds a *score itself* can qualify. Requires meaningful human intervention + logic explanation. [GDPR Art. 22](https://gdpr-info.eu/art-22-gdpr/)
- **US:** **Illinois HB 3773** (effective 2026-01-01; bars ZIP as protected-class proxy), **Colorado AI Act** (repealed/replaced May 2026 — fast-moving), **EEOC**/Title VII disparate-impact (four-fifths rule; AI guidance *removed* 2025-01-27 but statutes stand).
- **The teeth = litigation:** *Mobley v. Workday* — federal court granted **ADEA collective-action certification (2025-05-16)** over algorithmic rejection, later extended to HiredScore-scored candidates. [Holland & Knight](https://www.hklaw.com/en/insights/publications/2025/05/federal-court-allows-collective-action-lawsuit-over-alleged)

---

## Part 4 — Can TrueMatch self-learn and stay "most accurate at all times"?

**Yes — but as a governed pipeline, not a self-rewiring model.** For a high-stakes hiring product, naive self-learning is technically ill-advised and **illegal by construction**.

### What NOT to do
- **❌ True online / per-event self-learning.** Hiring labels are delayed by months, one bad batch poisons the live model, and catastrophic forgetting looms. [Huyen](https://huyenchip.com/2022/01/02/real-time-machine-learning-challenges-and-solutions.html) · [EWC, arXiv:1612.00796](https://arxiv.org/abs/1612.00796)
- **❌ The degenerate feedback loop.** Training on "candidates we surfaced and advanced" only observes outcomes for people the model already liked → entrenches historical exclusion. This is literally the **Amazon recruiting-tool failure**. [MIT Tech Review](https://www.technologyreview.com/2018/10/10/139858/amazon-ditched-ai-recruitment-software-because-it-was-biased-against-women/) · [degenerate loops](https://www.theoverfit.com/p/degenerate-feedback-loops)
- **❌ Training on AI output → model collapse** (variance shrinks each generation). [Shumailov et al., *Nature* 2024](https://www.nature.com/articles/s41586-024-07566-y)

### The hard limit — hiring "ground truth" barely exists
"Hired" encodes recruiter bias; "performed well" is delayed/noisy/biased; and you only observe outcomes for those **hired** — the **selective labels problem** ([Lakkaraju et al., KDD 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5958915/)). Naïve accuracy on hired candidates is **invalid for the rejected region a screener most affects.** Mitigations (contraction via lenient/strict reviewers; criterion-related validity) only partially help.

### What self-evolution SHOULD look like for TrueMatch (and what we already have)
1. **Stateful batch retraining, drift-triggered + scheduled floor, behind offline gates.** Monitor **prediction/embedding drift** (PSI ≥0.25, NDCG@k on logged signal) since labels lag; **backfill outcomes** when they arrive. *Foundation already built: Phase-3 longitudinal outcome tracking.*
2. **Engineer the feedback loop deliberately:** add **exploration** (surface candidates the model wouldn't top-rank), log with **propensities** + debias (IPS), keep a **human-labeled anchor**. *We already generate this via Article-14 human review + counter-recommendation — that human signal is the gold, not the model's own past matches.*
3. **Keep the keyword signal deterministic.** The three-signal split is an asset: keyword/TF-IDF stays language-invariant and does **not** learn; only **semantic** and **capability** signals evolve — isolating change and preserving an auditable, stable core.
4. **Validate job-relatedness, not "who got hired."** Aim for criterion-related validity; treat the hiring label as a biased hypothesis; use selective-labels-aware evaluation.
5. **Guardrail relentlessly for adverse impact** (four-fifths across protected + intersectional groups) — a non-negotiable metric that must not degrade even if accuracy improves. [Kohavi, Trustworthy OCEs](https://www.tandfonline.com/doi/full/10.1080/00031305.2023.2257237)
6. **Govern every change — legally required.** Under NYC LL144 / EU AI Act / Title VII / GDPR, a silently retrained model is a *new tool* whose audit/conformity assessment/disclosures are stale → non-compliant. The compliant loop: **version → model card → re-run fairness/adverse-impact → human sign-off → refresh audit/disclosures → then serve.** [NIST AI RMF](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/)

### Conclusion
"Most accurate at all times" is achievable **as a property of the pipeline**: continuously *detect drift → propose improvements → re-validate → human-approve a governed version bump.* Slower than "self-learning AI" sounds — and the **only** version that is simultaneously accurate, fair, and legal. The auditability/fairness discipline that slows us down is exactly the **moat** incumbents (shipping biased, near-random, un-auditable scorers) cannot easily match.

---

## Proposed next build — a governed `learning/` subsystem
Scoped against what exists today (3-signal engine, decision engine, Article-14 review, longitudinal outcomes, counter-recommendation):
- **Drift monitors** over the outcome/longitudinal store (feature, prediction, embedding drift; PSI/JS thresholds).
- **Exploration policy** + **propensity logging** to break the degenerate loop.
- **Human-labeled anchor set** sourced from Article-14 reviews.
- **Governed retrain-and-re-audit gate:** retraining triggers a *proposal*, never a live swap — version, model card, fairness/adverse-impact re-run, human approval, disclosure refresh.
- **Guardrail dashboard:** adverse-impact (four-fifths, intersectional) as a release-blocking metric.

---

*Methodology note: synthesized from a multi-source review (independent studies, primary regulatory/court documents, vendor docs, and engineering literature). Vendor metrics are directional; regulatory dates are fast-moving and must be re-verified against primary sources before compliance decisions.*
