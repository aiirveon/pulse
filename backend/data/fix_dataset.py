#!/usr/bin/env python3
"""
fix_dataset.py
--------------
Two targeted fixes based on diagnostic report:

Fix 1 — negative boundary: Generates 300 additional negative posts
with sharper arguing-vs-venting distinction from the labelling guide.
Appends to existing dataset as train rows.

Fix 2 — fashion_red_carpet test sample: Moves 15 train rows to test
for fashion_red_carpet category. No API calls for this fix.

Cost: approximately $0.04 (Fix 1 only. Fix 2 is free.)

Usage:
    cd backend
    python data/fix_dataset.py
    python data/train.py
"""

import csv
import json
import os
import random
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
import anthropic

load_dotenv()

MODEL       = "claude-haiku-4-5"
DATA_PATH   = Path(__file__).resolve().parent / "bafta_dataset.csv"
BATCH_SIZE  = 10
CSV_COLUMNS = ["content", "emotion", "topics", "confidence", "split"]

NEGATIVE_TOPICS = [
    "winner_reaction",
    "winner_reaction",
    "presenter_performance",
    "ceremony_production",
    "diversity_representation",
    "general_audience_reaction",
]

CLEAR_PROMPT = (
    "Write BAFTA 2026 social media posts where the writer is making a "
    "REASONED ARGUMENT about something that disappointed or frustrated them. "
    "The writer is ARGUING, not venting. They state a reason or explain "
    "their position. Calm, analytical, critical tone. "
    "Think: a film critic writing a measured review. "
    "The post must contain a reason or explanation — not just a feeling. "
    "CORRECT tone examples: "
    "'Really disappointed that film did not win — it was technically "
    "superior in every department and the voters missed that', "
    "'The presenter is not connecting with the room because the jokes "
    "rely on references most of the audience will not get', "
    "'Baffling decision — that performance was clearly more nuanced "
    "and emotionally layered than the one that won'. "
    "WRONG tone — do not write these: "
    "'FURIOUS!!!', 'Absolute disgrace', 'Typical BAFTA', "
    "'Right so we are just ignoring that film then'. "
    "No exclamation sequences. No ALL CAPS. No sarcasm. "
    "Must feel like a reasoned argument, not a vent. "
    "UK Twitter register. Under 280 chars."
)

SUBTLE_PROMPT = (
    "Write BAFTA 2026 social media posts with quiet, understated "
    "disappointment. The writer is mildly critical or let down. "
    "No heat, no sarcasm, no venting. Just measured dissatisfaction. "
    "The negativity is in the judgement, not the emotion. "
    "Must feel DIFFERENT from angry posts — there is no fury here, "
    "hot or cold. Just a person who expected better and is saying so calmly. "
    "CORRECT examples: "
    "'Not the result I was hoping for', "
    "'Could have been a stronger evening honestly', "
    "'A few questionable decisions tonight from the voters', "
    "'Expected more from this year's nominations if I'm honest'. "
    "WRONG — do not write these: "
    "'Typical.', 'Right.', 'Fascinating choice.', 'Remarkable.' "
    "Those are cold sarcasm and belong in the angry category. "
    "Under 280 chars. Calm and measured throughout."
)


def load_rows():
    with open(DATA_PATH, newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r.get("content", "").strip()]


def save_rows(rows):
    with open(DATA_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def append_rows(rows):
    with open(DATA_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writerows(rows)


def call_claude(client, prompt, conf_low, conf_high):
    full_prompt = (
        f"Generate exactly 10 synthetic BAFTA 2026 social media posts.\n\n"
        f"- {prompt}\n"
        f"- Each confidence must be a float between {conf_low} and {conf_high}\n"
        f"- Return ONLY a JSON array of exactly 10 objects\n"
        f"- Each object: content (string) and confidence (float)\n"
        f"- Raw JSON array only. Start with [ end with ]"
    )
    for attempt in range(1, 4):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=2048,
                system=(
                    "You are a JSON dataset generator. "
                    "Return only a valid JSON array. No markdown."
                ),
                messages=[{"role": "user", "content": full_prompt}],
            )
            raw = response.content[0].text.strip()
            if "```" in raw:
                lines = raw.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                raw = "\n".join(lines).strip()
            start = raw.find("[")
            end = raw.rfind("]")
            if start == -1 or end == -1:
                raise ValueError("No JSON array found")
            items = json.loads(raw[start:end + 1])
            for item in items:
                item["confidence"] = max(
                    conf_low, min(conf_high, float(item["confidence"]))
                )
            return items
        except Exception as e:
            wait = 5 * attempt
            print(
                f"\n    Warning: Attempt {attempt}/3 failed: {e}. "
                f"Retrying in {wait}s...",
                end=""
            )
            time.sleep(wait)
    raise RuntimeError("All 3 attempts failed")


def fix_negative(client):
    """Generate 300 additional negative posts with sharp boundary definition."""
    print("\n── FIX 1: negative boundary (300 rows) ──")

    segments = [
        ("clear",  180, CLEAR_PROMPT,  0.85, 0.97),
        ("subtle", 120, SUBTLE_PROMPT, 0.70, 0.84),
    ]

    total = 0
    for difficulty, count, prompt, conf_low, conf_high in segments:
        batches   = (count + BATCH_SIZE - 1) // BATCH_SIZE
        generated = 0
        print(f"  negative ({difficulty}) {count} rows... 0/{count}", end="", flush=True)

        for _ in range(batches):
            if generated >= count:
                break
            items      = call_claude(client, prompt, conf_low, conf_high)
            still_need = count - generated
            items      = items[:still_need]

            rows = []
            for item in items:
                rows.append({
                    "content":    item["content"].strip(),
                    "emotion":    "negative",
                    "topics":     random.choice(NEGATIVE_TOPICS),
                    "confidence": round(float(item["confidence"]), 4),
                    "split":      "train",
                })

            append_rows(rows)
            generated += len(rows)
            total     += len(rows)
            print(
                f"\r  negative ({difficulty}) {count} rows... "
                f"{generated}/{count}",
                end="",
                flush=True
            )
        print()

    print(f"  Done. Added {total} negative rows.")


def fix_fashion_test_sample():
    """
    Move 15 fashion_red_carpet rows from train to test.
    No API calls. Fixes unreliable F1 from 15 test examples.
    """
    print("\n── FIX 2: fashion_red_carpet test sample (free) ──")

    rows = load_rows()

    fashion_train = [
        i for i, r in enumerate(rows)
        if r.get("topics", "") == "fashion_red_carpet"
        and r.get("split") == "train"
    ]

    if len(fashion_train) < 15:
        print(f"  Only {len(fashion_train)} fashion train rows found — skipping.")
        return

    # Move 15 random train rows to test
    to_move = random.sample(fashion_train, 15)
    for idx in to_move:
        rows[idx]["split"] = "test"

    save_rows(rows)

    # Verify
    fashion_test_after = sum(
        1 for r in rows
        if r.get("topics", "") == "fashion_red_carpet"
        and r.get("split") == "test"
    )
    fashion_train_after = sum(
        1 for r in rows
        if r.get("topics", "") == "fashion_red_carpet"
        and r.get("split") == "train"
    )
    print(f"  Done. fashion_red_carpet: {fashion_train_after} train / "
          f"{fashion_test_after} test")


def main():
    if not DATA_PATH.exists():
        print(f"Error: {DATA_PATH} not found. Run generate_dataset.py first.")
        sys.exit(1)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print("=" * 62)
    print("  Pulse — Targeted Dataset Fix")
    print(f"  Fix 1: negative boundary (300 rows, ~$0.04)")
    print(f"  Fix 2: fashion_red_carpet test split (free)")
    print("=" * 62)

    fix_negative(client)
    fix_fashion_test_sample()

    print("\n  Both fixes complete. Run: python data/train.py")


if __name__ == "__main__":
    main()
