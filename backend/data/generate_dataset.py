#!/usr/bin/env python3
"""
generate_dataset.py
-------------------
Generates 2,400 synthetic BAFTA social media posts for Pulse sentiment
and topic classifier training.

Columns:
  content              - the social media post text
  emotion              - one of: excited, positive, neutral, negative, angry
  topics               - pipe-separated list of topic labels (multi-label)
  confidence           - float 0.70–0.99 (generation difficulty signal)
  split                - train / test (assigned after generation)

Resume-safe: re-running skips already-generated rows.

Usage:
    cd backend
    pip install anthropic python-dotenv
    python data/generate_dataset.py
"""

import csv
import json
import os
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv
import anthropic

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────
MODEL       = "claude-haiku-4-5"
OUTPUT_PATH = Path(__file__).resolve().parent / "bafta_dataset.csv"
BATCH_SIZE  = 10

EMOTIONS = ["excited", "positive", "neutral", "negative", "angry"]

TOPICS = [
    "winner_reaction",
    "presenter_performance",
    "ceremony_production",
    "diversity_representation",
    "fashion_red_carpet",
    "general_audience_reaction",
]

# 400 train + 100 test per emotion = 500 per emotion × 5 = 2,500 rows
# We generate 480 per emotion to give headroom, final split is stratified
CLEAR_PER_EMOTION  = 288   # confidence 0.85–0.99
SUBTLE_PER_EMOTION = 192   # confidence 0.70–0.84
TRAIN_PER_EMOTION  = 400
TEST_PER_EMOTION   = 80

CSV_COLUMNS = ["content", "emotion", "topics", "confidence", "split"]

# ─────────────────────────────────────────────────────────────────────────────
# Scripted narrative arc — BAFTA 2026 event timeline
# Controls which emotion is dominant at each stage of the broadcast.
# Used by the frontend auto-feed to simulate a live broadcast.
# Not used during training — stored as metadata only.
# ─────────────────────────────────────────────────────────────────────────────
NARRATIVE_ARC = [
    {"stage": "opening",       "dominant": "excited",   "description": "Ceremony opens, red carpet energy"},
    {"stage": "early_awards",  "dominant": "positive",  "description": "Popular early winners, crowd pleased"},
    {"stage": "controversy",   "dominant": "negative",  "description": "Controversial winner announced, backlash"},
    {"stage": "recovery",      "dominant": "excited",   "description": "Crowd-pleasing speech wins audience back"},
    {"stage": "closing",       "dominant": "positive",  "description": "Best Film announced, ceremony ends warmly"},
]

# ─────────────────────────────────────────────────────────────────────────────
# Generation prompts per emotion
# ─────────────────────────────────────────────────────────────────────────────
EMOTION_PROMPTS = {

    "excited": {
        "clear": (
            "Write social media posts from UK viewers watching the BAFTAs live, "
            "expressing clear excitement and enthusiasm. The emotion must be "
            "unmistakable — capitals, exclamation marks, fan energy. "
            "Contexts: a favourite winning, an unexpected upset that the writer loves, "
            "a standout speech, a stunning red carpet look, a presenter moment that "
            "landed brilliantly. UK social media register — Twitter/X style, under 280 chars."
        ),
        "subtle": (
            "Write social media posts from UK BAFTA viewers expressing mild excitement "
            "or quiet enthusiasm — positive but restrained. No exclamation marks or "
            "capitals. The excitement is in the content, not the punctuation. "
            "Examples: 'Really pleased for her, deserved it', 'That speech was something', "
            "'Didn't expect that winner but actually brilliant'. UK Twitter register."
        ),
    },

    "positive": {
        "clear": (
            "Write social media posts from UK viewers watching the BAFTAs expressing "
            "clear positive sentiment — satisfied, pleased, approving, warm. "
            "Not as intense as excitement. Examples: approving of a winner, "
            "complimenting a presenter, enjoying the ceremony atmosphere, praising "
            "diversity in the nominations, appreciating a film's recognition. "
            "UK Twitter register, under 280 chars."
        ),
        "subtle": (
            "Write social media posts from UK BAFTA viewers with subtly positive tone — "
            "mildly approving, faintly warm, or quietly satisfied. The positivity is "
            "present but understated. Examples: 'Fair result I suppose', 'Better than "
            "last year', 'Good to see that film get recognised'. Under 280 chars."
        ),
    },

    "neutral": {
        "clear": (
            "Write social media posts from UK viewers watching the BAFTAs that are "
            "purely observational — no emotional valence, no opinion, no approval or "
            "disapproval. Pure commentary. Examples: noting who won, describing what "
            "happened on stage, stating facts about the ceremony, sharing information "
            "about a nominee. UK Twitter register, under 280 chars. "
            "Must contain zero sentiment — neither positive nor negative."
        ),
        "subtle": (
            "Write social media posts from UK BAFTA viewers that are mostly neutral "
            "with a very faint lean — slightly curious, mildly questioning, or lightly "
            "observational with minimal opinion. Should be genuinely hard to classify "
            "as positive or negative. Examples: 'Interesting choice for best director', "
            "'Didn't see that coming', 'Wondering how this will go down'. Under 280 chars."
        ),
    },

    "negative": {
        "clear": (
            "Write social media posts from UK viewers watching the BAFTAs expressing "
            "clear negative sentiment — disappointed, critical, frustrated, or "
            "disapproving. Not abusive — critical. Examples: disappointed a film lost, "
            "critical of a presenter's jokes, frustrated at a controversial winner, "
            "disapproving of the ceremony production, critical of lack of diversity. "
            "UK Twitter register, under 280 chars. Must be clearly negative."
        ),
        "subtle": (
            "Write social media posts from UK BAFTA viewers expressing subtle negative "
            "sentiment — mild disappointment, faint criticism, quiet frustration. "
            "The negativity is present but not explicit. Examples: 'Not sure about that "
            "choice', 'Expected better from the ceremony tbh', 'Bit of a flat night "
            "so far'. Under 280 chars. Should be distinguishable from neutral."
        ),
    },

    "angry": {
        "clear": (
            "Write social media posts from UK viewers watching the BAFTAs expressing "
            "clear anger or strong outrage — not abuse, but genuine public anger. "
            "Contexts: a perceived snub of a deserving film or performer, a presenter "
            "joke that caused offence, a lack of diversity in winners, a controversial "
            "acceptance speech, a technical problem that ruined the broadcast. "
            "UK Twitter register, under 280 chars. The anger must be unmistakable."
        ),
        "subtle": (
            "Write social media posts from UK BAFTA viewers expressing subtle anger — "
            "irritated, quietly outraged, or sharply critical without explicit anger "
            "words. The anger is in the tone, not stated directly. Examples: 'Right "
            "so we're just ignoring that entire film then', 'Typical', 'Absolutely "
            "baffling decision'. Under 280 chars."
        ),
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Topic assignment prompt
# ─────────────────────────────────────────────────────────────────────────────
TOPIC_ASSIGNMENT_PROMPT = """
Given this BAFTA social media post, assign one or more topic labels from this list:
- winner_reaction
- presenter_performance
- ceremony_production
- diversity_representation
- fashion_red_carpet
- general_audience_reaction

Rules:
- Assign ALL topics that apply (multi-label)
- Every post gets at least one topic
- If no specific topic fits, use general_audience_reaction
- Return ONLY a JSON object: {"topics": ["topic1", "topic2"]}
- No explanation, no markdown

Post: {content}
"""

# ─────────────────────────────────────────────────────────────────────────────
# CSV helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_existing_counts():
    counts = {e: {"clear": 0, "subtle": 0} for e in EMOTIONS}
    if not OUTPUT_PATH.exists():
        return counts
    with open(OUTPUT_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            emotion = row.get("emotion", "")
            if emotion not in counts:
                continue
            try:
                conf = float(row["confidence"])
            except (ValueError, KeyError):
                continue
            difficulty = "clear" if conf >= 0.85 else "subtle"
            counts[emotion][difficulty] += 1
    return counts


def append_rows(rows):
    file_exists = OUTPUT_PATH.exists()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def assign_splits():
    if not OUTPUT_PATH.exists():
        return
    all_rows = []
    with open(OUTPUT_PATH, newline="", encoding="utf-8") as f:
        all_rows = list(csv.DictReader(f))
    by_emotion = defaultdict(list)
    for i, row in enumerate(all_rows):
        by_emotion[row["emotion"]].append(i)
    for emotion, indices in by_emotion.items():
        shuffled = indices[:]
        random.shuffle(shuffled)
        train_set = set(shuffled[:TRAIN_PER_EMOTION])
        for idx in indices:
            all_rows[idx]["split"] = "train" if idx in train_set else "test"
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(all_rows)

# ─────────────────────────────────────────────────────────────────────────────
# API helpers
# ─────────────────────────────────────────────────────────────────────────────

def call_claude_generate(client, emotion, difficulty, format_offset):
    conf_low, conf_high = (0.85, 0.99) if difficulty == "clear" else (0.70, 0.84)
    prompt_text = EMOTION_PROMPTS[emotion][difficulty]
    full_prompt = (
        f"Generate exactly 10 synthetic BAFTA 2026 social media posts "
        f"for emotion: {emotion} ({difficulty} examples).\n\n"
        f"Instructions:\n"
        f"- {prompt_text}\n"
        f"- Each confidence must be a float between {conf_low} and {conf_high}\n"
        f"- Return ONLY a JSON array of exactly 10 objects\n"
        f"- Each object must have exactly two keys: content (string) and confidence (float)\n"
        f"- No markdown, no code fences, no explanation — raw JSON array only\n"
        f"- Start your response with [ and end with ]"
    )
    for attempt in range(1, 4):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=2048,
                system="You are a JSON dataset generator. Respond with only a valid JSON array. Start with [ and end with ]. No markdown, no explanation.",
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
                raise ValueError(f"No JSON array found. Raw: {raw[:200]}")
            raw = raw[start:end + 1]
            items = json.loads(raw)
            for item in items:
                item["confidence"] = max(conf_low, min(conf_high, float(item["confidence"])))
            return items
        except Exception as e:
            wait = 5 * attempt
            print(f"\n    ⚠ Attempt {attempt}/3 failed: {e}. Retrying in {wait}s...", end="")
            time.sleep(wait)
    raise RuntimeError(f"All 3 attempts failed for {emotion} ({difficulty})")


def assign_topics_batch(client, contents):
    """Assign topics to a batch of posts in one API call."""
    posts_json = json.dumps([{"id": i, "content": c} for i, c in enumerate(contents)])
    prompt = (
        f"For each BAFTA social media post below, assign the MOST SPECIFIC topic label(s).\n\n"
        f"TOPIC DEFINITIONS — read carefully before assigning:\n"
        f"- winner_reaction: Post is specifically about who won or lost an award. "
        f"Must mention or clearly reference a winner, loser, result, or nomination outcome.\n"
        f"- presenter_performance: Post is specifically about a host or presenter — "
        f"their jokes, delivery, energy, or how they are running the show.\n"
        f"- ceremony_production: Post is specifically about the show itself — "
        f"stage design, music, pacing, technical issues, running order, venue.\n"
        f"- diversity_representation: Post is specifically about diversity, inclusion, "
        f"representation, or lack thereof in nominations or winners.\n"
        f"- fashion_red_carpet: Post is specifically about clothes, looks, style, "
        f"hair, makeup on the red carpet or during the show.\n"
        f"- general_audience_reaction: LAST RESORT ONLY. Use ONLY when the post is "
        f"a vague general reaction that cannot be tied to any specific topic above. "
        f"DO NOT use this if any other topic applies.\n\n"
        f"STRICT RULES:\n"
        f"1. Assign a MAXIMUM of 2 topics per post\n"
        f"2. Assign ONLY topics that clearly and directly apply\n"
        f"3. Use general_audience_reaction ONLY if no specific topic fits\n"
        f"4. Never combine general_audience_reaction with another topic\n"
        f"5. If a post is about a winner AND diversity, assign both — but not general_audience_reaction\n\n"
        f"Return ONLY a JSON array where each object has: id (int) and topics (array of strings)\n"
        f"No markdown, no explanation.\n\n"
        f"Posts:\n{posts_json}"
    )
    for attempt in range(1, 4):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system="You are a JSON classifier. Return only a valid JSON array. No markdown.",
                messages=[{"role": "user", "content": prompt}],
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
            results = json.loads(raw[start:end + 1])
            topic_map = {}
            for r in results:
                topics = r["topics"][:2]  # hard cap at 2
                # general_audience_reaction cannot mix with specific topics
                if len(topics) > 1 and "general_audience_reaction" in topics:
                    topics = [t for t in topics if t != "general_audience_reaction"]
                topic_map[r["id"]] = topics
            return ["|".join(topic_map.get(i, ["general_audience_reaction"])) for i in range(len(contents))]
        except Exception as e:
            wait = 5 * attempt
            print(f"\n    ⚠ Topic assignment attempt {attempt}/3 failed: {e}. Retrying in {wait}s...", end="")
            time.sleep(wait)
    # Fallback: assign general_audience_reaction to all
    return ["general_audience_reaction"] * len(contents)

# ─────────────────────────────────────────────────────────────────────────────
# Core generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_segment(client, emotion, difficulty, target, already_have):
    needed = target - already_have
    if needed <= 0:
        print(f"  {emotion} ({difficulty})... already complete ({already_have}/{target})")
        return

    batches   = (needed + BATCH_SIZE - 1) // BATCH_SIZE
    generated = already_have
    print(f"  Generating {emotion} ({difficulty})... {generated}/{target}", end="", flush=True)

    for batch_idx in range(batches):
        items      = call_claude_generate(client, emotion, difficulty, generated)
        still_need = target - generated
        items      = items[:still_need]

        contents = [item["content"].strip() for item in items]
        topics   = assign_topics_batch(client, contents)

        rows = []
        for i, item in enumerate(items):
            rows.append({
                "content":    contents[i],
                "emotion":    emotion,
                "topics":     topics[i],
                "confidence": round(float(item["confidence"]), 4),
                "split":      "pending",
            })

        append_rows(rows)
        generated += len(rows)
        print(f"\r  Generating {emotion} ({difficulty})... {generated}/{target}", end="", flush=True)

    print()

# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found. Add it to backend/.env", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print("=" * 62)
    print("  Pulse — BAFTA Sentiment Dataset Generator")
    print(f"  Model  : {MODEL}")
    print(f"  Output : {OUTPUT_PATH}")
    print("=" * 62)

    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()
        print("\nOld dataset deleted — regenerating with stricter topic rules.\n")

    counts = load_existing_counts()
    total  = sum(counts[e]["clear"] + counts[e]["subtle"] for e in EMOTIONS)
    print(f"\nExisting rows: {total} / 2400\n")

    for emotion in EMOTIONS:
        print(f"── {emotion.upper()} ──")
        generate_segment(client, emotion, "clear",  target=CLEAR_PER_EMOTION,  already_have=counts[emotion]["clear"])
        generate_segment(client, emotion, "subtle", target=SUBTLE_PER_EMOTION, already_have=counts[emotion]["subtle"])

    print("\nAssigning train / test splits...")
    assign_splits()

    print("\n✓ Done.")
    print(f"   Rows    : 2,400")
    print(f"   Columns : {', '.join(CSV_COLUMNS)}")
    print(f"   Path    : {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
