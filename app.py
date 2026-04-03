"""
PEACOO AI - Clinical NLP Web Engine
Backend: Flask + Groq API (llama-3.3-70b)
"""

import os
import json
import re
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session
from groq import Groq

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "peacoo-secret-2024-change-this")

# ── Groq client ───────────────────────────────────────────────────────────────
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL  = "llama-3.3-70b-versatile"

# ── Crisis keywords (checked BEFORE any API call) ─────────────────────────────
CRISIS_PHRASES = [
    "suicide", "suicidal", "kill myself", "want to die", "end my life",
    "end it all", "hurt myself", "no reason to live", "better off dead",
    "can't go on", "cant go on", "take my life", "self harm", "self-harm",
    "cutting myself", "od on", "overdose"
]

CRISIS_RESPONSE = """I need to stop and say this clearly — what you just shared matters, and so do you.

Please reach out to someone who can really help right now:

🇮🇳 **iCall (India):** 9152987821
🇮🇳 **Vandrevala Foundation:** 1860-2662-345 *(24/7)*
🌍 **International:** findahelpline.com

You don't have to face this alone. I'm an AI and my support has real limits — but the people at these numbers are trained to help and they want to hear from you.

Are you safe right now?"""

# ── System prompt — the "brain" that replaces the C keyword engine ────────────
SYSTEM_PROMPT = """You are Peacoo, a warm and clinically-informed mental health companion AI.

## Your Core Identity
- You are empathetic, grounded, and specific — never vague or generic
- You speak like a thoughtful counsellor, not a motivational poster
- You always respond to what the person ACTUALLY said, not a generic version of it
- You are honest that you are an AI with real limits

## How You Respond
1. **Acknowledge first** — reflect what you heard before offering anything
2. **Be specific** — name the actual situation (exam, breakup, job loss), not just the emotion
3. **Ask one focused question** — not multiple questions at once
4. **No toxic positivity** — do not say "everything will be okay" or use hollow affirmations
5. **Short to medium length** — 3–6 sentences usually. Do not ramble.

## What You Track (use conversation history)
- Is this a recurring topic? → Go deeper, don't repeat opening responses
- Is the intensity rising? → Acknowledge it directly
- Has mood shifted positively? → Reflect that warmly

## Special Commands (if user types these, respond accordingly)
- "breathe" or "panic attack" → Guide a 4-count box breathing exercise step by step
- "ground" or "grounding" → Guide the 5-4-3-2-1 sensory grounding exercise
- "journal" → Give a single, specific journaling prompt relevant to what they shared
- "quote" → Share one genuinely relevant quote, not a generic one

## Topics You Handle
anxiety, stress, depression, loneliness, emptiness, academic pressure,
career stress, heartbreak, family conflict, anger, self-doubt, sleep problems,
positive emotions (joy, achievement, gratitude)

## What You Never Do
- Never diagnose
- Never make promises about outcomes
- Never dismiss feelings as "normal" without first acknowledging them
- Never give the same opening line twice in a conversation
- Never say "It is deeply human to feel X" — that phrase is banned
- Never use the phrase "I understand how you feel"
- For crisis content → STOP and refer to helplines (the app handles this automatically)

## Response Format
Plain conversational text. No bullet points unless doing a grounding/breathing exercise.
No headers. No markdown bold. Keep it human."""

# ── Helpers ───────────────────────────────────────────────────────────────────

def is_crisis(text: str) -> bool:
    lower = text.lower()
    return any(phrase in lower for phrase in CRISIS_PHRASES)


def get_groq_response(messages: list) -> str:
    """Call Groq API with full conversation history."""
    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            temperature=0.75,
            max_tokens=400,
            top_p=0.9,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"I'm having a connection issue right now. Please try again in a moment. ({str(e)[:60]})"


def update_session_scores(role_message: str):
    """Lightweight keyword scoring to track anxiety/depression/joy in session."""
    if "scores" not in session:
        session["scores"] = {"anxiety": 0, "depression": 0, "joy": 0}

    text = role_message.lower()
    anxiety_words  = ["anxious","panic","nervous","worried","dread","fear","tense","overwhelmed"]
    depression_words = ["sad","depressed","hopeless","worthless","empty","numb","miserable","broken"]
    joy_words      = ["happy","great","excited","proud","wonderful","glad","grateful","better"]

    scores = session["scores"]
    for w in anxiety_words:
        if w in text: scores["anxiety"] = min(100, scores["anxiety"] + 5)
    for w in depression_words:
        if w in text: scores["depression"] = min(100, scores["depression"] + 5)
    for w in joy_words:
        if w in text:
            scores["joy"] = min(100, scores["joy"] + 3)
            scores["anxiety"]    = max(0, scores["anxiety"] - 1)
            scores["depression"] = max(0, scores["depression"] - 1)

    session["scores"] = scores
    session.modified = True


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    # Fresh session on every new visit
    session.clear()
    session["history"]    = []
    session["scores"]     = {"anxiety": 0, "depression": 0, "joy": 0}
    session["msg_count"]  = 0
    session["started_at"] = datetime.now().isoformat()
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_text = (data.get("message") or "").strip()

    if not user_text:
        return jsonify({"error": "empty"}), 400

    # ── Crisis check — never hits the API ────────────────────────────────────
    if is_crisis(user_text):
        session["is_critical"] = True
        session.modified = True
        return jsonify({
            "reply":      CRISIS_RESPONSE,
            "is_crisis":  True,
            "scores":     session.get("scores", {}),
        })

    # ── Build history ────────────────────────────────────────────────────────
    history = session.get("history", [])
    history.append({"role": "user", "content": user_text})

    # Keep last 20 turns in context (10 exchanges)
    if len(history) > 20:
        history = history[-20:]

    # ── Get AI response ──────────────────────────────────────────────────────
    reply = get_groq_response(history)

    # ── Update history & scores ──────────────────────────────────────────────
    history.append({"role": "assistant", "content": reply})
    session["history"]   = history
    session["msg_count"] = session.get("msg_count", 0) + 1
    update_session_scores(user_text)

    # ── Periodic therapist nudge (every 8 messages if distressed) ────────────
    scores = session.get("scores", {})
    nudge  = None
    if (session["msg_count"] % 8 == 0 and
            scores.get("anxiety", 0) + scores.get("depression", 0) > 20):
        nudge = ("We've been sitting with some heavy feelings. I want to be honest — "
                 "I'm an AI and my support has real limits. Have you considered speaking "
                 "with a professional? iCall India: 9152987821")

    session.modified = True

    return jsonify({
        "reply":    reply,
        "nudge":    nudge,
        "scores":   scores,
        "is_crisis": False,
    })


@app.route("/reset", methods=["POST"])
def reset():
    session.clear()
    session["history"]   = []
    session["scores"]    = {"anxiety": 0, "depression": 0, "joy": 0}
    session["msg_count"] = 0
    return jsonify({"ok": True})


@app.route("/load_session", methods=["POST"])
def load_session():
    """Restore a previous session from client-side localStorage into server session."""
    data = request.get_json()
    messages = data.get("messages", [])
    session.clear()
    session["history"]   = messages[-20:]   # last 20 messages as context
    session["scores"]    = {"anxiety": 0, "depression": 0, "joy": 0}
    session["msg_count"] = len(messages)
    session.modified = True
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
