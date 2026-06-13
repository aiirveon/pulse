# OPPORTUNITY ASSESSMENT

**Product:** Pulse — AI Audience Sentiment Monitor for Live Broadcasting
**Author:** Ogbebor Osaheni
**Date:** March 2026
**Status:** v1 shipped — June 2026
**GitHub:** https://github.com/aiirveon/pulse

---

## 0. How to read this document

This is the first of four PM artefacts written before any code (OA → PRD → Ethics Framework → Competitive Analysis). Its purpose is to decide whether the problem Pulse addresses is worth solving at all, and on what terms, before committing to a build.

A note on intent, stated plainly because it changes how the rest should be judged: Pulse is a portfolio product. Its primary "customer" is a hiring manager assessing whether I can run the reasoning an AI product manager runs when sizing an opportunity — separating user from buyer, naming the risks honestly, and deciding to build with eyes open. The commercial scenario assessed below (a UK broadcaster as institutional buyer) is real and reasoned, not aspirational; but the document does not pretend Pulse is a venture seeking a market. Where the market is small or the build-vs-buy case is weak, this document says so rather than arguing around it.

---

## 1. The problem

Live broadcast producers make editorial decisions in real time with no structured read on how the audience is reacting. During high-stakes live events — awards ceremonies, election nights, live finals — audience reaction exists in large volume on social platforms, but it reaches the gallery too late, too unstructured, and too noisy to act on inside the 3–10 second windows in which a producer actually decides.

The reaction is not missing. It is unusable at the speed and in the form the decision requires. That is the gap Pulse targets: classified audience sentiment, by emotion and topic, with a confidence score, readable at a glance.

### Who feels it

| Role | Relationship to the problem |
|---|---|
| Gallery producer | Feels it most acutely — decides in seconds, currently flying blind on audience reaction |
| Social media editor | Today's workaround — reads raw feeds in a side room, relays to the gallery via Slack |
| Editorial director | Feels it indirectly — owns the consequences of editorial decisions made without good information |

The current state at most UK broadcasters is the third row of the Competitive Analysis: a person in a separate room reading social posts manually and messaging the gallery. It is inconsistent, unscalable, and runs 5–15 minutes behind the event. That manual workaround is the real incumbent — not a competing product.

---

## 2. Why now

Three things make this solvable in 2026 that were not true a few years ago:

1. **Classification quality at low cost.** Short-text emotion and topic classification is now achievable to a useful standard with classical ML (TF-IDF + gradient boosting) for long text and an LLM API for short ambiguous text, at a per-post cost measured in fractions of a penny. Real-time classified sentiment no longer requires an enterprise data-science pipeline.

2. **Synthetic data closes the cold-start gap.** A credible, class-balanced training set can be generated for roughly $1 in API cost, sidestepping the consent, GDPR, and labelling-cost barriers that previously made a niche classifier expensive to start. This is a deliberate v1 privacy decision, not only a convenience — see the Ethics Framework.

3. **Editorial scrutiny is rising, not falling.** Ofcom impartiality expectations and internal editorial-integrity concerns make a tool that is *designed* not to drive coverage — classification without recommendation — more defensible now than a generic "engagement maximiser" would be.

---

## 3. User, buyer, champion

The most important distinction in this assessment: the person who *uses* Pulse is not the person who *pays* for it, and neither is necessarily the person who *advocates* for it internally. Conflating these is the most common way a B2B tool with real user value still fails to sell.

| Layer | Who | What they care about |
|---|---|---|
| **User** | Gallery producer | Can I read it in 3 seconds and trust it? |
| **Economic buyer** | UK broadcaster — technology or editorial-operations budget | Does this fit editorial policy and reduce risk without adding headcount? |
| **Champion** | Senior producer or editorial-systems lead | Does this solve a pain I personally feel and can defend to my director? |

Producers do not hold software budgets; the broadcaster as an institution does. The Ofcom / BBC Editorial Guidelines framing built into Pulse is aimed squarely at the buyer layer — it is what turns "a sentiment dashboard" into "a tool that fits our compliance posture." The single-producer scoping is aimed at the champion: it is the feature that lets a senior producer adopt it without triggering an org-wide integration review.

### Why not the other candidate buyers

- **Production companies** make individual live shows but rent capability per production and rarely carry standing software. Fragmented, project-based, thin margins — a hard first customer.
- **Social / audience-insight teams** would recognise the problem fastest and already buy tools like Brandwatch and Pulsar — but they would push Pulse toward exactly the broadcast-wide deployment the Ethics Framework deliberately designs against. Selling to them would mean compromising the product's central integrity constraint.

---

## 4. Market sizing (honest, not inflated)

This is a deliberately narrow market, and the assessment treats that as a finding rather than a problem to argue away.

- **Realistic buyer set:** the major UK broadcasters — BBC, ITV, Channel 4, Sky — plus a small number of large production companies handling live tentpole events. That is a single-digit-to-low-double-digit count of serious institutional buyers in the UK.
- **Usage occasions are episodic, not continuous.** The tool earns its value during a handful of high-stakes live events per broadcaster per year, not in daily always-on use. This caps natural willingness-to-pay and argues for an event/seat-based model over a heavy annual platform licence.
- **Adjacent expansion exists but is unproven:** other live formats (election nights, sporting finals, music awards) and other English-language markets with comparable regulatory regimes. These are noted as a v2 direction in MODEL_DECISIONS.md, not counted in the v1 case.

**Conclusion:** the addressable market is small and episodic. That is acceptable for the stated purpose. It would be a serious obstacle for a venture, and a real assessment should say so — which is the point of writing this section honestly rather than reaching for a large top-down number.

---

## 5. Why Pulse, specifically

The defensible position is the intersection of four properties no single existing tool combines (full detail in the Competitive Analysis):

1. **Real-time + structured** — classified, confidence-scored results in under 2 seconds, where enterprise listening tools take minutes to hours.
2. **Producer-scoped interface** — built for a 3-second glance, not a 30-minute report.
3. **Editorial-integrity framing** — the only design that treats the audience-feedback loop as a hard constraint rather than ignoring it.
4. **UK regulatory alignment** — Ofcom Broadcasting Code and BBC Editorial Guidelines referenced as design inputs, not marketing.

The first two are capability differences a competitor could close. The last two are the genuinely defensible part, because they are *product philosophy* choices that run against the commercial grain of an engagement-maximising tool — a competitor would have to want to build a deliberately self-limiting product, which most do not.

---

## 6. Risks and what would kill this

Stated directly, then weighed.

| Risk | Severity | Assessment |
|---|---|---|
| **Small, episodic market** | High | Real and unresolved. Acceptable for a portfolio piece; disqualifying for a standalone venture. |
| **Build-vs-buy** — a broadcaster builds it internally | High | BBC R&D and Channel 4's data team have the capability. If they build it, Pulse becomes a demonstration of the problem space — which is its stated primary purpose, so this is not a fatal outcome here. |
| **Incumbent extends down-market** — Brandwatch adds a real-time producer view | Medium | Possible but against their enterprise-marketing commercial model; they have not, for structural reasons, not technical ones. |
| **Editorial-integrity risk in use** — the feedback loop | Medium | The deepest product risk, addressed structurally in the Ethics Framework rather than dismissed. |
| **Signal representativeness** — social audience ≠ broadcast audience | Medium | Cannot be solved, only disclosed. Handled via a persistent demographic caveat in the UI. |

The two High risks both point to the same honest conclusion: Pulse is a strong demonstration of product judgement and a weak standalone business. For the stated purpose, that is the correct trade, and naming it is more credible than hiding it.

---

## 7. Decision

**Build it — as a portfolio product, scoped to a single live event (BAFTA 2026), with editorial integrity as a hard design constraint.**

The opportunity is worth pursuing not because the market is large — it is not — but because the problem is real, sharply defined, and unusually rich in the trade-offs an AI PM is hired to navigate: a genuine user/buyer/champion split, a real latency-vs-cost-vs-explainability model decision, and an ethics constraint that actively conflicts with the easiest path to revenue. A product that surfaces those trade-offs and resolves them deliberately is the right thing to build for this purpose.

The success criteria therefore are not commercial. They are the metrics in the PRD (§3) — classification quality, glanceable interface, honest handling of limitations — and the quality of the four PM artefacts this document opens.

---

## 8. What I would do differently with more time

- **Talk to real users.** This assessment reasons about gallery producers; it does not yet quote one. Two or three discovery conversations with people who have worked in live TV would either validate the 3-second-window premise or revise it, and would do more for the document's credibility than any further analysis. This is the largest gap and is logged as the top follow-up.
- **Pressure-test willingness-to-pay** with one broadcaster contact rather than inferring it from market structure.
- **Validate the manual-monitoring baseline** (the 5–15 minute latency claim) against someone who has actually run that workaround in a gallery.
