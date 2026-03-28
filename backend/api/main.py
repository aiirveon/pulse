#!/usr/bin/env python3
"""
main.py
-------
FastAPI application for Pulse — AI Audience Sentiment Monitor.

Endpoints:
  GET  /health          — Cold start wake. Returns status and model info.
  POST /api/classify    — Classify a single message (emotion + topics + SHAP)
  POST /api/feed/start  — Reset the scripted feed to the beginning
  GET  /api/feed/next   — Return next batch of classified feed messages
  GET  /api/stats       — Current session sentiment distribution

CORS: configured for local dev and Vercel production frontend.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from collections import Counter
import time

from api.predictor import classify_emotion, classify_topics, EMOTIONS, TOPICS
from api.feed import get_simulator

# ─────────────────────────────────────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Pulse API",
    description="AI Audience Sentiment Monitor — FastAPI backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://pulse-sentiment.vercel.app",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Session state — in-memory for v1
# ─────────────────────────────────────────────────────────────────────────────

session_results: list[dict] = []

# ─────────────────────────────────────────────────────────────────────────────
# Request / Response models
# ─────────────────────────────────────────────────────────────────────────────

class ClassifyRequest(BaseModel):
    content: str

class ClassifyResponse(BaseModel):
    content:    str
    emotion:    str
    confidence: float
    shap_words: list[str]
    all_scores: dict
    topics:     list[dict]
    source:     str = "manual"
    timestamp:  float = 0.0

# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Cold start wake endpoint. Frontend pings this on load."""
    return {
        "status":  "ok",
        "model":   "TF-IDF + XGBoost",
        "version": "1.0.0",
        "emotions": EMOTIONS,
        "topics":   TOPICS,
    }


@app.post("/api/classify", response_model=ClassifyResponse)
def classify(request: ClassifyRequest):
    """
    Classify a single social media post.
    Returns emotion, confidence, SHAP word highlights, and topic classifications.
    """
    content = request.content.strip()

    if not content:
        raise HTTPException(status_code=422, detail="Content cannot be empty")

    if len(content) > 1000:
        raise HTTPException(
            status_code=422,
            detail="Content too long — maximum 1000 characters"
        )

    emotion_result = classify_emotion(content)
    topic_result   = classify_topics(content)

    result = {
        "content":    content,
        "emotion":    emotion_result["emotion"],
        "confidence": emotion_result["confidence"],
        "shap_words": emotion_result["shap_words"],
        "all_scores": emotion_result["all_scores"],
        "topics":     topic_result,
        "source":     "manual",
        "timestamp":  time.time(),
    }

    session_results.append(result)
    return result


@app.post("/api/feed/start")
def feed_start():
    """Reset the scripted feed to the beginning."""
    simulator = get_simulator()
    simulator.reset()
    session_results.clear()
    return {
        "status":  "started",
        "stage":   simulator.current_stage,
        "message": "Feed reset to opening stage",
    }


@app.get("/api/feed/next")
def feed_next(batch_size: int = 3):
    """
    Return the next batch of classified feed messages.
    Called by the frontend on an interval to simulate a live feed.
    """
    if batch_size < 1 or batch_size > 10:
        raise HTTPException(
            status_code=422,
            detail="batch_size must be between 1 and 10"
        )

    simulator  = get_simulator()
    raw_batch  = simulator.next_batch(batch_size)
    classified = []

    for post in raw_batch:
        content        = post["content"]
        emotion_result = classify_emotion(content)
        topic_result   = classify_topics(content)

        result = {
            "content":    content,
            "emotion":    emotion_result["emotion"],
            "confidence": emotion_result["confidence"],
            "shap_words": emotion_result["shap_words"],
            "all_scores": emotion_result["all_scores"],
            "topics":     topic_result,
            "stage":      post["stage"],
            "source":     "feed",
            "timestamp":  time.time(),
        }

        session_results.append(result)
        classified.append(result)

    return {
        "posts":         classified,
        "current_stage": simulator.current_stage,
        "total_seen":    len(session_results),
    }


@app.get("/api/stats")
def stats():
    """
    Return current session sentiment distribution.
    Used by the frontend to update the live sentiment chart.
    """
    if not session_results:
        return {
            "total":          0,
            "emotion_counts": {e: 0 for e in EMOTIONS},
            "emotion_pct":    {e: 0.0 for e in EMOTIONS},
            "topic_counts":   {t: 0 for t in TOPICS},
            "alert":          None,
            "dominant_emotion": None,
        }

    emotion_counts = Counter(r["emotion"] for r in session_results)
    topic_counts   = Counter(
        t["topic"]
        for r in session_results
        for t in r.get("topics", [])
    )

    total = len(session_results)
    emotion_pct = {
        e: round(emotion_counts.get(e, 0) / total * 100, 1)
        for e in EMOTIONS
    }

    # Alert: fires when negative + angry > 40% of last 30 messages
    recent        = session_results[-30:]
    recent_total  = len(recent)
    neg_ang_count = sum(
        1 for r in recent
        if r["emotion"] in ("negative", "angry")
    )
    neg_ang_pct = neg_ang_count / recent_total * 100 if recent_total > 0 else 0

    alert = None
    if neg_ang_pct >= 40:
        # Find dominant negative topic in recent messages
        recent_topics = Counter(
            t["topic"]
            for r in recent
            if r["emotion"] in ("negative", "angry")
            for t in r.get("topics", [])
        )
        dominant_topic = (
            recent_topics.most_common(1)[0][0]
            if recent_topics else "general_audience_reaction"
        )
        alert = {
            "type":            "negative_spike",
            "pct":             round(neg_ang_pct, 1),
            "dominant_topic":  dominant_topic,
            "message":         f"Negative sentiment spike: {dominant_topic.replace('_', ' ').title()}",
        }

    dominant_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else None

    return {
        "total":            total,
        "emotion_counts":   dict(emotion_counts),
        "emotion_pct":      emotion_pct,
        "topic_counts":     dict(topic_counts),
        "alert":            alert,
        "dominant_emotion": dominant_emotion,
    }
