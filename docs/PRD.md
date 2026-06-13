# PRODUCT REQUIREMENTS DOCUMENT
**Product:** Pulse — AI Audience Sentiment Monitor for Live Broadcasting
**Author:** Ogbebor Osaheni
**Date:** March 2026
**Status:** v1 shipped — June 2026
**GitHub:** https://github.com/aiirveon/pulse

---

### 1. Problem

Live broadcast producers at UK broadcasters make editorial decisions in real time with no structured audience intelligence. During high-stakes events — the BAFTAs, election nights, live finals — audience reaction exists in volume on social media but reaches the gallery too late, too unstructured, and too noisy to act on.

The gap: a tool that classifies audience sentiment in real time, by topic and emotion, in a format a producer can read in under 5 seconds and act on immediately.

---

### 2. User

**Primary:** Live broadcast producer — controls running order, presenter cues, segment timing during a live event. Sits in the gallery. Makes decisions in 3–10 second windows. Does not have time to read raw social posts.

**Out of scope for v1:** Social media editor, editorial director, post-broadcast analytics teams. These are v2 personas.

---

### 3. Success Metrics

| Metric | Target | How measured |
|---|---|---|
| Sentiment classification F1 | > 0.82 across all emotion categories | Test set evaluation |
| Topic classification F1 | > 0.80 across all topic categories | Test set evaluation |
| Dashboard read time | Glanceable in < 5 seconds | Design review |
| Auto-feed simulation | 200+ messages, scripted narrative arc | Manual count |
| Demo uptime | Public URL live, cold start handled | Deployment check |
| PM artefacts | 4 documents committed before first line of code | GitHub commit history |

**Results vs targets (v1):** The macro emotion F1 target (> 0.82) was substantially met at 0.830, but two categories landed below their per-category targets: `negative` emotion at 0.750 and `general_audience_reaction` topic at 0.304. Both were accepted as documented limitations rather than blockers — the full rationale, failure analysis, and production mitigations are in `docs/MODEL_DECISIONS.md` §5. The targets above are preserved as originally written; this note reconciles them against shipped results.

---

### 4. Functional Requirements

**FR-01 — Real-time feed simulation (P0)**
The system must simulate a live social media feed during a BAFTA broadcast event. Pre-written synthetic messages must be released at a controlled rate (3–5 per second). The feed must follow a scripted narrative arc with at least three sentiment shifts — opening excitement, controversy spike, recovery. A pause/resume control must be available.

**FR-02 — Manual message input (P0)**
A producer must be able to type any message into an input field and receive a classification result within 2 seconds. The result must appear in the dashboard alongside auto-feed results without disrupting the live simulation.

**FR-03 — Sentiment classification (P0)**
Every message must be classified into one of five emotion categories: Excited, Positive, Neutral, Negative, Angry. Classification must include a confidence score. Low confidence results (< 0.65) must be visually distinct — not hidden, not removed.

**FR-04 — Topic classification (P0)**
Every message must be classified into one of six BAFTA-relevant topic categories: Winner Reaction, Presenter Performance, Ceremony Production, Diversity & Representation, Fashion & Red Carpet, General Audience Reaction. A single message may carry multiple topic labels (multi-label classification).

**FR-05 — Live sentiment dashboard (P0)**
A real-time chart must show sentiment distribution over time — updating as each message is classified. The producer must be able to see at a glance: current dominant sentiment, sentiment trend over the last 60 seconds, and any sudden spikes or drops.

**FR-06 — Topic heat map (P1)**
A panel showing which topics are generating the most volume and the most negative sentiment in real time. Lets the producer see not just how the audience feels but what they are feeling about.

**FR-07 — Alert system (P1)**
If negative or angry sentiment exceeds 40% of the last 30 messages, a visual alert must fire. The alert must name the dominant negative topic. This is the feature that makes the tool actionable — not just informational.

**FR-08 — Editorial guardrail display (P1)**
A persistent on-screen reminder — not a modal, not a popup — that reads: *"Pulse surfaces audience signals. Editorial decisions remain with the producer."* This is not a UX flourish. It is an ethics constraint built into the interface, as documented in the Ethics Framework.

**FR-09 — Session summary (P2)**
At the end of a simulated broadcast session, a summary panel showing: peak sentiment moment, most discussed topic, sentiment arc overview. Exportable as a one-page PDF for post-broadcast editorial review.

**FR-10 — Cold start handling (P0)**
The FastAPI backend on Render free tier takes 30–50 seconds to wake. The frontend must handle this gracefully — silent health ping on load, WARMING UP state shown to user, auto-retry until live. Same pattern as Bias Audit.

---

### 5. Non-Functional Requirements

- **Latency:** Classification result must return within 2 seconds of message submission
- **Accuracy floor:** No emotion category may fall below F1 0.78 (same threshold as Bias Audit — consistent standard)
- **Confidence transparency:** Confidence score shown on every result — never hidden
- **Privacy:** No real user data. Synthetic dataset only. Documented as deliberate choice in MODEL_DECISIONS.md
- **Accessibility:** Dashboard readable without colour alone — sentiment shown with both colour and label

---

### 6. Out of Scope — v1

- Real Twitter/X API integration
- User authentication
- Multi-event support (v1 is BAFTA only)
- Mobile optimised layout
- Historical broadcast comparison

---

### 7. Architecture Overview

```
Synthetic Feed Generator (Python script)
        ↓
FastAPI Backend (Render)
  ├── POST /api/classify     — single message → emotion + topic + confidence
  ├── POST /api/feed/start   — begins timed message release
  ├── GET  /api/feed/next    — returns next batch of messages
  ├── GET  /api/stats        — current session sentiment distribution
  └── GET  /health           — cold start wake
        ↓
Next.js Frontend (Vercel)
  ├── Live Feed Panel        — messages appearing in real time
  ├── Sentiment Chart        — recharts line chart, updates per message
  ├── Topic Heatmap          — recharts bar chart, multi-label counts
  ├── Alert Banner           — fires on negative threshold breach
  └── Editorial Guardrail    — persistent footer label
```

---

### 8. ML Model Decisions (to be detailed in MODEL_DECISIONS.md)

- **Emotion classification:** TF-IDF + XGBoost, 5-class single-label
- **Topic classification:** TF-IDF + XGBoost, 6-class multi-label (one-vs-rest)
- **Training data:** 2,000–3,000 synthetic BAFTA social posts generated via Claude API
- **Confidence scoring:** XGBoost `predict_proba` — shown on every result
- **SHAP:** Applied to emotion classifier — word-level highlights on manual input results

---

### 9. Phased Delivery

| Phase | Deliverable | Done when |
|---|---|---|
| Phase 0 | PM artefacts: OA, PRD, Ethics, Competitive Analysis | 4 docs committed to GitHub |
| Phase 1 | Synthetic dataset + trained models (emotion + topic) | F1 > 0.82 on test set |
| Phase 2 | FastAPI backend — 5 endpoints deployed to Render | /health returns 200 |
| Phase 3 | Next.js frontend — 3 panels deployed to Vercel | Public URL live |
| Phase 4 | Scripted narrative arc — auto-feed tells BAFTA story | 3 sentiment shifts visible in demo |

