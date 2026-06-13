#!/usr/bin/env python3
"""
predictor.py
------------
Loads trained model artefacts and exposes two prediction functions:
  - classify_emotion(text) -> emotion, confidence, shap_words
  - classify_topics(text)  -> list of (topic, confidence) tuples
"""

import pickle
import json
import numpy as np
from pathlib import Path
import anthropic
import os
from dotenv import load_dotenv
load_dotenv()

MODEL_DIR = Path(__file__).resolve().parent.parent / "model"


def load_artefacts():
    with open(MODEL_DIR / "vectorizer.pkl",    "rb") as f:
        vectorizer = pickle.load(f)
    with open(MODEL_DIR / "emotion_model.pkl", "rb") as f:
        emotion_model = pickle.load(f)
    with open(MODEL_DIR / "topic_model.pkl",   "rb") as f:
        topic_model = pickle.load(f)
    with open(MODEL_DIR / "mlb.pkl",           "rb") as f:
        mlb = pickle.load(f)
    with open(MODEL_DIR / "meta.json",         "r") as f:
        meta = json.load(f)
    return vectorizer, emotion_model, topic_model, mlb, meta


# Load once at startup
vectorizer, emotion_model, topic_model, mlb, meta = load_artefacts()

EMOTIONS = meta["emotions"]
TOPICS   = meta["topics"]


def get_shap_words(text: str, label_index: int, top_n: int = 5) -> list[str]:
    """Return top N words that most influenced the emotion classification."""
    try:
        import shap
        explainer = shap.TreeExplainer(emotion_model)
        X = vectorizer.transform([text])
        shap_values = explainer.shap_values(X)
        feature_names = vectorizer.get_feature_names_out()
        scores = shap_values[label_index][0]
        top_indices = np.argsort(np.abs(scores))[-top_n:][::-1]
        words = [feature_names[i] for i in top_indices if scores[i] != 0]
        return words[:top_n]
    except Exception:
        return []


def classify_with_claude(text: str) -> dict:
    """
    Tier 2 classification using Claude API for short or ambiguous text.
    Used when word count is between 4 and 20 words.
    Returns same structure as classify_emotion.
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = (
        f"Classify the emotion of this social media post about a live TV broadcast event.\n\n"
        f"Post: \"{text}\"\n\n"
        f"Choose ONE emotion from: excited, positive, neutral, negative, angry\n\n"
        f"Rules:\n"
        f"- excited: high energy positive, caps, exclamation marks, buzzing\n"
        f"- positive: warm, pleased, approving, satisfied\n"
        f"- neutral: purely observational, no emotional lean\n"
        f"- negative: disappointed, critical, calm dissatisfaction\n"
        f"- angry: outrage, fury, or cold sarcasm\n\n"
        f"Also choose ALL topics that apply from:\n"
        f"winner_reaction, presenter_performance, ceremony_production,\n"
        f"diversity_representation, fashion_red_carpet, general_audience_reaction\n\n"
        f"Return ONLY a JSON object with exactly these keys:\n"
        f"emotion (string), confidence (float 0.7-0.95), topics (array of strings)\n"
        f"No markdown, no explanation."
    )

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        import json as _json
        raw = response.content[0].text.strip()
        if "```" in raw:
            lines = raw.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            raw = "\n".join(lines).strip()
        result = _json.loads(raw)
        return {
            "emotion":          result.get("emotion", "neutral"),
            "confidence":       float(result.get("confidence", 0.75)),
            "confidence_type":  "estimated",
            "shap_words":       [],
            "all_scores":       {e: 0.1 for e in EMOTIONS},
            "topics":           [{"topic": t, "confidence": 0.8, "confidence_type": "estimated"}
                                 for t in result.get("topics", ["general_audience_reaction"])],
            "tier":             2,
            "degraded":         False,
        }
    except Exception as exc:
        return {
            "emotion":          "unavailable",
            "confidence":       0.0,
            "confidence_type":  "estimated",
            "shap_words":       [],
            "all_scores":       {e: 0.0 for e in EMOTIONS},
            "topics":           [],
            "tier":             2,
            "degraded":         True,
            "error":            f"Claude API failure: {type(exc).__name__}",
        }


def classify_emotion(text: str) -> dict:
    """
    Tiered emotion classification.
    Tier 1 (<=3 words): auto-neutral, low confidence
    Tier 2 (4-20 words): Claude API semantic classification
    Tier 3 (>20 words): XGBoost + SHAP
    """
    words = text.strip().split()
    word_count = len(words)

    # Tier 1 — too short to classify reliably
    if word_count <= 3:
        return {
            "emotion":         "neutral",
            "confidence":      0.4,
            "confidence_type": "estimated",
            "shap_words":      [],
            "all_scores":      {e: 0.2 for e in EMOTIONS},
            "tier":            1,
            "degraded":        False,
        }

    # Tier 2 — short text, use Claude for semantic understanding
    if word_count <= 20:
        return classify_with_claude(text)

    # Tier 3 — full XGBoost + SHAP pipeline
    X = vectorizer.transform([text])
    proba = emotion_model.predict_proba(X)[0]
    label_index = int(np.argmax(proba))
    emotion = EMOTIONS[label_index]
    confidence = float(proba[label_index])
    shap_words = get_shap_words(text, label_index)

    return {
        "emotion":         emotion,
        "confidence":      round(confidence, 4),
        "confidence_type": "calibrated",
        "shap_words":      shap_words,
        "all_scores":      {
            e: round(float(proba[i]), 4)
            for i, e in enumerate(EMOTIONS)
        },
        "tier":            3,
        "degraded":        False,
    }


def classify_topics(text: str) -> list[dict]:
    """
    Classify the topics of a social media post (multi-label).
    Returns list of topics with confidence scores, sorted by confidence.
    """
    X = vectorizer.transform([text])
    # OneVsRestClassifier predict_proba returns (n_samples, n_classes)
    try:
        proba = topic_model.predict_proba(X)[0]
    except AttributeError:
        # Fallback for estimators without predict_proba
        pred = topic_model.predict(X)[0]
        return [
            {"topic": TOPICS[i], "confidence": 1.0}
            for i, v in enumerate(pred) if v == 1
        ]

    results = []
    for i, topic in enumerate(TOPICS):
        conf = float(proba[i])
        if conf >= 0.3:  # minimum confidence threshold
            results.append({
                "topic":      topic,
                "confidence": round(conf, 4),
            })

    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results[:2] if results else [
        {"topic": "general_audience_reaction", "confidence": 0.3}
    ]
