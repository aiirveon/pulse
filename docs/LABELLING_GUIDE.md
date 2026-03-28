# LABELLING_GUIDE.md — Pulse BAFTA Dataset

> Version: 1.0
> Status: Final — approved before generation begins
> Author: Ogbebor Osaheni
> Purpose: This document defines every label in the training dataset.
> Anyone generating, reviewing, or quality-checking data must read this
> before touching any data.

---

## What This Document Is

Before generating a single training example, every label must be precisely
defined. This prevents three expensive mistakes:

1. Generating data with blurry boundaries between similar categories
2. Having to regenerate thousands of rows because the model learned the
   wrong thing
3. Wasting API credits fixing problems that clear definitions would have
   prevented upfront

---

## The Task

We are generating synthetic social media posts from UK viewers watching
the BAFTAs live. Each post needs two labels:

1. Emotion — how the writer feels (one label per post)
2. Topic — what the post is about (one or two labels per post)

---

## Column 1: Emotion Labels

Five possible values: excited, positive, neutral, negative, angry

Rule: emotion is about TONE not topic. A post about a winner can be any
of the 5 emotions depending on how the writer responds.

---

### excited

Plain English: The writer is buzzing. They cannot contain themselves.

Signals: Multiple !!! in a row, words in ALL CAPS, physical reactions
described (screaming, jumping, crying happy tears), words like YESSS,
LIVING FOR IT.

Worked example:
"MY GIRL WON!!! I literally screamed so loud my neighbours banged on
the wall!! What a night for British cinema!! #BAFTA2026"
Why excited: ALL CAPS on MY GIRL, triple exclamation marks, physical
reaction described (screaming), high energy throughout.

Boundary test: If you removed all punctuation and caps, would the post
still feel warm and positive? If yes -> positive. If it would feel flat
-> excited (the energy IS the caps and punctuation).

Do NOT label excited just because something good happened. Label it
excited because of HOW the writer is expressing it.

---

### positive

Plain English: The writer is pleased. Warm, satisfied, approving.
Not jumping around — just genuinely happy.

Signals: Measured language, no CAPS, no !!! sequences.
Words like: pleased, deserved, glad, really good, well done, happy to see.

Worked example:
"Really pleased for her — she has been nominated three times and finally
got the recognition she deserves. Good result tonight."
Why positive: Warm and approving, but measured. No exclamation sequences.
The writer is satisfied, not buzzing.

Boundary test: If the post has two or more !!! sequences OR has words in
CAPS -> check if it is excited instead.

Do NOT label positive just because the writer says something nice.
"YES that is brilliant!!!" is excited, not positive.

---

### neutral

Plain English: The writer is reporting or observing. No emotional lean.
Could have been written by someone who does not care either way.

Signals: Factual statements, questions without implied opinion,
observations without a verdict.

Worked example:
"Best Director just announced. Goes to the documentary about the NHS.
Third consecutive BAFTA for a documentary in this category."
Why neutral: Pure observation. No approval or disapproval.
Could be a news bot.

THE SARCASM TEST — most important test for neutral:
Ask: could this sentence be sarcastic? If yes, it is NOT neutral.

"Interesting choice." — Could be sarcastic -> NOT neutral.
Label negative or angry depending on context.
"Best Director just announced." — Cannot be sarcastic -> neutral.

Never label sarcasm as neutral. Sarcasm is always negative or angry.

---

### negative

Plain English: The writer is disappointed, critical, or unimpressed.
Tone is CALM and REASONED — like a critic writing a review, not a
fan venting.

Signals: Words like disappointed, expected better, not the right call,
shame, baffling decision. A reason or explanation for the criticism.
No ALL CAPS rage, no !!! sequences.

Worked example:
"Really disappointed that film did not take Best Picture. It was clearly
the more technically accomplished work and deserved the recognition.
Shame the voters did not see it that way."
Why negative: Disappointed and critical, but calm. Makes a reasoned
argument. No heat or fury.

THE CRITICAL BOUNDARY WITH ANGRY:
Ask: is the writer ARGUING or VENTING?

ARGUING (= negative):
- States a reason
- Calm delivery
- Could appear in a film review
- "Wrong call because the other film was stronger"

VENTING (= angry):
- Just expresses the feeling
- Hot or cold fury
- Could not appear in a film review
- "Absolute joke. Typical."

Do NOT label negative just because the post is unhappy. If there is no
reasoning and just reaction -> angry.

---

### angry

Plain English: The writer is outraged or furious. Comes in two styles —
both are angry.

Style 1 — Hot anger: Loud, caps, exclamation marks, explicit fury.
"ABSOLUTE DISGRACE. How DARE they overlook that performance AGAIN.
This is embarrassing for BAFTA."

Style 2 — Cold sarcasm: Quiet, clipped, dripping with contempt.
"Right so we are just ignoring that entire film then. Fine.
Totally normal."

Worked example (cold sarcasm):
"Typical. Nothing ever changes. Same faces, same decisions, year
after year."
Why angry: The writer is venting. No argument being made. Contained
fury through clipped language.

Boundary test: Is there a reasoned argument in this post?
If yes -> negative. If no, just reaction -> angry.

One-word reactions like "Interesting." or "Right." or "Typical." used
alone = almost always angry (cold sarcasm).

Do NOT assume angry only looks loud. Cold sarcasm is also angry.
Both share one thing: venting, not arguing.

---

## Column 2: Topic Labels

Six possible values. Maximum 2 topics per post.

Rule: always assign the MOST SPECIFIC topic that applies.
general_audience_reaction is last resort — only use it when genuinely
nothing else fits.

---

### winner_reaction

Definition: The post is specifically about who won, who lost, who was
nominated, or who was snubbed.

Test: Does the post make a claim about a result, even implicitly?

Examples:
"Cant believe that film won. Deserved it."
-> winner_reaction (directly about a winner)

"Right so we are just ignoring that film then."
-> winner_reaction (implicitly about a snub)

"Three years of nominations and finally!"
-> winner_reaction (about a nomination outcome)

NOT this label:
"What a night" -> no result referenced -> general_audience_reaction
"The host is hilarious" -> about presenter -> presenter_performance

---

### presenter_performance

Definition: The post is specifically about a host or presenter — their
jokes, delivery, chemistry, or how they are running the show.

Test: Is there a named or implied reference to a host or presenter
doing something?

Examples:
"That opening monologue was hilarious"
-> presenter_performance

"These two hosts have brilliant chemistry"
-> presenter_performance

"That joke did NOT land and the room went silent"
-> presenter_performance

NOT this label:
"That acceptance speech was incredible"
-> acceptance speeches are by winners, not presenters -> winner_reaction

"The show feels slow tonight"
-> about pacing, not the presenter -> ceremony_production

---

### ceremony_production

Definition: The post is about the show itself as a production — stage,
lighting, music, pacing, montages, technical issues, running order.

Test: Is the post about something the production team made or decided,
not the people on stage?

Examples:
"That tribute montage was beautifully put together"
-> ceremony_production

"The pacing tonight is absolutely terrible"
-> ceremony_production

"Stage design is stunning this year"
-> ceremony_production

NOT this label:
"What a great evening overall" -> too vague -> general_audience_reaction
"The presenter is killing it" -> about a person -> presenter_performance

---

### diversity_representation

Definition: The post is explicitly about diversity, inclusion, or
representation — in nominations, winners, or the broader industry.

Test: Does the post use words like diversity, representation, inclusion,
or make a point about which groups are or are not represented?

Examples:
"Finally seeing proper representation in these nominations"
-> diversity_representation

"Another year, no women directors nominated. Embarrassing."
-> diversity_representation

"The lack of diversity in these winners says everything."
-> diversity_representation

NOT this label:
"Cant believe that director did not win" — even if that director is a
woman, unless diversity is explicitly mentioned -> winner_reaction

---

### fashion_red_carpet

Definition: The post is about a specific fashion element — an outfit,
dress, suit, hair, makeup, jewellery, or red carpet look.

Test: Does the post mention a specific physical appearance element?

Must-have test: Can you point to a specific item (dress, suit, hair,
makeup, shoes, jewellery)? If not -> do not use this label.

Examples:
"That red carpet gown is absolutely stunning"
-> fashion_red_carpet (mentions gown)

"Not sure about that suit choice tonight"
-> fashion_red_carpet (mentions suit)

"The hair and makeup this year is incredible"
-> fashion_red_carpet (mentions specific elements)

NOT this label:
"She looked amazing" -> no specific fashion element named
-> general_audience_reaction

"That entrance was iconic" -> about a moment, not an outfit
-> ceremony_production

---

### general_audience_reaction

Definition: The post expresses a general feeling about the evening as a
whole. Cannot be tied to any specific winner, presenter, production
element, diversity point, or fashion item.

THIS IS THE LABEL OF LAST RESORT.
Before assigning it, check every other label first.

Test: If you removed the post from any BAFTA context and placed it at
any other awards show, would it still make sense as-is?
If yes -> general_audience_reaction.

Examples:
"What a night this has been" -> general_audience_reaction
"Best BAFTAs in years, genuinely" -> general_audience_reaction
"Loving the energy in that room" -> general_audience_reaction

NOT this label (use something more specific):
"Cant believe who won" -> winner_reaction
"The host is on fire tonight" -> presenter_performance
"That dress though!" -> fashion_red_carpet

Cannot be combined with another label. If a post has a specific topic
AND a general reaction, use only the specific topic.

---

## Emotion Decision Tree

Is the post happy or positive in some way?
  YES -> Is it loud? (CAPS, multiple !!!, screaming, jumping)
    YES -> excited
    NO  -> positive
  NO  -> Is it flat and purely observational?
    YES -> Is it sarcastic? (Interesting. Right. Typical.)
      YES -> angry (cold sarcasm)
      NO  -> neutral
    NO  -> Does the writer make a reasoned argument?
      YES -> negative
      NO  -> angry

---

## Topic Decision Tree

Does the post mention an award result, winner, loser, or snub?
  YES -> winner_reaction

Does the post mention a host, presenter, or their performance?
  YES -> presenter_performance

Does the post mention stage, music, pacing, montage, or production?
  YES -> ceremony_production

Does the post mention diversity, representation, or inclusion?
  YES -> diversity_representation

Does the post mention a specific outfit, dress, hair, or makeup item?
  YES -> fashion_red_carpet

None of the above apply?
  -> general_audience_reaction

---

## Pilot Check Protocol

Before running a full generation of 2400 rows:

1. Generate exactly 20 examples per emotion (100 total)
2. Print them and read every single one
3. Apply the decision trees above to each one manually
4. Check: does the assigned emotion match your manual assessment?
5. Check: are negative and angry clearly different from each other?
6. Check: is general_audience_reaction being assigned sparingly?
7. If more than 3 out of 100 rows feel wrong -> stop, fix the prompt,
   re-pilot
8. Only proceed to full generation when the pilot passes

Cost of a pilot: approximately $0.02
Cost of skipping the pilot and getting it wrong: approximately $0.50
per regeneration run plus retrain time

---

## Final Checklist Before Starting Generation

- I have read every label definition above
- I understand the negative vs angry boundary
- I understand the sarcasm = angry rule
- I understand general_audience_reaction is last resort only
- I have run a pilot of 100 examples and reviewed them manually
- The pilot passed (fewer than 3 rows felt mislabelled)
- I am ready to run the full generation
