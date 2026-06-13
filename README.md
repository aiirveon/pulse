# Pulse — AI Audience Sentiment Monitor for Live Broadcasting

Real-time audience sentiment classification for UK broadcast producers.

Pulse classifies social media posts by emotion and topic during live broadcast
events — BAFTAs, election nights, live finals — and surfaces the result in a
dashboard a gallery producer can read in under 5 seconds. It is designed for
the editorial decision window: 3 to 10 seconds, flying blind on how the
audience is reacting. Every classification carries a confidence score.
Every design decision is constrained by the principle that audience signals
inform editorial judgement — they do not replace it.

---

## Demo

[Live demo](TODO: paste Vercel URL)

The backend runs on Render free tier and takes approximately 30–50 seconds
to wake on first load. The frontend handles this with a WARMING UP state and
automatic retry — no manual refresh needed.

<!-- TODO: add screenshot or GIF of the dashboard during the controversy spike.
     Ideal moment: the negative-sentiment alert firing during the scripted
     diversity_representation controversy arc, showing the alert banner,
     the sentiment chart tipping negative, and a feed post labelled ANGRY
     with an "est." confidence badge. Drop the file in public/ and update
     this line with: ![Alert firing during controversy spike](public/your-screenshot.png) -->

---

## Architecture

A synthetic feed generator (or manual input from the producer) sends posts
to a FastAPI backend, which classifies each post and returns emotion, topic,
confidence score, and SHAP word highlights. The Next.js frontend polls the
backend on an interval and updates the live sentiment chart, topic heatmap,
and alert banner in real time.

```
Synthetic Feed Generator (Python) / Manual Input
        |
        v
FastAPI Backend (Render)
  +-- POST /api/classify     -- single message -> emotion + topic + confidence
  +-- POST /api/feed/start   -- resets session, begins scripted arc
  +-- GET  /api/feed/next    -- returns next classified batch
  +-- GET  /api/stats        -- current session sentiment distribution
  +-- GET  /health           -- cold start wake
        |
        v
Next.js Frontend (Vercel)
  +-- Live Feed Panel        -- posts appearing in real time with emotion badges
  +-- Sentiment Chart        -- Recharts line chart, updates per batch
  +-- Topic Heatmap          -- multi-label topic counts and negative volume
  +-- Alert Banner           -- fires when negative + angry > 40% of last 30 posts
  +-- Editorial Guardrail    -- persistent footer: "Pulse surfaces audience signals.
                                Editorial decisions remain with the producer."
```

### Three-tier classification routing

Classification is not handled by a single model. `predictor.py` routes each
post by word count to the approach with the right signal-to-cost trade-off:

| Tier | Word count | Approach | Notes |
|------|-----------|----------|-------|
| 1 | <= 3 words | Rule-based low-confidence neutral | Too short to classify reliably by any method |
| 2 | 4-20 words | Claude API (Haiku) semantic classification | LLM has semantic signal TF-IDF lacks at short length |
| 3 | > 20 words | TF-IDF + XGBoost + SHAP | Fast, free per inference, calibrated probability |

Most tweet-length posts — including nearly all of the scripted demo feed —
go through Tier 2. Tier 3 handles longer posts and is the only tier with
SHAP word-level explainability.

---

## Results (honest)

The Tier 3 XGBoost emotion classifier achieved macro F1 0.830 on the held-out
test set. Two categories landed below their per-category targets and are
accepted as documented limitations:

- `negative` emotion: F1 0.750 (target 0.78). The failure mode is confusion
  with `angry` at the boundary between calm disappointment and cold sarcasm.
  Production mitigation: the alert threshold uses combined negative + angry,
  so the combined signal is reliable even where the boundary is imprecise.

- `general_audience_reaction` topic: F1 0.304. This category is defined by
  exclusion — it applies when no specific topic fits — which is structurally
  harder to learn. It is also the least actionable signal for a producer:
  a post saying "what a night" does not change any editorial decision.

These F1 numbers measure the Tier 3 XGBoost classifier only. Tier 2 (Claude
API) classification is not separately benchmarked in v1 — there is no offline
F1 figure for it, and none is claimed. This is the largest accuracy gap in v1
and is logged as the top v2 action item.

Full analysis, threshold rationale, and per-category breakdowns: [docs/MODEL_DECISIONS.md](docs/MODEL_DECISIONS.md)

---

## Design decisions worth highlighting

**Tiered hybrid architecture as a deliberate trade-off.** TF-IDF on a 4-word
post has almost no lexical signal; an LLM understands semantics at that
length. Posts above 20 words have enough signal for the classical model, which
is fast (under 10 ms), free per inference, and SHAP-explainable. Very short
fragments cannot be reliably classified by anything — Tier 1 returns an honest
low-confidence neutral rather than a confident guess. Each tier uses the
cheapest approach that can actually do the job.

**Confidence labelled by type, not treated as equivalent.** Tier 3 confidence
is `predict_proba` — a calibrated probability. Tier 2 confidence is a number
the LLM is prompted to produce between 0.70 and 0.95 — it reflects the
model's self-assessment, not a calibrated probability from a held-out
evaluation. The UI labels these differently ("est." badge on Tier 1 and Tier 2)
because presenting an LLM's self-reported certainty as a calibrated probability
would mislead the producer. This is a direct implementation of the Ethics
Framework principle that confidence must be honest.

**API failures are explicit, not silent.** If the Claude API call fails, the
classification returns `emotion: "unavailable"`, `degraded: true`, and an
error string. Degraded posts are excluded from the emotion counts, percentages,
and the negative-spike alert threshold. The alternative — a silent neutral
fallback — would drag down the negative percentage during an API outage and
suppress the alert during the exact scenario it exists to catch.

**Editorial-integrity guardrails as hard constraints.** The alert banner names
the signal ("Negative sentiment spike: Diversity & Representation"), never an
action. There is no recommendation anywhere in the interface. The editorial
guardrail footer is non-dismissible. These are not UX choices — they are
architecture requirements derived from the Ethics Framework's analysis of the
feedback loop risk: if producers consistently respond to sentiment spikes by
pivoting coverage, the signal degrades and editorial sovereignty is gradually
replaced by audience pressure.

---

## Documentation

This product was designed with four PM artefacts written before any code.

| Document | Description |
|---|---|
| [Opportunity Assessment](docs/OPPORTUNITY_ASSESSMENT.md) | Problem sizing, user/buyer/champion split, honest market analysis, build decision |
| [PRD](docs/PRD.md) | Functional requirements, success metrics, architecture overview |
| [Ethics Framework](docs/ETHICS.md) | Central ethical tension, hard constraints, feedback loop risk analysis, regulatory context |
| [Competitive Analysis](docs/COMPETITIVE_ANALYSIS.md) | Five competitors profiled, capability matrix, defensible position |

---

## Tech stack

**Backend**
- Python, FastAPI
- scikit-learn (TF-IDF vectoriser, OneVsRest topic classifier)
- XGBoost (emotion and topic classifiers)
- SHAP (word-level explainability on emotion classifier)
- Anthropic API / Claude Haiku (Tier 2 short-text classification)
- Deployed on Render free tier

**Frontend**
- Next.js, React, TypeScript
- Tailwind CSS
- Recharts (sentiment line chart, topic bar chart)
- Deployed on Vercel

---

## Run locally

### Backend

```bash
cd backend
pip install -r requirements.txt
```

The backend requires an Anthropic API key for Tier 2 (short-text) classification.
Create a `.env` file in `backend/`:

```
ANTHROPIC_API_KEY=your_key_here
```

```bash
uvicorn api.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend expects the backend at `http://localhost:8000` in development.
Check `frontend/.env.local` or the API base URL config if the backend is
running on a different port.

---

## What I would do differently / v1 limitations

**No user discovery yet.** The 3-to-10-second editorial decision window is
the core premise of the product, and it is reasoned from the PRD — it has
not been validated in conversation with a real gallery producer. Two or three
discovery interviews would either confirm the premise or revise it, and would
do more for the product's credibility than any further analysis. This is the
largest gap.

**In-memory session state shared across visitors.** The backend holds
`session_results` as a module-level list. In a multi-visitor demo, one
visitor's feed run overwrites another's stats. This is a known v1 limitation
acceptable for a single-session portfolio demo, and would require a
session-keyed store (Redis or similar) before any real deployment.

**Tier 2 is not offline-benchmarked.** The F1 tables in the documentation
measure the Tier 3 XGBoost classifier. Most posts in the live demo go through
Tier 2. There is no held-out evaluation of Tier 2 accuracy. The v2 action
item is to build a labelled short-post eval set (200+ posts, 4–20 words) and
report per-emotion F1 for the Claude API path, with a formal accuracy threshold
equivalent to the Tier 3 threshold.
