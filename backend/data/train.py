#!/usr/bin/env python3
"""
train.py
--------
Trains two classifiers on the synthetic BAFTA dataset:
  1. Emotion classifier  — 5-class single-label (TF-IDF + XGBoost)
  2. Topic classifier    — 6-class multi-label  (TF-IDF + OneVsRest XGBoost)

Saves three artefacts to backend/model/:
  - vectorizer.pkl       (shared TF-IDF vectoriser)
  - emotion_model.pkl    (XGBoost classifier)
  - topic_model.pkl      (OneVsRestClassifier wrapping XGBoost)

Usage:
    cd backend
    python data/train.py
"""

import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score
from xgboost import XGBClassifier

DATA_PATH  = Path(__file__).resolve().parent / "bafta_dataset.csv"
MODEL_DIR  = Path(__file__).resolve().parent.parent / "model"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

EMOTIONS = ["excited", "positive", "neutral", "negative", "angry"]
TOPICS   = [
    "winner_reaction",
    "presenter_performance",
    "ceremony_production",
    "diversity_representation",
    "fashion_red_carpet",
    "general_audience_reaction",
]

EMOTION_LABEL_MAP = {e: i for i, e in enumerate(EMOTIONS)}
F1_THRESHOLD = 0.78  # PRD acceptance criteria

def load_data():
    df = pd.read_csv(DATA_PATH)
    train_df = df[df["split"] == "train"].copy()
    test_df  = df[df["split"] == "test"].copy()
    train_df = train_df.dropna(subset=["content", "emotion", "topics"]).reset_index(drop=True)
    test_df  = test_df.dropna(subset=["content", "emotion", "topics"]).reset_index(drop=True)
    print(f"Train rows : {len(train_df)}")
    print(f"Test rows  : {len(test_df)}")
    return train_df, test_df

def build_vectorizer(train_texts):
    vectorizer = TfidfVectorizer(
        max_features=30000,
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=2,
    )
    vectorizer.fit(train_texts)
    return vectorizer

def train_emotion_classifier(X_train, y_train):
    model = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        use_label_encoder=False,
        eval_metric="mlogloss",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    return model

def train_topic_classifier(X_train, y_train_multilabel):
    base = XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.1,
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
    )
    model = OneVsRestClassifier(base)
    model.fit(X_train, y_train_multilabel)
    return model

def evaluate_emotion(model, X_test, y_test):
    preds = model.predict(X_test)
    print("\n── Emotion Classifier ──")
    print(classification_report(y_test, preds, target_names=EMOTIONS))
    per_class_f1 = f1_score(y_test, preds, average=None)
    all_pass = True
    for i, emotion in enumerate(EMOTIONS):
        status = "✓" if per_class_f1[i] >= F1_THRESHOLD else "✗ BELOW THRESHOLD"
        print(f"  {emotion:<28} F1: {per_class_f1[i]:.3f}  {status}")
        if per_class_f1[i] < F1_THRESHOLD:
            all_pass = False
    macro_f1 = f1_score(y_test, preds, average="macro")
    print(f"\n  Macro F1: {macro_f1:.3f}")
    if all_pass:
        print("  ✓ All emotion categories pass the 0.78 threshold")
    else:
        print("  ✗ Some categories below threshold — review training data")
    return macro_f1

def evaluate_topics(model, mlb, X_test, y_test_raw):
    y_test_bin = mlb.transform(y_test_raw)
    preds_bin  = model.predict(X_test)
    print("\n── Topic Classifier ──")
    print(classification_report(y_test_bin, preds_bin, target_names=TOPICS))
    per_class_f1 = f1_score(y_test_bin, preds_bin, average=None)
    all_pass = True
    for i, topic in enumerate(TOPICS):
        status = "✓" if per_class_f1[i] >= F1_THRESHOLD else "✗ BELOW THRESHOLD"
        print(f"  {topic:<35} F1: {per_class_f1[i]:.3f}  {status}")
        if per_class_f1[i] < F1_THRESHOLD:
            all_pass = False
    if all_pass:
        print("  ✓ All topic categories pass the 0.78 threshold")
    else:
        print("  ✗ Some categories below threshold — review training data")

def save_artefacts(vectorizer, emotion_model, topic_model, mlb):
    with open(MODEL_DIR / "vectorizer.pkl",    "wb") as f: pickle.dump(vectorizer,    f)
    with open(MODEL_DIR / "emotion_model.pkl", "wb") as f: pickle.dump(emotion_model, f)
    with open(MODEL_DIR / "topic_model.pkl",   "wb") as f: pickle.dump(topic_model,   f)
    with open(MODEL_DIR / "mlb.pkl",           "wb") as f: pickle.dump(mlb,           f)
    # Save label maps for API use
    meta = {
        "emotions": EMOTIONS,
        "topics":   TOPICS,
        "emotion_label_map": EMOTION_LABEL_MAP,
        "f1_threshold": F1_THRESHOLD,
    }
    with open(MODEL_DIR / "meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"\n✓ Artefacts saved to {MODEL_DIR}/")
    print("  - vectorizer.pkl")
    print("  - emotion_model.pkl")
    print("  - topic_model.pkl")
    print("  - mlb.pkl")
    print("  - meta.json")

def main():
    if not DATA_PATH.exists():
        print(f"Error: dataset not found at {DATA_PATH}", file=sys.stderr)
        print("Run data/generate_dataset.py first.", file=sys.stderr)
        sys.exit(1)

    print("=" * 62)
    print("  Pulse — Model Training")
    print("=" * 62)

    train_df, test_df = load_data()

    # ── Emotion labels ────────────────────────────────────────────────────────
    y_train_emotion = train_df["emotion"].map(EMOTION_LABEL_MAP).values
    y_test_emotion  = test_df["emotion"].map(EMOTION_LABEL_MAP).values

    # ── Topic labels (multi-label) ────────────────────────────────────────────
    def parse_topics(s):
        return [t.strip() for t in str(s).split("|") if t.strip() in TOPICS]

    y_train_topics_raw = train_df["topics"].apply(parse_topics).tolist()
    y_test_topics_raw  = test_df["topics"].apply(parse_topics).tolist()

    mlb = MultiLabelBinarizer(classes=TOPICS)
    mlb.fit(y_train_topics_raw)
    y_train_topics = mlb.transform(y_train_topics_raw)

    # ── Vectorise ─────────────────────────────────────────────────────────────
    print("\nBuilding TF-IDF vectoriser...")
    vectorizer = build_vectorizer(train_df["content"].tolist())
    X_train = vectorizer.transform(train_df["content"])
    X_test  = vectorizer.transform(test_df["content"])

    # ── Train ─────────────────────────────────────────────────────────────────
    print("Training emotion classifier (XGBoost 5-class)...")
    emotion_model = train_emotion_classifier(X_train, y_train_emotion)

    print("Training topic classifier (OneVsRest XGBoost)...")
    topic_model = train_topic_classifier(X_train, y_train_topics)

    # ── Evaluate ──────────────────────────────────────────────────────────────
    evaluate_emotion(emotion_model, X_test, y_test_emotion)
    evaluate_topics(topic_model, mlb, X_test, y_test_topics_raw)

    # ── Save ──────────────────────────────────────────────────────────────────
    save_artefacts(vectorizer, emotion_model, topic_model, mlb)

if __name__ == "__main__":
    main()
