#!/usr/bin/env python3
"""
feed.py
-------
Manages the scripted BAFTA narrative arc simulation.
Pre-loads a set of sample posts and releases them on a timed basis
to simulate a live social media feed.

The narrative arc has 5 stages that map to dominant emotions:
  opening      -> excited
  early_awards -> positive
  controversy  -> negative + angry spike
  recovery     -> excited
  closing      -> positive
"""

import random
from typing import Generator

# Scripted BAFTA posts — curated to tell a compelling narrative arc
# Each post has: content, expected_emotion, stage
SCRIPTED_FEED = [
    # Stage 1 — Opening (excited)
    {"content": "Here we go!! The BAFTAs 2026 are LIVE and I am SO ready for this!! #BAFTA2026", "stage": "opening"},
    {"content": "The red carpet looks tonight are absolutely STUNNING. British fashion at its finest!! #BAFTAs", "stage": "opening"},
    {"content": "MY FAVOURITE PRESENTER IS HOSTING!! This is already the best BAFTA night ever!! 🎉", "stage": "opening"},
    {"content": "Right, snacks ready, phone charged, fully prepared for a brilliant evening of British cinema #BAFTA2026", "stage": "opening"},
    {"content": "That opening number just gave me CHILLS!! What a way to start the ceremony!! 🔥 #BAFTAs", "stage": "opening"},
    {"content": "The energy in that room is incredible — you can feel it through the screen!! Brilliant start #BAFTA2026", "stage": "opening"},

    # Stage 2 — Early awards (positive)
    {"content": "Really pleased with that Best Supporting Actress result — genuinely deserved recognition #BAFTAs", "stage": "early_awards"},
    {"content": "Good to see that documentary getting recognised. Important work, well rewarded tonight #BAFTA2026", "stage": "early_awards"},
    {"content": "Strong start to the evening. BAFTA voters making sensible choices so far #BAFTAs", "stage": "early_awards"},
    {"content": "Well done to the costume design team — that win was fully deserved, stunning work all year #BAFTA2026", "stage": "early_awards"},
    {"content": "Pleased they acknowledged that screenplay. One of the most original pieces of writing this year #BAFTAs", "stage": "early_awards"},
    {"content": "The diversity in the nominations this year is genuinely encouraging. Progress being made #BAFTA2026", "stage": "early_awards"},

    # Stage 3 — Controversy (negative + angry)
    {"content": "Right so we're just pretending that performance didn't exist then. Fascinating decision BAFTA.", "stage": "controversy"},
    {"content": "FURIOUS at that Best Film result. An absolute joke. That film was clearly superior in every way.", "stage": "controversy"},
    {"content": "Really disappointed — that director has been overlooked three years running now. Baffling.", "stage": "controversy"},
    {"content": "Typical. Same faces, same outcomes. Nothing ever changes at these things.", "stage": "controversy"},
    {"content": "The lack of recognition for that British indie film is genuinely insulting to everyone involved.", "stage": "controversy"},
    {"content": "How DARE they snub that performance AGAIN. This is an embarrassment for British cinema.", "stage": "controversy"},
    {"content": "Absolutely baffling decision. The other nominee was clearly the stronger performance by miles.", "stage": "controversy"},
    {"content": "Not the result I was hoping for. That film deserved more than this — significantly more.", "stage": "controversy"},

    # Stage 4 — Recovery (excited)
    {"content": "WAIT THAT SPEECH JUST MADE ME CRY!! The most moving thing I have heard all year!! 😭✨", "stage": "recovery"},
    {"content": "YES!! My absolute favourite just won!! I am literally jumping around my living room!! 🎉🏆", "stage": "recovery"},
    {"content": "THAT COMEBACK!! The whole room on their feet!! This is what the BAFTAs are FOR!! 🔥🔥", "stage": "recovery"},
    {"content": "The presenter just absolutely SAVED this ceremony with that bit!! COMEDY GOLD!! 😂", "stage": "recovery"},
    {"content": "I cannot believe that upset!! The underdog WON!! British cinema is THRIVING tonight!! 🎬", "stage": "recovery"},
    {"content": "That acceptance speech was EVERYTHING!! The emotion, the honesty, the standing ovation!! 💛", "stage": "recovery"},

    # Stage 5 — Closing (positive)
    {"content": "A genuinely strong evening overall. Some questionable decisions but the right films celebrated #BAFTAs", "stage": "closing"},
    {"content": "Best Film went to the right choice. A worthy winner and a good end to the ceremony #BAFTA2026", "stage": "closing"},
    {"content": "Really well produced ceremony this year. Good pacing, strong presenters, memorable moments #BAFTAs", "stage": "closing"},
    {"content": "Pleased with how the evening ended. British cinema in good health #BAFTA2026", "stage": "closing"},
    {"content": "Good night for representation in the winners. Progress is slow but it is happening #BAFTAs", "stage": "closing"},
    {"content": "Until next year. Proud of British cinema tonight. Mostly. #BAFTA2026", "stage": "closing"},
]


class FeedSimulator:
    """Manages the scripted feed state for a single session."""

    def __init__(self):
        self.posts = SCRIPTED_FEED.copy()
        random.shuffle(self.posts[:6])   # shuffle within opening stage
        self.index = 0
        self.session_id = None

    def next_batch(self, batch_size: int = 3) -> list[dict]:
        """Return the next batch of posts. Loops when exhausted."""
        if self.index >= len(self.posts):
            self.index = 0  # loop for demo purposes

        batch = self.posts[self.index:self.index + batch_size]
        self.index += batch_size
        return batch

    def reset(self):
        self.index = 0

    @property
    def current_stage(self) -> str:
        if self.index < 6:
            return "opening"
        elif self.index < 12:
            return "early_awards"
        elif self.index < 20:
            return "controversy"
        elif self.index < 26:
            return "recovery"
        else:
            return "closing"


# Single global simulator instance per process
_simulator = FeedSimulator()


def get_simulator() -> FeedSimulator:
    return _simulator
