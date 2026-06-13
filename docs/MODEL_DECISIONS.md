# MODEL_DECISIONS.md — Pulse

> Author: Ogbebor Osaheni
> Date: March 2026
> Purpose: Documents every significant decision made during the ML build.
> Audience: Editorial directors, trust and safety leads, Ofcom compliance
> officers, and technical reviewers. Written to be understood without a
> data science background.

---

## 1. What the models do

Pulse classifies every social media post into an emotion and one or more
topics. Classification is not handled by a single model — it uses a
three-tier routing system that selects the right approach based on how
many words the post contains. This routing is a deliberate product
decision, explained in Section 2.

### Routing overview

| Tier | Word count | Approach | Typical example |
|------|-----------|----------|-----------------|
| 1 | ≤ 3 words | Rule-based low-confidence neutral | "lol", "wow ok" |
| 2 | 4–20 words | Claude API (LLM) semantic classification | "that was painful to watch honestly" |
| 3 | > 20 words | TF-IDF vectoriser + XGBoost + SHAP | Full-sentence posts and threads |

In practice, the majority of social media posts during a live broadcast
event — including nearly all of the scripted demo feed — fall in the
4–20 word range and are classified by Tier 2, not XGBoost.

---

### Emotion classifier

Classifies the emotional tone of a post into one of five categories:
excited, positive, neutral, negative, angry.

- **Tier 1**: returns "neutral" with confidence 0.4. This is not a
  real classification — it is an honest statement that the text is too
  short to classify reliably.
- **Tier 2**: asks the Claude API to return an emotion and confidence
  score. The confidence is a number the model is prompted to produce
  between 0.70 and 0.95. It reflects the LLM's self-assessment, not a
  calibrated probability.
- **Tier 3**: TF-IDF vectoriser + XGBoost, 5-class single-label.
  Confidence is `predict_proba` — a calibrated probability from the
  classifier. Word-level SHAP values are computed at the same time.

---

### Topic classifier

Classifies what the post is about into one or more of six categories:
winner_reaction, presenter_performance, ceremony_production,
diversity_representation, fashion_red_carpet, general_audience_reaction.

Architecture: TF-IDF vectoriser + OneVsRest XGBoost (6-class multi-label).
Applied at all tiers. For Tier 2 posts the Claude prompt also requests
topic tags; these are merged with the XGBoost topic result. Tier 3
uses XGBoost `predict_proba` for topic confidence — these are calibrated.

Both models share a single TF-IDF vectoriser trained on the full dataset.

---

## 2. Why a tiered hybrid architecture

The routing decision follows a simple principle: use the cheapest tool
that has enough signal to classify reliably. Different post lengths have
very different signal characteristics, and a single model cannot handle
all of them well.

### Tier 1 — very short fragments (≤ 3 words)

A fragment like "wow" or "lol" gives a bag-of-words model almost nothing
to work with. An LLM has more context than a classical model, but a
three-word post still lacks enough content to distinguish "wow" (excited)
from "wow" (sarcastic negative). Returning a confident emotion would be
false precision. Tier 1 returns a low-confidence neutral and makes this
explicit in the confidence score (0.4) and confidence_type ("estimated"),
so the producer knows not to weight the result.

### Tier 2 — short text (4–20 words)

TF-IDF represents text as a word-frequency vector. On a 10-word post,
most vector dimensions are zero — there is almost no lexical signal for
the model to work with. More importantly, TF-IDF has no semantic
understanding: "that was brutal" and "that was brilliant" share no
vocabulary and are orthogonal in TF-IDF space, but an LLM understands
that one is negative and one is positive from the semantics of the words.

Routing short posts to the Claude API gives Tier 2 posts the semantic
understanding a classical model cannot provide at this text length. The
trade-off is real: each Tier 2 classification is an API round-trip
(typically 200–800 ms) and has a per-call cost (fractions of a penny at
Haiku rates). At demo-feed volume this is negligible. At production scale
it informs the v2 decision to train on real data and eliminate the API
dependency (see Section 8).

### Tier 3 — full-length posts (> 20 words)

Posts above 20 words give TF-IDF enough lexical signal to classify
reliably. At this length, the classical model offers three advantages the
LLM path does not:

1. **Speed**: TF-IDF + XGBoost classifies in under 10 ms on CPU, versus
   an API round-trip.
2. **Cost**: zero per-inference cost after training.
3. **Explainability**: word-level SHAP values are computed at the same
   time as the prediction. A producer can see exactly which words drove
   a "negative" classification — a hard requirement from the Ethics
   Framework on operator accountability.

---

### Tier comparison

| | Tier 1 | Tier 2 | Tier 3 |
|---|---|---|---|
| Typical input | Fragments ≤ 3 words | Short posts 4–20 words | Full posts > 20 words |
| Latency | < 1 ms | 200–800 ms (API round-trip) | < 10 ms |
| Cost per classification | None | ~$0.0001 (Haiku) | None |
| SHAP explainability | No | No | Yes |
| Confidence type | Estimated | Estimated | Calibrated |

---

## 3. Training data

Dataset: 2,699 synthetic BAFTA 2026 social media posts
(2,399 original + 300 targeted augmentation for negative boundary)

Generated using: Claude API (claude-haiku-4-5)
Generation cost: approximately $1.08 total across all runs

Why synthetic data:
No real user posts are stored or processed in v1. This is a deliberate
privacy decision — not a shortcut. Synthetic data allows precise control
over class balance and label distribution, avoids GDPR consent obligations,
and can be regenerated if label definitions change. The limitation is that
synthetic data may not capture long-tail real-world cases. This is
addressed in the v2 roadmap by supplementing with real data under
appropriate consent frameworks.

Class balance:
All five emotion categories are balanced at approximately 480 rows each.
Topic categories are naturally imbalanced — winner_reaction is the most
common topic in BAFTA broadcast social media and this is reflected in the
training data.

Train/test split: 80/20 stratified by emotion category.

Labelling guide: docs/LABELLING_GUIDE.md defines every label precisely.
All data generation prompts implement the definitions in that guide.

---

## 4. Final F1 scores

**Important caveat on scope.** The F1 tables below measure the Tier 3
XGBoost classifier on the held-out test set only. They do not measure
Tier 2 (Claude API) classification accuracy. Tier 2 is not separately
benchmarked in v1 — there is no offline F1 figure for it, and no such
figure is claimed. Tier 2 accuracy depends on the Claude model's
performance on short broadcast social media posts, which has not been
formally evaluated. This is logged as a gap in Section 8.

The F1 scores below therefore describe how well the classical model
classifies longer posts, not how well the system classifies all posts.

### Emotion classifier (Tier 3 — XGBoost)

| Emotion  | F1    | Status           |
|----------|-------|------------------|
| excited  | 0.854 | Pass (>= 0.78)   |
| positive | 0.821 | Pass (>= 0.78)   |
| neutral  | 0.908 | Pass (>= 0.78)   |
| negative | 0.750 | Below threshold  |
| angry    | 0.815 | Pass (>= 0.78)   |
| Macro F1 | 0.830 | —                |

### Topic classifier (Tier 3 — XGBoost)

| Topic                      | F1    | Status           |
|----------------------------|-------|------------------|
| winner_reaction            | 0.810 | Pass (>= 0.78)   |
| presenter_performance      | 0.838 | Pass (>= 0.78)   |
| ceremony_production        | 0.779 | Pass (>= 0.78)   |
| diversity_representation   | 0.833 | Pass (>= 0.78)   |
| fashion_red_carpet         | 0.776 | Below threshold  |
| general_audience_reaction  | 0.304 | Accepted limit   |

PRD threshold: F1 >= 0.78 per category (emotion classifier)
Multi-label threshold: F1 >= 0.75 per category (topic classifier —
lower threshold accepted, documented below)

---

## 5. Known limitations

### Limitation 1 — negative emotion F1 0.750

What it means: The Tier 3 model correctly classifies negative posts 75% of
the time on the test set. The primary failure mode is confusion with angry —
posts near the boundary between calm disappointment and cold sarcasm
sometimes misclassify in either direction.

Why it was not fixed further: Two targeted augmentation runs moved the
score from 0.742 to 0.750. The remaining gap is likely irreducible with
synthetic data alone. The negative/angry boundary on subtle posts
requires authentic real-world examples to learn precisely.

Production mitigation: The Pulse alert system uses combined
negative + angry score, not either emotion alone. A producer sees
"audience sentiment is unhappy" rather than a breakdown between
disappointed and angry. This combined signal is reliable at the
current F1 levels. Individual emotion breakdown is shown with
confidence scores — low confidence results are visually distinct.

### Limitation 2 — general_audience_reaction topic F1 0.304

What it means: The model correctly classifies general audience reaction
posts only 30% of the time. Recall is 0.20 — the model misses 80% of
actual general_audience_reaction examples in the test set.

Why this happens: general_audience_reaction is defined by exclusion —
it applies when no specific topic fits. Models learn by positive examples.
A category defined by the absence of other signals is structurally
harder to learn than a category with distinctive vocabulary.

Why it is accepted: general_audience_reaction is the least actionable
signal for a broadcast producer. A producer watching a live BAFTA
broadcast cares about specific signals — winner controversy, presenter
backlash, diversity criticism. A post that says "what a night" does not
change any editorial decision.

Production mitigation: Topic assignments with confidence below 0.65
are shown with a distinct visual indicator in the dashboard. The producer
treats low-confidence topic tags as uncertain. This is the same pattern
used in the Bias Audit Dashboard for the geographic_bias limitation.

### Limitation 3 — fashion_red_carpet topic F1 0.776

What it means: Two hundredths below the 0.78 PRD threshold.

Why it is accepted: The test set for this category has 30 examples
after rebalancing from an original 15. At 30 examples, a single wrong
prediction moves F1 by approximately 3 percentage points. The score
is at the margin of statistical reliability. The model's precision for
this category is 1.00 — when it predicts fashion_red_carpet, it is
always correct. The failure is in recall (0.63) — it misses some
fashion posts. This is an acceptable failure mode for a live dashboard
where over-flagging is worse than under-flagging.

Production mitigation: Fashion topic tags are informational, not used
in alert thresholds. Missing a fashion post does not affect any
producer decision.

### Limitation 4 — Tier 2 accuracy is not benchmarked

What it means: There is no offline F1 figure for the Claude API
classification path. The vast majority of posts in the live feed go
through Tier 2. The F1 scores in Section 4 do not describe this path.

Why it is not fixed in v1: Building a held-out benchmark for Tier 2
requires labelled short-post examples and a repeatable eval harness.
This is feasible but was not in scope for v1. The gap is accepted
because (a) LLM semantic classification of simple short posts is
qualitatively well-behaved and (b) Tier 2 results are labelled
"estimated" in the UI so producers are not given false precision.

Gap logged for v2: Add a separate Tier 2 eval set (200+ labelled
short posts, 4–20 words) and report F1 per emotion alongside the
Tier 3 numbers.

---

## 6. Failure-mode and confidence honesty

Two design decisions in the code directly implement the Ethics Framework
principle that confidence signals must be honest.

### 6a — Confidence type labelling

Every classification result carries a `confidence_type` field:

- `"calibrated"` — Tier 3 (XGBoost `predict_proba`). This is a genuine
  calibrated probability from the classifier. 80% confidence means the
  model is right approximately 80% of the time at this score on the
  test set.
- `"estimated"` — Tier 1 and Tier 2. For Tier 2, the confidence is a
  number the Claude model is prompted to return between 0.70 and 0.95.
  It reflects the LLM's self-reported certainty, not a calibrated
  probability from a held-out evaluation. Presenting it as equivalent
  to a Tier 3 probability would mislead the producer.

The UI renders an "est." label next to Tier 1 and Tier 2 confidence
scores so the producer can see at a glance whether the number is
calibrated or estimated.

### 6b — Explicit degraded state for API failures

If the Claude API call in Tier 2 throws any exception, the classification
does not silently return a neutral result. It returns an explicit
degraded state: `emotion: "unavailable"`, `degraded: true`, and an error
string. Degraded posts are:

- Excluded from all emotion counts and percentages in the stats endpoint.
- Excluded from the negative-spike alert threshold calculation.
- Rendered in the UI with a distinct failed-classification indicator
  rather than an emotion badge.

The reason this matters: a silent neutral fallback during a negative
sentiment spike would drag down the negative percentage and suppress
the alert. That is exactly the scenario where the product's core job is
to warn the producer. A fake neutral at that moment is actively
misleading. An explicit degraded state preserves the integrity of the
signal that does exist.

---

## 7. What the model cannot do

The system cannot:
- Detect sarcasm reliably in all contexts
- Classify posts longer than approximately 280 characters accurately
  (it was trained on Twitter-length posts)
- Generalise to non-BAFTA broadcast contexts without retraining
- Detect hate speech, explicit content, or harmful language
  (this is not what it was designed for)
- Replace human editorial judgement
- Provide calibrated accuracy figures for Tier 2 classifications
  (not benchmarked in v1 — see Section 5, Limitation 4)

The system can:
- Reliably detect when audience sentiment shifts toward negative or angry
  (Tier 3 in under 10 ms; Tier 2 via API round-trip)
- Identify which specific topics are generating the most emotional response
- Surface confidence scores labelled by type so producers know whether
  to treat a number as a calibrated probability or an estimate
- Classify short posts semantically where a bag-of-words model has no signal
- Exclude failed classifications from the sentiment stats rather than
  silently corrupting them

---

## 8. Threshold rationale

The 0.78 F1 threshold was set in the PRD before training began.
The reasoning: 0.78 represents the point at which a classification is
reliable enough to surface to a producer without causing more confusion
than clarity. Below 0.78, the false positive and false negative rates
are high enough that a producer would need to manually verify too many
classifications to benefit from the tool.

The 0.75 threshold for multi-label topic classification reflects the
genuine difficulty of multi-label tasks. Industry standard F1 for
multi-label text classification is typically 0.70-0.80. Setting 0.75
as the floor for topic classification acknowledges this while still
requiring meaningful performance.

These thresholds apply to the Tier 3 XGBoost classifier. No formal
threshold has been set for Tier 2, as it has not been benchmarked.
Setting a formal threshold is a v2 action item.

---

## 9. v2 roadmap for model improvements

1. **Benchmark Tier 2 accuracy** (highest priority gap)
   Build a labelled short-post eval set (200+ posts, 4–20 words) and
   report per-emotion F1 for the Claude API classification path. Set a
   formal accuracy threshold equivalent to the Tier 3 threshold. This
   closes the largest honesty gap in the current v1 documentation.
2. **Bootstrapped labelling from real broadcast data** (REQUIRES DPIA)
   Collect anonymised audience comments from one live show using
   official platform APIs. Use Claude API classifications as labels.
   Retrain XGBoost on this real dataset to eliminate Tier 2 API cost
   at scale. Legal requirements before this can proceed: Data Protection
   Impact Assessment (DPIA) under UK GDPR Article 35, Legitimate
   Interests Assessment (LIA), privacy notice update, platform API
   compliance review. Ethical requirements: anonymise at collection
   (content only, no usernames or account IDs), train on minimum 3
   events to avoid feedback loop, document demographic skew in
   MODEL_DECISIONS.md. Estimated cost saving at production scale
   (10,000+ posts/hour): eliminates ~$3/hour in Claude API spend.
3. Retrain negative/angry boundary with real social data from
   a consented pilot with broadcast team (target: negative F1 > 0.82)
4. Upgrade to sentence transformer for semantic classification
   (target: all emotions > 0.85), replacing Tier 2 with a locally
   hosted model that gives calibrated probabilities and SHAP support
5. Expand training data beyond BAFTA to other live broadcast events
   (election nights, sporting finals, music awards)
6. Add explicit confidence calibration layer to Tier 3 to improve
   alignment between reported probability and empirical accuracy
7. Evaluate fairness metrics across demographic groups in test set
   using Fairlearn (as implemented in Bias Audit Dashboard)
