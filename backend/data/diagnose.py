#!/usr/bin/env python3
"""
diagnose.py
-----------
Reads the existing bafta_dataset.csv and prints a distribution report.
No API calls. No cost. Runs locally in seconds.

Usage:
    cd backend
    python data/diagnose.py
"""

import csv
from collections import Counter, defaultdict
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent / "bafta_dataset.csv"


def main():
    if not DATA_PATH.exists():
        print(f"Error: {DATA_PATH} not found.")
        return

    rows = []
    with open(DATA_PATH, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r.get("content", "").strip()]

    print("=" * 62)
    print("  Pulse — Dataset Diagnostic Report")
    print(f"  Total rows: {len(rows)}")
    print("=" * 62)

    # ── Emotion distribution ──────────────────────────────────────
    emotion_counts = Counter(r["emotion"] for r in rows)
    split_emotion  = defaultdict(Counter)
    for r in rows:
        split_emotion[r["split"]][r["emotion"]] += 1

    print("\n── EMOTION DISTRIBUTION ──")
    print(f"  {'Emotion':<12} {'Total':>7} {'Train':>7} {'Test':>7}")
    print(f"  {'-'*12} {'-'*7} {'-'*7} {'-'*7}")
    for emotion in ["excited", "positive", "neutral", "negative", "angry"]:
        total = emotion_counts.get(emotion, 0)
        train = split_emotion["train"].get(emotion, 0)
        test  = split_emotion["test"].get(emotion, 0)
        flag  = " <- LOW TEST SAMPLE" if test < 50 else ""
        print(f"  {emotion:<12} {total:>7} {train:>7} {test:>7}{flag}")

    # ── Topic distribution ────────────────────────────────────────
    all_topics = []
    for r in rows:
        for t in r.get("topics", "").split("|"):
            t = t.strip()
            if t:
                all_topics.append((t, r["split"]))

    topic_counts = Counter(t for t, _ in all_topics)
    split_topic  = defaultdict(Counter)
    for t, s in all_topics:
        split_topic[s][t] += 1

    topics = [
        "winner_reaction",
        "presenter_performance",
        "ceremony_production",
        "diversity_representation",
        "fashion_red_carpet",
        "general_audience_reaction",
    ]

    print("\n── TOPIC DISTRIBUTION ──")
    print(f"  {'Topic':<30} {'Total':>7} {'Train':>7} {'Test':>7}")
    print(f"  {'-'*30} {'-'*7} {'-'*7} {'-'*7}")
    for topic in topics:
        total = topic_counts.get(topic, 0)
        train = split_topic["train"].get(topic, 0)
        test  = split_topic["test"].get(topic, 0)
        flag  = " <- LOW TEST SAMPLE" if test < 30 else ""
        print(f"  {topic:<30} {total:>7} {train:>7} {test:>7}{flag}")

    # ── Negative vs angry detail ──────────────────────────────────
    neg_rows = [r for r in rows if r["emotion"] == "negative"]
    ang_rows = [r for r in rows if r["emotion"] == "angry"]

    print("\n── NEGATIVE vs ANGRY DETAIL ──")
    print(f"  Negative rows total : {len(neg_rows)}")
    print(f"  Angry rows total    : {len(ang_rows)}")
    ratio = len(neg_rows) / max(len(ang_rows), 1)
    print(f"  Ratio (neg/ang)     : {ratio:.2f}")
    if ratio < 0.8 or ratio > 1.2:
        print("  <- WARNING: Imbalance between negative and angry")
    else:
        print("  <- Balance looks healthy")

    # ── Confidence distribution ───────────────────────────────────
    confs = []
    for r in rows:
        try:
            confs.append(float(r["confidence"]))
        except (ValueError, KeyError):
            pass

    if confs:
        clear  = sum(1 for c in confs if c >= 0.85)
        subtle = sum(1 for c in confs if c < 0.85)
        print("\n── CONFIDENCE DISTRIBUTION ──")
        print(f"  Clear examples  (>= 0.85): {clear:>5} ({clear/len(confs)*100:.1f}%)")
        print(f"  Subtle examples (<  0.85): {subtle:>5} ({subtle/len(confs)*100:.1f}%)")

    # ── Split summary ─────────────────────────────────────────────
    split_counts = Counter(r["split"] for r in rows)
    print("\n── SPLIT SUMMARY ──")
    for split, count in sorted(split_counts.items()):
        print(f"  {split:<10} {count:>5}")

    print("\n  Done.")


if __name__ == "__main__":
    main()
