# COMPETITIVE ANALYSIS

**Product:** Pulse — AI Audience Sentiment Monitor for Live Broadcasting
**Author:** Ogbebor Osaheni
**Date:** March 2026
**Status:** v1 shipped — June 2026

---

## 1. The Market

Social listening and sentiment analysis is a crowded space. But almost every tool in it is built for marketing teams, not broadcast producers. The distinction matters: a marketing team has hours to interpret a report. A gallery producer has 3 seconds to glance at a screen. No existing tool is designed for that constraint.

---

## 2. Competitors Profiled

### Brandwatch

The dominant enterprise social listening platform. Used by major UK broadcasters for post-broadcast analysis and brand monitoring. Produces detailed reports, trend graphs, and demographic breakdowns.

- **Built for:** Marketing and communications teams
- **Latency:** Reports generated over minutes to hours — not real-time
- **Gap:** No live broadcast producer workflow. No gallery-ready interface. No event-scoped sentiment arc.

### Sprout Social

Social media management platform with built-in sentiment analysis. Strong for scheduled content performance tracking.

- **Built for:** Social media managers
- **Latency:** Near real-time for monitored keywords but requires manual query setup per event
- **Gap:** Not scoped to live broadcast events. No topic classification. No editorial guardrail framing.

### Pulsar

UK-based audience intelligence platform used by Channel 4 and BBC for audience research. Strong demographic segmentation and cultural trend analysis.

- **Built for:** Audience research and strategy teams
- **Latency:** Batch processing — daily or weekly reports
- **Gap:** Explicitly post-event. No live dashboard capability. No producer-facing interface.

### Twitter/X Live Event Pages

Twitter's native event pages aggregate tweets around a live event in real time. Used informally by producers during broadcasts.

- **Built for:** General audience — not producers
- **Latency:** Real-time
- **Gap:** Raw unclassified feed. No sentiment scoring. No topic classification. No confidence scoring. No editorial guardrail. Noise-to-signal ratio too high for gallery use.

### Manual Monitoring (the real competitor)

A social media editor in a separate room reading tweets and sending Slack messages to the gallery producer. This is the actual workflow at most UK broadcasters today.

- **Built for:** This is not a product — it is a workaround
- **Latency:** 5–15 minutes from event to producer awareness
- **Gap:** Inconsistent, unscalable, dependent on individual attention and judgement

---

## 3. Capability Matrix

| Capability | Pulse | Brandwatch | Sprout Social | Pulsar | Twitter/X | Manual |
|---|---|---|---|---|---|---|
| Real-time classification (< 2s) | ✅ | ❌ | ⚠️ | ❌ | ✅ raw only | ❌ |
| Emotion classification (5 categories) | ✅ | ⚠️ basic | ⚠️ basic | ❌ | ❌ | ❌ |
| Topic classification (multi-label) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Confidence score on every result | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Gallery-ready interface (< 5s read) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Negative sentiment alert system | ✅ | ⚠️ email only | ⚠️ email only | ❌ | ❌ | ❌ |
| Editorial guardrail built into UI | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Event-scoped (BAFTA context) | ✅ | ❌ | ❌ | ❌ | ⚠️ | ✅ |
| SHAP explainability | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Ofcom/BBC Guidelines framing | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Price | Free (open source) | £££ enterprise | ££ | £££ enterprise | Free | Staff cost |

---

## 4. Positioning Statement

Pulse is the only tool designed specifically for the live broadcast producer workflow — classifying audience sentiment by emotion and topic in real time, at gallery speed, with confidence scoring, editorial guardrails, and UK broadcasting regulatory framing built in.

Every existing tool is either too slow (Brandwatch, Pulsar), too noisy (Twitter/X), too generic (Sprout Social), or not a product at all (manual monitoring). Pulse is not competing with enterprise social listening platforms. It is filling a gap those platforms were never designed to address.

---

## 5. Defensible Position

The defensible position is the intersection of four things no single competitor has together:

- **Real-time + structured** — classified, confidence-scored results in under 2 seconds
- **Producer-scoped interface** — designed for a 3-second glance, not a 30-minute report
- **Editorial integrity framing** — the only tool that treats the feedback loop risk as a design constraint
- **UK regulatory alignment** — Ofcom Broadcasting Code and BBC Editorial Guidelines referenced explicitly

---

## 6. Risk: If Brandwatch Builds This

Brandwatch has the data, the engineering resource, and the broadcaster relationships to build a real-time producer dashboard if they chose to. They haven't — because their commercial model is built on enterprise contracts with marketing teams, not on individual producer tooling.

The more credible risk is a broadcaster building this internally. BBC R&D and Channel 4's data team have the capability. If they do, Pulse becomes a portfolio demonstration of the problem space rather than a market product — which is its primary purpose.
