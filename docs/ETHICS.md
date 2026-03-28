ETHICS FRAMEWORK
Product: Pulse — AI Audience Sentiment Monitor for Live Broadcasting
Author: Ogbebor Osaheni
Date: March 2026
Status: Phase 0 — Pre-build

1. The Central Ethical Tension
Pulse is designed to help. A live broadcast producer who can see that 60% of audience sentiment has turned negative in the last 90 seconds has better information than one flying blind. Better information should produce better decisions.
But there is a risk embedded in that logic that must be named directly before a single line of code is written.
If a producer sees that topic X is generating high audience engagement and pivots the broadcast to cover topic X — and that producer does this repeatedly across dozens of broadcasts — Pulse has not informed editorial judgement. It has replaced it. The algorithm has become the editor. The audience, in aggregate, has learned that emotional reaction drives coverage, and they adjust their behaviour accordingly. The signal and the editorial response enter a feedback loop that degrades both.
This is the failure mode Cathy O'Neil describes in Weapons of Math Destruction — a model that is opaque, operates at scale, and causes harm not through malice but through the uncritical application of optimisation logic to a domain where optimisation is the wrong frame. Editorial integrity is not an optimisation problem. A broadcast that tells audiences what they want to hear is not a better broadcast. It is a less honest one.
Pulse must be designed so this failure mode cannot happen by accident. Every architectural and interface decision in this document is made with that constraint in mind.

2. Core Principles
Principle 1 — Editorial sovereignty is non-negotiable
Pulse surfaces signals. Producers make decisions. The system has no mechanism to influence the running order, suggest content changes, or flag editorial omissions. It classifies what the audience is saying. What to do with that information is a human judgement, always.
Principle 2 — Transparency over false confidence
Every classification includes a confidence score. Low-confidence results are visually distinct — not hidden, not removed, not averaged away. A producer who sees a 0.61 confidence score knows to treat that signal with scepticism. A tool that hides uncertainty manufactures false authority.
Principle 3 — The audience is not the editorial compass
High audience engagement with a topic is not evidence that the topic deserves more coverage. Controversy generates engagement. Outrage generates engagement. A sentiment spike is a data point, not an editorial directive. Pulse must never frame its outputs as recommendations — only as observations.
Principle 4 — Representation in the signal
Social media audiences are not representative of broadcast audiences. Younger, more digitally active, more urban demographics are systematically overrepresented in real-time social signals. Pulse must communicate this limitation visibly — the audience reacting on social media is a subset of the audience watching, and that subset has known demographic biases.
Principle 5 — Privacy by design
No real user data is stored or processed in v1. The synthetic dataset approach — established in Bias Audit — is the right pattern here. The model learns sentiment patterns from synthetic BAFTA content, not from real individuals' posts.

3. Hard Constraints — Built Into the Architecture
These are not guidelines. They are design requirements that cannot be overridden by a product decision, a user request, or a feature request.
ConstraintImplementationNo editorial recommendationsThe system never suggests what to cover. Output is classification only.Confidence always visiblepredict_proba score shown on every result. No result displayed without it.Editorial guardrail persistent in UINon-dismissible label: "Pulse surfaces audience signals. Editorial decisions remain with the producer." Present on every screen, every session.No auto-alert as directiveAlerts fire when negative sentiment exceeds threshold — but the alert names the signal, never the action. "Negative sentiment spike: Diversity & Representation" not "Consider addressing diversity concerns."Synthetic data only in v1No real user posts stored, processed, or logged.Demographic caveat visibleDashboard includes a persistent note: "Social signal audiences skew younger and more urban than linear broadcast audiences."

4. The Feedback Loop Risk
This deserves its own section because it is the failure mode most likely to occur slowly and invisibly.
If Pulse is used consistently across multiple broadcasts, and producers consistently respond to sentiment spikes by pivoting coverage, the following happens:

Audiences learn that emotional reaction drives what gets covered
Engagement-maximising behaviour increases — more extreme reactions, more volume
The sentiment signal degrades — it begins to measure strategic audience behaviour, not genuine reaction
Editorial decisions increasingly reflect the most vocal, most reactive segment of the audience
The broadcast becomes less representative of the full audience and more representative of the most engaged fraction

This is not a hypothetical. It is the documented trajectory of social media editorial integration at news organisations over the past decade, as described in The Alignment Problem (Brian Christian) — systems that were designed to inform human judgement gradually displaced it.
Mitigation built into Pulse v1:

The tool is scoped to a single producer screen — not broadcast-wide integration
No historical comparison feature in v1 — producers cannot see "what worked last time"
No engagement optimisation framing anywhere in the UI — sentiment is described as audience reaction, never as performance
The Ethics Framework is linked from the README and the case study — it is public, not internal


5. Regulatory Context
Ofcom Broadcasting Code — Section 5: Due Impartiality and Due Accuracy
Broadcasters must maintain due impartiality on matters of public policy and political controversy. A tool that systematically amplifies audience reaction to politically charged topics risks nudging coverage away from impartiality and toward reaction. Pulse's design — classification without recommendation — is the mitigation.
Ofcom Broadcasting Code — Section 2: Harm and Offence
Broadcast content must not cause unnecessary harm or offence. Pulse's alert system flags negative sentiment spikes to producers — giving them earlier warning of content that may be generating harmful audience reaction, supporting Section 2 compliance rather than undermining it.
BBC Editorial Guidelines — Impartiality
The BBC's editorial guidelines require that coverage reflects a range of significant views and is not driven by audience pressure. Pulse is designed to be consistent with this requirement — it informs, it does not pressure.
Online Safety Act 2023
Not directly applicable to Pulse in v1 — the tool processes synthetic data only and does not moderate user-generated content. Relevant in v2 if real social data is ingested.

6. What Good Looks Like
A producer using Pulse well:

Glances at the dashboard during ad breaks to understand the emotional temperature of the audience
Notes a negative sentiment spike on Diversity & Representation
Considers whether the broadcast has addressed that topic adequately — based on editorial judgement, not the score
Makes a decision that they could explain fully to their editorial director and to Ofcom without reference to Pulse

A producer using Pulse badly:

Treats every sentiment spike as an action item
Pivots coverage based on score without independent editorial reasoning
Cannot explain a coverage decision without saying "the dashboard showed negative sentiment"

Pulse cannot prevent the second scenario through technology alone. It mitigates it through interface design, persistent guardrails, and honest documentation of the risk — including this document.

7. Ongoing Responsibilities
These are the responsibilities that do not end at ship:

Signal drift monitoring: If v2 integrates real social data, sentiment distribution must be monitored for evidence that the signal is degrading due to strategic audience behaviour
Demographic representation audit: Every 6 months, the gap between social signal demographics and linear broadcast audience demographics must be reviewed and the caveat updated
Editorial impact review: If Pulse is deployed in a real production environment, editorial decisions influenced by Pulse signals must be reviewed quarterly for evidence of the feedback loop risk
Model retraining: Sentiment language evolves — BAFTA 2026 vocabulary may not classify correctly in 2027. Retraining schedule must be documented before v2