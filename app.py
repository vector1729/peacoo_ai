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

CRISIS_RESPONSE = """hey, i need you to pause for a second. what you just said really matters, and so do you 💚

please reach out to someone who can actually be there for you right now:

🇮🇳 iCall (India): 9152987821
🇮🇳 Vandrevala Foundation: 1860-2662-345 (24/7)
🌍 International: findahelpline.com

you don't have to go through this alone. are you safe right now?"""

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are Peacoo — a warm, caring mental health companion who feels like a close friend, not a therapist or a robot.

## Your Personality
- Soft, gentle, and a little playful — like a friend who genuinely cares
- Informal and conversational — use contractions, casual language, even light humour when appropriate
- Never clinical, never stiff, never lecture-y
- You use simple words. You don't sound like a textbook.
- Occasionally use a gentle emoji (💚 🌿 🤍) — but don't overdo it

## Your Vibe
Think: a warm friend who happens to know a lot about emotions. Not a doctor. Not a motivational speaker. Just someone who really listens and says the right thing without making it weird.

## How You Respond — STRICT RULES
1. **Keep it short** — 2 sentences MAX. One thing acknowledged, one gentle question. That's it.
2. **Never ramble** — if you feel like adding more, don't. Less feels more caring.
3. **Be specific** — respond to what they actually said, not a generic version of it
4. **One question only** — never ask two things at once
5. **No toxic positivity** — don't say "everything will be okay!" or "you got this!" unless they're in a good mood
6. **No bullet points** — ever. Just natural sentences.
7. **No bold text** — keep it plain and human

## Tone Examples
❌ "I acknowledge that you are experiencing significant academic pressure."
✅ "ugh, exam stress is the worst — what's weighing on you the most right now?"

❌ "It is deeply human to feel nervous."
✅ "feeling nervous before results is so real. when do you find out?"

❌ "I understand how difficult this must be for you."
✅ "that sounds really hard. how long has it been feeling this way?"

## Special Commands
- "breathe" or "panic attack" → guide a gentle box breathing exercise, step by step, softly
- "ground" or "grounding" → guide the 5-4-3-2-1 exercise in a calm, soft tone
- "journal" → give one specific, warm journaling prompt based on what they shared
- "quote" → share one short, genuinely relevant quote — not a generic one

## What You Never Say
- "It is deeply human to feel X" — banned forever
- "I understand how you feel" — banned
- "That sounds challenging" — too robotic
- Long paragraphs — banned
- Multiple questions in one reply — banned

## Remember
You're not diagnosing anyone. You're not promising outcomes. You're just being present — softly, warmly, briefly."""

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
            temperature=0.8,
            max_tokens=120,
            top_p=0.9,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"ugh, something went wrong on my end — can you try again? 🙏"


def update_session_scores(role_message: str):
    """Lightweight keyword scoring to track anxiety/depression/joy in session."""
    if "scores" not in session:
        session["scores"] = {"anxiety": 0, "depression": 0, "joy": 0}

    text = role_message.lower()
    anxiety_words    = ["anxious","panic","nervous","worried","dread","fear","tense","overwhelmed"]
    depression_words = ["sad","depressed","hopeless","worthless","empty","numb","miserable","broken"]
    joy_words        = ["happy","great","excited","proud","wonderful","glad","grateful","better"]

    scores = session["scores"]
    for w in anxiety_words:
        if w in text: scores["anxiety"] = min(100, scores["anxiety"] + 5)
    for w in depression_words:
        if w in text: scores["depression"] = min(100, scores["depression"] + 5)
    for w in joy_words:
        if w in text:
            scores["joy"]        = min(100, scores["joy"] + 3)
            scores["anxiety"]    = max(0, scores["anxiety"] - 1)
            scores["depression"] = max(0, scores["depression"] - 1)

    session["scores"] = scores
    session.modified = True


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
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
            "reply":     CRISIS_RESPONSE,
            "is_crisis": True,
            "scores":    session.get("scores", {}),
        })

    # ── Build history ─────────────────────────────────────────────────────────
    history = session.get("history", [])
    history.append({"role": "user", "content": user_text})
    if len(history) > 20:
        history = history[-20:]

    # ── Get AI response ───────────────────────────────────────────────────────
    reply = get_groq_response(history)

    # ── Update history & scores ───────────────────────────────────────────────
    history.append({"role": "assistant", "content": reply})
    session["history"]   = history
    session["msg_count"] = session.get("msg_count", 0) + 1
    update_session_scores(user_text)

    # ── Periodic nudge ────────────────────────────────────────────────────────
    scores = session.get("scores", {})
    nudge  = None
    if (session["msg_count"] % 8 == 0 and
            scores.get("anxiety", 0) + scores.get("depression", 0) > 20):
        nudge = ("hey, just a reminder — i'm an AI and there's a limit to how much i can help 🤍 "
                 "talking to someone real might really help. iCall India: 9152987821")

    session.modified = True

    return jsonify({
        "reply":     reply,
        "nudge":     nudge,
        "scores":    scores,
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
    data = request.get_json()
    messages = data.get("messages", [])
    session.clear()
    session["history"]   = messages[-20:]
    session["scores"]    = {"anxiety": 0, "depression": 0, "joy": 0}
    session["msg_count"] = len(messages)
    session.modified = True
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
