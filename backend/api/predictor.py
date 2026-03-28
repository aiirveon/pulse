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


def classify_emotion(text: str) -> dict:
    """
    Classify the emotion of a social media post.
    Returns emotion label, confidence score, and SHAP word highlights.
    """
    X = vectorizer.transform([text])
    proba = emotion_model.predict_proba(X)[0]
    label_index = int(np.argmax(proba))
    emotion = EMOTIONS[label_index]
    confidence = float(proba[label_index])
    shap_words = get_shap_words(text, label_index)

    return {
        "emotion":     emotion,
        "confidence":  round(confidence, 4),
        "shap_words":  shap_words,
        "all_scores":  {
            e: round(float(proba[i]), 4)
            for i, e in enumerate(EMOTIONS)
        },
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
