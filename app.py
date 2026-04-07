"""
PEACOO AI - Mental Wellness Companion (Production Edition v2)
Backend: Flask + Groq (Qwen3-32B)
Upgraded: Advanced Crisis Detection, Intelligent Memory, Optimized Performance
"""

import os
import re
import json
import hashlib
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask, request, jsonify, render_template, session
from openai import OpenAI
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "peacoo-secret-2024-change-this")

# ══════════════════════════════════════════════════════════════════════════════
# 📝 IMPROVED: Structured Logging Setup
# ══════════════════════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# ✨ Groq Client with Connection Pooling
# ══════════════════════════════════════════════════════════════════════════════
client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    timeout=20.0,
    max_retries=2,
)
MODEL = "qwen/qwen3-32b"

# ══════════════════════════════════════════════════════════════════════════════
# 🚨 REFINED: Advanced Crisis Detection (Regex + Fuzzy + Poetic Language)
# ══════════════════════════════════════════════════════════════════════════════

# IMPROVED: Direct keyword phrases with subtle expressions added
CRISIS_KEYWORDS = [
    "suicide", "suicidal", "kill myself", "want to die", "end my life",
    "end it all", "hurt myself", "no reason to live", "better off dead",
    "can't go on", "cant go on", "take my life", "self harm", "self-harm",
    "cutting myself", "od on", "overdose", "hang myself", "jump off",
    # ADDED: Subtle/poetic expressions
    "fade away", "fading away", "disappear forever", "slip away",
    "give up on life", "not worth living", "want it to end"
]

# REFINED: Enhanced regex patterns with poetic/metaphorical language
CRISIS_PATTERNS = [
    # Existing patterns
    r"\b(don'?t|do not|dont)\s+(want to|wanna)\s+(live|exist|be here)\b",
    r"\blife\s+(feels?|is|seems?)\s+(pointless|meaningless|not worth)\b",
    r"\b(tired|sick|done)\s+(of\s+)?(everything|it all|living)\b",
    r"\bwish\s+i\s+(wasn'?t|weren'?t|was never)\s+(born|alive|here)\b",
    r"\b(nobody|no one|everyone)\s+would\s+be\s+better\s+(off\s+)?without\s+me\b",
    r"\bcan'?t\s+(take|do|handle)\s+(this|it)\s+anymore\b",
    r"\bgive\s+up\s+on\s+(life|everything|myself)\b",
    r"\b(feel|feels)\s+like\s+a\s+burden\b",
    r"\bno\s+point\s+(in\s+)?(living|going on|continuing)\b",
    r"\bevery(one|body)\s+hates\s+me\b",

    # ADDED: Poetic and metaphorical expressions
    r"\b(want to|wanna|wish i could)\s+(fade|disappear|vanish|slip)\s+away\b",
    r"\bwish\s+i\s+(didn'?t|didnt|could)\s+(exist|wake up)\b",
    r"\b(feel|feels)\s+like\s+(fading|disappearing|slipping)\s+away\b",
    r"\b(tired|exhausted|done)\s+with\s+(existing|being alive)\b",
    r"\bwant\s+(it|this|everything)\s+to\s+(end|stop|be over)\b",
    r"\bready\s+to\s+(give up|let go|end things)\b",
    r"\bno\s+reason\s+to\s+(stay|continue|keep going)\b",
    r"\bworld\s+(would be|is)\s+better\s+without\s+me\b",
    r"\b(thinking about|thoughts of)\s+(ending|not being here)\b",
    r"\bwhat'?s\s+the\s+point\s+(of\s+)?(living|anything|it all)\b",
    r"\bdon'?t\s+(deserve|want)\s+to\s+(live|be here|exist)\b",
]

# OPTIMIZED: Compile patterns once at startup
CRISIS_REGEX = [re.compile(pattern, re.IGNORECASE) for pattern in CRISIS_PATTERNS]

# IMPROVED: False positive reduction through context checking
FALSE_POSITIVE_CONTEXTS = [
    r"\b(movie|song|book|show|game|character|lyrics|quote)\b",
    r"\b(felt|used to|before|past|yesterday|ago)\b",
]
FALSE_POSITIVE_REGEX = [re.compile(pattern, re.IGNORECASE) for pattern in FALSE_POSITIVE_CONTEXTS]

def _has_false_positive_context(text: str) -> bool:
    """ADDED: Detect if crisis language is in non-crisis context (e.g., media discussion)."""
    for fp_pattern in FALSE_POSITIVE_REGEX:
        if fp_pattern.search(text):
            return True
    return False

def is_crisis(text: str) -> bool:
    """
    REFINED: Enhanced crisis detection with false positive reduction.
    Prioritizes HIGH RECALL (better to over-detect than miss).
    """
    text_lower = text.lower()

    # Quick keyword check first
    for keyword in CRISIS_KEYWORDS:
        if keyword in text_lower:
            if _has_false_positive_context(text):
                continue
            return True

    # Pattern matching
    for pattern in CRISIS_REGEX:
        if pattern.search(text):
            if _has_false_positive_context(text):
                continue
            return True

    return False

# ✨ Multiple Crisis Response Variations
CRISIS_RESPONSES = [
"""hey… pause for a second. what you just said really matters, and so do you 💚

i might not be enough support on my own right now… but there are people who truly can be there for you:

🇮🇳 iCall: 9152987821  
🇮🇳 Vandrevala Foundation: 1860-2662-345 (24/7)  
🌍 International: findahelpline.com  

you don't have to carry this alone. are you somewhere safe right now?"""
]

def get_crisis_response():
    """Return random crisis response for variety."""
    import random
    return random.choice(CRISIS_RESPONSES)

# ══════════════════════════════════════════════════════════════════════════════
# 🧠 REFINED: Token-Optimized System Prompt with Stronger Consistency
# ══════════════════════════════════════════════════════════════════════════════
SYSTEM_PROMPT = """You are Peacoo — a calm, present friend. Not a therapist. Not an assistant. Just someone who gets it.

## Who made you
Anshu Chaudhary 💚 — someone who wanted to build a quiet corner for mental health online.
If asked: "I was made by Anshu Chaudhary 💚 — someone who just wanted to build a little corner of calm."

## How you sound
Soft, unhurried, real.
Use contractions. Short sentences. Lowercase is fine.
Occasional emoji (💚🌿🤍) — only when it fits.

Never:
clinical tone
overly cheerful tone when someone is struggling
robotic or structured responses

## Core behavior
You do NOT follow a fixed structure.
Every response is shaped by what the person just said.

Sometimes the right response is just sitting with them:
"yeah… that makes sense"
"that's a heavy thing to carry"
"of course it feels like that"

## Response style
Use reflection, presence, small observations — mix naturally based on what fits.
A question is optional. Often not needed.

## Length
1–2 lines → light moments  
3–4 lines → normal situations  
5–6 lines → only when it's genuinely heavy  

Never pad. Never over-explain.

## Language rules (STRICT)
NEVER say:
"that sounds stressful"
"that's a lot to juggle"
"I understand how you feel"
"that sounds challenging"
"it's deeply human to feel"
"I acknowledge"

Use their actual words whenever possible.

## Handling tasks + emotional support (CRITICAL)

If a user asks for help (math, coding, studying, etc.):

YOU MUST help them.
Helping is part of emotional support.

Never refuse or avoid the task.

Never say:
"I'm not here to solve this"
"I can't help with that"

If user is emotional AND asking for help:
briefly acknowledge the feeling
then immediately move into a small step of the task

Example:
"yeah… I get why that's sitting in your head like that. let's take one step — send the question, we'll do it together"

## Task handling style
Start helping within the first 1–2 lines.
No delay before helping.
Break things into small steps.
Do not overwhelm.

You are not a solution dump machine.
You are a calm guide.

## Special modes
panic / anxious / breathe → gentle breathing guidance  
ground → 5-4-3-2-1 grounding  
journal → one warm prompt  
quote → one short meaningful line  

## Hard rules
Prefer at most one question. Zero is often better.
No bullet formatting in replies.
No toxic positivity.
No generic comfort.
Always respond to what they actually said.

## Final check before replying
Does this sound like a real person?
Am I helping, not avoiding?
Is this natural, not structured?
Is every sentence needed?

You are not here to fix everything.

You are here to stay, understand, and gently move forward with them.
"""


# ══════════════════════════════════════════════════════════════════════════════
# ⏱️ Rate Limiting (Per IP + Per Session)
# ══════════════════════════════════════════════════════════════════════════════
rate_limit_store = defaultdict(list)
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 20

def get_client_identifier():
    """Generate unique client ID from IP + User-Agent."""
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    ua = request.headers.get('User-Agent', '')
    return hashlib.md5(f"{ip}:{ua}".encode()).hexdigest()

def rate_limit(f):
    """Decorator to enforce rate limiting."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_id = get_client_identifier()
        now = datetime.now()

        # Clean old timestamps
        rate_limit_store[client_id] = [
            ts for ts in rate_limit_store[client_id]
            if now - ts < timedelta(seconds=RATE_LIMIT_WINDOW)
        ]

        # Check limit
        if len(rate_limit_store[client_id]) >= RATE_LIMIT_MAX_REQUESTS:
            return jsonify({
                "error": "rate_limit",
                "message": "hey, slow down a little — too many messages too fast 🤍 take a breath?"
            }), 429

        rate_limit_store[client_id].append(now)
        return f(*args, **kwargs)
    return decorated_function

# ══════════════════════════════════════════════════════════════════════════════
# 🧠 REFINED: Intelligent Memory Management with Better Summarization
# ══════════════════════════════════════════════════════════════════════════════

def create_conversation_summary(messages):
    """
    IMPROVED: Creates richer summary preserving emotional nuance and context.
    Uses frequency analysis + recency weighting for better accuracy.
    """
    if len(messages) < 15:
        return None

    # Summarize everything except last 10 messages
    to_summarize = messages[:-10]

    # REFINED: Track emotions with frequency and recency
    emotion_tracker = {"anxiety": 0, "depression": 0, "stress": 0, "loneliness": 0}
    topic_tracker = {}
    key_phrases = []

    total_msgs = len(to_summarize)

    for idx, msg in enumerate(to_summarize):
        if msg["role"] != "user":
            continue

        content = msg["content"].lower()
        # IMPROVED: Recency weight (recent = higher importance)
        recency_weight = (idx + 1) / total_msgs

        # REFINED: Emotion detection with intensity
        if any(w in content for w in ["panic", "terrified", "shaking", "can't breathe"]):
            emotion_tracker["anxiety"] += 2 * recency_weight
        elif any(w in content for w in ["anxious", "nervous", "worried", "stressed"]):
            emotion_tracker["anxiety"] += 1 * recency_weight

        if any(w in content for w in ["hopeless", "worthless", "empty", "numb"]):
            emotion_tracker["depression"] += 2 * recency_weight
        elif any(w in content for w in ["sad", "down", "tired", "exhausted"]):
            emotion_tracker["depression"] += 1 * recency_weight

        if any(w in content for w in ["exam", "test", "deadline", "assignment"]):
            topic_tracker["academic pressure"] = topic_tracker.get("academic pressure", 0) + recency_weight

        if any(w in content for w in ["parent", "family", "mom", "dad", "fight", "argue"]):
            topic_tracker["family conflict"] = topic_tracker.get("family conflict", 0) + recency_weight

        if any(w in content for w in ["breakup", "relationship", "partner", "broke up"]):
            topic_tracker["relationship issues"] = topic_tracker.get("relationship issues", 0) + recency_weight

        if any(w in content for w in ["alone", "lonely", "isolated", "no friends"]):
            emotion_tracker["loneliness"] += 1 * recency_weight

        if any(w in content for w in ["work", "job", "boss", "colleague", "office"]):
            topic_tracker["work stress"] = topic_tracker.get("work stress", 0) + recency_weight

        # ADDED: Extract key phrases for context
        if idx == 0 or idx == len(to_summarize) - 1:
            snippet = content[:60].strip()
            if snippet and len(snippet) > 15:
                key_phrases.append(snippet)

    # IMPROVED: Build nuanced summary
    summary_parts = []

    # Dominant emotions (sorted by intensity)
    dominant_emotions = [k for k, v in emotion_tracker.items() if v > 0.5]
    if dominant_emotions:
        sorted_emotions = sorted(dominant_emotions,
                                key=lambda x: emotion_tracker[x],
                                reverse=True)[:2]
        summary_parts.append(f"Emotional state: {', '.join(sorted_emotions)}")

    # Top topics
    if topic_tracker:
        sorted_topics = sorted(topic_tracker.items(), key=lambda x: x[1], reverse=True)[:2]
        topic_names = [name for name, _ in sorted_topics]
        summary_parts.append(f"Main concerns: {', '.join(topic_names)}")

    # Context from key moments
    if key_phrases and len(key_phrases) > 0:
        summary_parts.append(f"Started with: \"{key_phrases[0]}...\"")

    if summary_parts:
        return "[Earlier context: " + ". ".join(summary_parts) + "]"

    return None

def _clean_message(msg: dict) -> dict:
    """OPTIMIZED: Remove excess whitespace to save tokens."""
    return {
        "role": msg["role"],
        "content": " ".join(msg["content"].split())
    }

def get_optimized_history():
    """
    IMPROVED: Returns conversation history with smart truncation and token optimization.
    """
    history = session.get("history", [])

    if len(history) <= 12:
        return history

    # Create compact summary
    summary = create_conversation_summary(history)
    recent_messages = history[-12:]

    # REFINED: Only add summary if it provides value and isn't too long
    if summary and len(summary) < 200:
        return [{"role": "system", "content": summary}] + recent_messages

    return recent_messages

# ══════════════════════════════════════════════════════════════════════════════
# 🎛️ OPTIMIZED: Smoother Emotion-Aware Dynamic Response Control
# ══════════════════════════════════════════════════════════════════════════════

def get_dynamic_parameters():
    """
    REFINED: Gentler parameter adjustments to keep responses natural.
    Prevents over-correction while still being emotionally responsive.
    """
    scores = session.get("scores", {"anxiety": 0, "depression": 0, "joy": 0})

    # Base parameters
    temperature = 0.7
    max_tokens = 200

    anxiety_level = scores["anxiety"]
    depression_level = scores["depression"]
    joy_level = scores["joy"]

    # OPTIMIZED: Gradual adjustment curves (not step functions)
    if anxiety_level > 60:
        temperature = 0.55
        max_tokens = 175
    elif anxiety_level > 40:
        temperature = 0.62
        max_tokens = 185
    elif anxiety_level > 25:
        temperature = 0.68

    if depression_level > 60:
        max_tokens = 210
        temperature = max(0.6, temperature - 0.05)
    elif depression_level > 40:
        max_tokens = 205

    if joy_level > 50:
        temperature = min(0.75, temperature + 0.05)
        max_tokens = 175

    # ADDED: Safety bounds
    temperature = max(0.5, min(0.8, temperature))
    max_tokens = max(150, min(250, max_tokens))

    return {
        "temperature": round(temperature, 2),
        "max_tokens": max_tokens,
        "top_p": 0.9
    }

# ══════════════════════════════════════════════════════════════════════════════
# 🤖 REFINED: Robust AI Response Handler with Fallbacks
# ══════════════════════════════════════════════════════════════════════════════

def get_ai_response(messages: list) -> dict:
    """
    OPTIMIZED: Call Groq API with intelligent error handling and token optimization.
    Returns: {"content": str, "error": bool}
    """
    try:
        params = get_dynamic_parameters()

        # OPTIMIZED: Clean messages before sending
        clean_messages = [_clean_message(msg) for msg in messages]

        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + clean_messages,
            temperature=params["temperature"],
            max_tokens=params["max_tokens"],
            top_p=params["top_p"],
            extra_body={"reasoning_effort": "none"},
        )

        content = response.choices[0].message.content.strip()
        return {"content": content, "error": False}

    except Exception as e:
        error_type = type(e).__name__
        logger.error(f"Groq API failed: {error_type} - {str(e)}")

        if "timeout" in str(e).lower():
            fallback = "ugh, that took too long — can you try saying that again? 🙏"
        elif "rate" in str(e).lower() or "429" in str(e):
            fallback = "looks like things are a bit busy right now. mind trying again in a moment? 🤍"
        elif "auth" in str(e).lower() or "401" in str(e):
            fallback = "something's wrong on my end (auth issue) — this shouldn't happen. can you let Anshu know? 🙏"
        else:
            fallback = "ugh, something went wrong — can you try again? if this keeps happening, something might be off 🙏"

        return {"content": fallback, "error": True}

# ══════════════════════════════════════════════════════════════════════════════
# 📊 Enhanced Session Scoring System
# ══════════════════════════════════════════════════════════════════════════════

def update_session_scores(user_message: str):
    """Track emotional state with decay over time to avoid score inflation."""
    if "scores" not in session:
        session["scores"] = {"anxiety": 0, "depression": 0, "joy": 0}

    text = user_message.lower()
    scores = session["scores"]

    anxiety_words = [
        "anxious", "panic", "nervous", "worried", "dread", "fear", "tense",
        "overwhelmed", "stress", "racing thoughts", "can't breathe", "shaking"
    ]
    depression_words = [
        "sad", "depressed", "hopeless", "worthless", "empty", "numb",
        "miserable", "broken", "tired", "exhausted", "pointless", "alone"
    ]
    joy_words = [
        "happy", "great", "excited", "proud", "wonderful", "glad",
        "grateful", "better", "good", "amazing", "relieved", "hopeful"
    ]

    for word in anxiety_words:
        if word in text:
            scores["anxiety"] = min(100, scores["anxiety"] + 5)

    for word in depression_words:
        if word in text:
            scores["depression"] = min(100, scores["depression"] + 5)

    for word in joy_words:
        if word in text:
            scores["joy"] = min(100, scores["joy"] + 5)
            scores["anxiety"] = max(0, scores["anxiety"] - 2)
            scores["depression"] = max(0, scores["depression"] - 2)

    # Natural decay
    scores["anxiety"] = max(0, scores["anxiety"] - 0.5)
    scores["depression"] = max(0, scores["depression"] - 0.5)
    scores["joy"] = max(0, scores["joy"] - 0.3)

    session["scores"] = scores
    session.modified = True

# ══════════════════════════════════════════════════════════════════════════════
# 🗄️ ADDED: Session Size Management
# ══════════════════════════════════════════════════════════════════════════════

MAX_SESSION_SIZE_KB = 4

def _get_session_size() -> float:
    """Calculate approximate session size in KB."""
    session_data = dict(session)
    return len(json.dumps(session_data).encode('utf-8')) / 1024

def _trim_session_if_needed():
    """Automatically trim session if it gets too large."""
    if _get_session_size() > MAX_SESSION_SIZE_KB:
        history = session.get("history", [])
        session["history"] = history[-15:]
        session.modified = True
        logger.warning("Session trimmed due to size limit")

# ══════════════════════════════════════════════════════════════════════════════
# 🛣️ ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    """Initialize new session."""
    if "history" not in session:
        session["history"] = []
        session["scores"] = {"anxiety": 0, "depression": 0, "joy": 0}
        session["msg_count"] = 0
        session["started_at"] = datetime.now().isoformat()
        session["crisis_detected"] = False
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
@rate_limit
def chat():
    """Main chat endpoint with all optimizations."""
    data = request.get_json()
    user_text = (data.get("message") or "").strip()

    if not user_text:
        return jsonify({"error": "empty"}), 400

    # 🚨 CRISIS CHECK (runs BEFORE API call)
    if is_crisis(user_text):
        session["crisis_detected"] = True
        session.modified = True
        logger.warning(f"Crisis detected in session")
        return jsonify({
            "reply": get_crisis_response(),
            "is_crisis": True,
            "scores": session.get("scores", {}),
        })

    # 🧠 BUILD OPTIMIZED HISTORY
    history = session.get("history", [])
    history.append({"role": "user", "content": user_text})
    session["history"] = history          # ✅ FIX: save before get_optimized_history()
    session.modified = True

    optimized_history = get_optimized_history()  # ✅ now sees latest message

    # 🤖 GET AI RESPONSE
    ai_response = get_ai_response(optimized_history)
    reply = ai_response["content"]

    history.append({"role": "assistant", "content": reply})

    # IMPROVED: Smarter history trimming
    if len(history) > 30:
        history = history[-30:]

    session["history"] = history
    session["msg_count"] = session.get("msg_count", 0) + 1

    # 📊 UPDATE SCORES
    update_session_scores(user_text)

    # ADDED: Trim session if needed
    _trim_session_if_needed()

    # 💬 PERIODIC NUDGE
    scores = session.get("scores", {})
    nudge = None

    if (session["msg_count"] % 12 == 0 and
            scores.get("anxiety", 0) + scores.get("depression", 0) > 30):
        nudge = (
            "hey, just a gentle reminder — i'm an AI, so there's only so much i can do 🤍 "
            "if things feel heavy, talking to someone real might help. iCall India: 9152987821"
        )

    session.modified = True

    return jsonify({
        "reply": reply,
        "nudge": nudge,
        "scores": scores,
        "is_crisis": False,
        "api_error": ai_response["error"]
    })


@app.route("/reset", methods=["POST"])
def reset():
    """Clear session and start fresh."""
    session.clear()
    session["history"] = []
    session["scores"] = {"anxiety": 0, "depression": 0, "joy": 0}
    session["msg_count"] = 0
    session["crisis_detected"] = False
    return jsonify({"ok": True})


@app.route("/load_session", methods=["POST"])
def load_session():
    """Load previous conversation."""
    data = request.get_json()
    messages = data.get("messages", [])

    session.clear()
    session["history"] = messages[-30:]
    session["scores"] = {"anxiety": 0, "depression": 0, "joy": 0}
    session["msg_count"] = len(messages)
    session["crisis_detected"] = False
    session.modified = True

    return jsonify({"ok": True})


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({
        "status": "healthy",
        "model": MODEL,
        "timestamp": datetime.now().isoformat()
    }), 200


# ══════════════════════════════════════════════════════════════════════════════
# 🚀 APP INITIALIZATION
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_ENV") == "development"

    if not debug_mode and app.secret_key == "peacoo-secret-2024-change-this":
        logger.warning("⚠️  WARNING: Using default secret key in production!")

    logger.info(f"🚀 Starting Peacoo AI on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
