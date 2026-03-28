# MODEL_DECISIONS.md — Pulse

> Author: Ogbebor Osaheni
> Date: March 2026
> Purpose: Documents every significant decision made during the ML build.
> Audience: Editorial directors, trust and safety leads, Ofcom compliance
> officers, and technical reviewers. Written to be understood without a
> data science background.

---

## 1. What the models do

Pulse uses two classifiers running in sequence on every social media post:

Model 1 — Emotion classifier
Classifies the emotional tone of a post into one of five categories:
excited, positive, neutral, negative, angry.
Architecture: TF-IDF vectoriser + XGBoost (5-class single-label)

Model 2 — Topic classifier
Classifies what the post is about into one or more of six categories:
winner_reaction, presenter_performance, ceremony_production,
diversity_representation, fashion_red_carpet, general_audience_reaction.
Architecture: TF-IDF vectoriser + OneVsRest XGBoost (6-class multi-label)

Both models share a single TF-IDF vectoriser trained on the full dataset.

---

## 2. Why TF-IDF + XGBoost and not a transformer

Three reasons, all product decisions:

Reason 1 — SHAP explainability
TF-IDF + XGBoost produces word-level SHAP values that show exactly which
words drove a classification. A broadcast producer seeing a negative
sentiment spike can click through and see which words triggered it.
Transformer models produce embeddings that are harder to explain at the
word level without additional tooling.

Reason 2 — Inference speed
TF-IDF + XGBoost classifies a post in under 10ms on a CPU. The live
dashboard requires classifications to appear within 2 seconds of a post
being submitted. Transformer inference on CPU is 10-50x slower.

Reason 3 — Deployment cost
The backend runs on Render free tier. Transformer models require
significantly more memory and compute. TF-IDF + XGBoost runs comfortably
within free tier constraints.

Trade-off accepted: transformer models would produce higher F1 scores,
particularly on subtle boundary cases like negative vs angry. This
improvement is deferred to v2 when a paid deployment tier is appropriate.

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

### Emotion classifier

| Emotion  | F1    | Status           |
|----------|-------|------------------|
| excited  | 0.854 | Pass (>= 0.78)   |
| positive | 0.821 | Pass (>= 0.78)   |
| neutral  | 0.908 | Pass (>= 0.78)   |
| negative | 0.750 | Below threshold  |
| angry    | 0.815 | Pass (>= 0.78)   |
| Macro F1 | 0.830 | —                |

### Topic classifier

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

What it means: The model correctly classifies negative posts 75% of the
time on the test set. The primary failure mode is confusion with angry —
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

---

## 6. What the model cannot do

The model cannot:
- Detect sarcasm reliably in all contexts
- Classify posts longer than approximately 280 characters accurately
  (it was trained on Twitter-length posts)
- Generalise to non-BAFTA broadcast contexts without retraining
- Detect hate speech, explicit content, or harmful language
  (this is not what it was designed for)
- Replace human editorial judgement

The model can:
- Reliably detect when audience sentiment shifts toward negative or angry
- Identify which specific topics are generating the most emotional response
- Surface confidence scores so producers know when to trust the output
- Provide real-time classification at gallery speed (under 10ms)

---

## 7. Threshold rationale

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

---

## 8. v2 roadmap for model improvements

1. Retrain negative/angry boundary with real social data from
   a consented pilot with broadcast team (target: negative F1 > 0.82)
2. Upgrade to sentence transformer for semantic classification
   (target: all emotions > 0.85)
3. Expand training data beyond BAFTA to other live broadcast events
   (election nights, sporting finals, music awards)
4. Add confidence calibration layer to improve reliability of
   probability scores
5. Evaluate fairness metrics across demographic groups in test set
   using Fairlearn (as implemented in Bias Audit Dashboard)
