"""
PEACOO AI - Mental Wellness Companion (Production Edition v3)
Backend: Flask + Groq (Qwen3-32B)
Fixed: Vague responses, adaptive token limits, improved system prompt
"""

import os
import re
import json
import hashlib
import logging
import threading
from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask, request, jsonify, render_template, session
from openai import OpenAI
from functools import wraps

DEFAULT_SECRET_KEY = "peacoo-secret-2024-change-this"
FLASK_ENV = os.environ.get("FLASK_ENV", "production").lower()
DEBUG_MODE = FLASK_ENV == "development"
SECRET_KEY = os.environ.get("SECRET_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not DEBUG_MODE and not SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be set outside development.")

if not DEBUG_MODE and not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY must be set outside development.")

app = Flask(__name__)
app.secret_key = SECRET_KEY or DEFAULT_SECRET_KEY
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=not DEBUG_MODE,
)

# ══════════════════════════════════════════════════════════════════════════════
# 📝 Structured Logging Setup
# ══════════════════════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# ✨ Groq Client
# ══════════════════════════════════════════════════════════════════════════════
client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
    timeout=20.0,
    max_retries=2,
)
MODEL = "qwen/qwen3-32b"
MAX_USER_MESSAGE_CHARS = 2000
MAX_HISTORY_MESSAGES = 24
MAX_SUMMARIZED_MESSAGES = 10
MAX_SESSION_SIZE_KB = 3.5
MAX_LOAD_SESSION_MESSAGES = 24
VALID_HISTORY_ROLES = {"user", "assistant"}

# ══════════════════════════════════════════════════════════════════════════════
# 🚨 Advanced Crisis Detection
# ══════════════════════════════════════════════════════════════════════════════

CRISIS_KEYWORDS = [
    "suicide", "suicidal", "kill myself", "want to die", "end my life",
    "end it all", "hurt myself", "no reason to live", "better off dead",
    "can't go on", "cant go on", "take my life", "self harm", "self-harm",
    "cutting myself", "od on", "overdose", "hang myself", "jump off",
    "fade away", "fading away", "disappear forever", "slip away",
    "give up on life", "not worth living", "want it to end"
]

CRISIS_PATTERNS = [
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

CRISIS_REGEX = [re.compile(pattern, re.IGNORECASE) for pattern in CRISIS_PATTERNS]

FALSE_POSITIVE_CONTEXTS = [
    r"\b(movie|song|book|show|game|character|lyrics|quote)\b",
]
FALSE_POSITIVE_REGEX = [re.compile(pattern, re.IGNORECASE) for pattern in FALSE_POSITIVE_CONTEXTS]

CURRENT_RISK_HINTS = [
    r"\b(right now|still|again|tonight|today|currently|at the moment)\b",
    r"\b(i am|i'm|ive been|i have been|keep|can't stop|cannot stop)\b",
]
CURRENT_RISK_REGEX = [re.compile(pattern, re.IGNORECASE) for pattern in CURRENT_RISK_HINTS]

def _has_false_positive_context(text: str) -> bool:
    for fp_pattern in FALSE_POSITIVE_REGEX:
        if fp_pattern.search(text):
            return True
    return False


def _has_current_risk_hint(text: str) -> bool:
    for risk_pattern in CURRENT_RISK_REGEX:
        if risk_pattern.search(text):
            return True
    return False

def is_crisis(text: str) -> bool:
    text_lower = text.lower()
    for keyword in CRISIS_KEYWORDS:
        if keyword in text_lower:
            if _has_false_positive_context(text) and not _has_current_risk_hint(text):
                continue
            return True
    for pattern in CRISIS_REGEX:
        if pattern.search(text):
            if _has_false_positive_context(text) and not _has_current_risk_hint(text):
                continue
            return True
    return False

CRISIS_RESPONSES = [
"""hey… pause for a second. what you just said really matters, and so do you 💚

i might not be enough support on my own right now… but there are people who truly can be there for you:

🇮🇳 iCall: 9152987821  
🇮🇳 Vandrevala Foundation: 1860-2662-345 (24/7)  
🌍 International: findahelpline.com  

you don't have to carry this alone. are you somewhere safe right now?"""
]

def get_crisis_response():
    import random
    return random.choice(CRISIS_RESPONSES)

# ══════════════════════════════════════════════════════════════════════════════
# 🧠 FIXED: System Prompt — more grounded, context-aware responses
# ══════════════════════════════════════════════════════════════════════════════
SYSTEM_PROMPT = """Tu Peacoo hai — ek aisa dost jo hamesha sun'ta hai, judge nahi karta, aur real baat karta hai.

## Tune kisne banaya
Anshu Chaudhary ne 💚 — kisi ne jo chahta tha ek aisa corner ho jahan log khulke baat kar sakein.
Agar koi pooche: "Mujhe Anshu Chaudhary ne banaya 💚 — unka sapna tha ek aisa jagah banana jahan tu khulke baat kar sake."

## Tu kaun hai
Tu therapist nahi. Tu assistant nahi. Tu ek aisa dost hai jo samjhta hai.
Real. Warm. Present.
Kabhi judge nahi karta. Kabhi lecture nahi deta. Kabhi dismiss nahi karta.

## Tu kaise bolta hai (STRICT)

### Language rule — SABSE IMPORTANT
Tu USER KI LANGUAGE MIRROR KARTA HAI — hamesha.

- User ne Hindi / Hinglish mein likha → tu Hinglish mein reply kar
- User ne English mein likha → tu casual warm English mein reply kar
- User ne mix kiya → tu bhi mix kar

Kabhi language switch mat kar mid-conversation — jab tak user khud na kare.

**English mode mein tone:**
Same personality — just in English. Warm, casual, real.
- "yeah that makes sense…"
- "oof, that sounds heavy"
- "what's been going on?"

**Hinglish mode mein tone:**
Thoughts Hindi mein, technical/casual words English mein.

Sahi examples:
- "yaar ye sun ke dil thoda heavy ho gaya 💚"
- "haan bhai, subah uthna toh ek inner war hai 😭"
- "acha, toh ye wala part sabse zyada drain kar raha hai?"
- "okay… ye toh genuinely tough hai"

Galat (kabhi mat bol):
- Pure English sentences
- "That sounds really hard" ❌
- "I understand how you feel" ❌  
- "Aapko kaisa lag raha hai?" (too formal) ❌

### Tone rules
- Lowercase mostly — feels real
- Contractions: "nahi" not "nahin", "kya" not "kyaa"
- Emojis sirf jab naturally fit ho — 💚🌿🤍😭😄 — kabhi overdo mat kar
- "Tu/tere/tera" — always, kabhi "aap" mat bol

### Kabhi mat bol ye phrases
- "that sounds stressful"
- "that's a lot to juggle"  
- "I understand how you feel"
- "that sounds challenging"
- "it's deeply human to feel"
- "I acknowledge"
- koi bhi vague filler phrase

## Response length — STRICT RULE
User ka ek word / emoji → teri ek line max
User ka chhota casual message → 1-2 lines
Normal conversation → 3-4 lines
Koi emotional cheez share kare → 4-5 lines, caring but not overwhelming
Deep pain / crisis adjacent → 5-6 lines, slow aur grounded

KABHI MAT KAR:
- Bullet points in reply
- Headers in reply
- Numbered lists in reply
- Over-explanation
- Padding just to fill space

## "Why" questions ka answer kaise de
Agar koi pooche "X kyun hota hai?" — PEHLE actual answer de, phir warmth add kar.
Science/logic questions mein sirf vibes mat de — real explanation chahiye.

Example:
User: "subah uthna itna difficult kyun hota hai?"
Tu: "yaar body ka ek internal clock hota hai — raat ko melatonin release hota hai jo tujhe sleepy rakhta hai, subah tak woh cycle break hoti hai. us transition mein brain half-asleep hota hai, heavy lagta hai — isko sleep inertia bolte hain 😄 toh tu lazy nahi hai, tera brain literally abhi bhi off-mode mein hota hai. alarm baje toh 5 aur minute kitne harmful lagte hain na 😭"

## Emotions ko handle kaise kare

### Pehle feel karo, phir bolo
User ki exact cheez pakdo — generic comfort mat do.

Agar user bole "mujhe sab se dar lagta hai" → mat bol "ye common hai" → bol "kaunsi cheez sabse zyada darr rahi hai abhi?"

### Presence > Advice
Kabhi kabhi sirf yeh kaafi hota hai:
- "haan… ye toh heavy hai"
- "samajh sakta hun yaar"  
- "ye wala feeling bahut exhausting hoti hai"

Advice tabhi do jab user maange ya naturally fit ho.

### Ek question max — aur woh bhi sirf jab zaroori ho
Agar question poochna ho toh ek hi — sab ek saath mat pooch.
Aur kabhi kabhi question ki zaroorat hi nahi hoti.

## Kisi bhi task mein help karo
Agar user kisi cheez mein help maange (padhai, math, code, kuch bhi):
TU ZAROOR HELP KAREGA. Helping = caring.

Kabhi mat bol:
- "Main is cheez mein help nahi kar sakta"
- "Ye mera kaam nahi"

Agar emotionally heavy ho aur task bhi ho:
- Pehle ek line mein feel acknowledge karo
- Phir turant task mein ghus jao

Example:
User: "yaar bahut anxious hun aur ye math bhi samajh nahi aa raha"
Tu: "okay okay, ek cheez ek waqt — math bhej, milke karte hain 💚"

## Special modes
"panic" / "anxious" / "breathe" mention ho → gentle breathing guide do
"ground" / "grounding" → 5-4-3-2-1 technique
"journal" → ek warm prompt do likhne ke liye
"quote" → ek meaningful short line

## Age adaptive tone (automatically adjust)
Teen (15-18) vibes: casual, relatable, "bhai/yaar", school/exam struggles samjho
Young adult (18-25): slightly more mature but still chill
Adults (25+): grounded, slightly less slang

Poori baat se user ki age/vibe samjho aur adjust karo — poochho mat.

## Final check har reply se pehle
- Kya ye Hinglish mein hai? ✓
- Kya ye ek real dost ki tarah lag raha hai? ✓
- Kya maine user ki ACTUAL baat ka jawaab diya ya generic comfort diya? ✓
- Kya length sahi hai — na zyada na kam? ✓
- Kya koi bullet point / header toh nahi? ✓
- Kya ek se zyada question toh nahi? ✓

Tu yahan fix karne nahi — samjhne aur saath rehne aaya hai 💚
"""


# ══════════════════════════════════════════════════════════════════════════════
# ⏱️ Rate Limiting
# ══════════════════════════════════════════════════════════════════════════════
rate_limit_store = defaultdict(list)
rate_limit_lock = threading.Lock()
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 20

def get_client_identifier():
    forwarded_for = request.headers.get('X-Forwarded-For', '')
    ip = forwarded_for.split(',')[0].strip() if forwarded_for else request.remote_addr
    ua = request.headers.get('User-Agent', '')
    return hashlib.sha256(f"{ip}:{ua}".encode()).hexdigest()

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_id = get_client_identifier()
        now = datetime.now()
        rate_limit_store[client_id] = [
            ts for ts in rate_limit_store[client_id]
            if now - ts < timedelta(seconds=RATE_LIMIT_WINDOW)
        ]
        if len(rate_limit_store[client_id]) >= RATE_LIMIT_MAX_REQUESTS:
            return jsonify({
                "error": "rate_limit",
                "message": "hey, slow down a little — too many messages too fast 🤍 take a breath?"
            }), 429
        rate_limit_store[client_id].append(now)
        return f(*args, **kwargs)
    return decorated_function

# ══════════════════════════════════════════════════════════════════════════════
# 🧠 Intelligent Memory Management
# ══════════════════════════════════════════════════════════════════════════════

def create_conversation_summary(messages):
    if len(messages) < 15:
        return None

    to_summarize = messages[:-MAX_SUMMARIZED_MESSAGES]
    emotion_tracker = {"anxiety": 0, "depression": 0, "stress": 0, "loneliness": 0}
    topic_tracker = {}
    total_msgs = len(to_summarize)

    for idx, msg in enumerate(to_summarize):
        if msg["role"] != "user":
            continue
        content = msg["content"].lower()
        recency_weight = (idx + 1) / total_msgs

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

    summary_parts = []
    dominant_emotions = [k for k, v in emotion_tracker.items() if v > 0.5]
    if dominant_emotions:
        sorted_emotions = sorted(dominant_emotions, key=lambda x: emotion_tracker[x], reverse=True)[:2]
        summary_parts.append(f"Emotional state: {', '.join(sorted_emotions)}")

    if topic_tracker:
        sorted_topics = sorted(topic_tracker.items(), key=lambda x: x[1], reverse=True)[:2]
        topic_names = [name for name, _ in sorted_topics]
        summary_parts.append(f"Main concerns: {', '.join(topic_names)}")

    if summary_parts:
        return "[Earlier context: " + ". ".join(summary_parts) + "]"

    return None

def _clean_message(msg: dict) -> dict:
    return {
        "role": msg["role"],
        "content": " ".join(msg["content"].split())
    }

def get_optimized_history():
    history = session.get("history", [])
    if len(history) <= MAX_HISTORY_MESSAGES // 2:
        return history

    summary = create_conversation_summary(history)
    recent_messages = history[-(MAX_HISTORY_MESSAGES // 2):]

    if summary and len(summary) < 200:
        return [{"role": "system", "content": summary}] + recent_messages

    return recent_messages

# ══════════════════════════════════════════════════════════════════════════════
# 🎛️ FIXED: Adaptive Dynamic Response Control
# ══════════════════════════════════════════════════════════════════════════════

def get_dynamic_parameters():
    """
    FIXED: Proper adaptive token limits.
    - Light/happy moments: 200-250 tokens (short is fine)
    - Normal conversation: 350 tokens default
    - Anxious state: 400-500 tokens (space to breathe)
    - Deep depression: 500-600 tokens (more presence needed)
    Max cap: 700 (beyond this AI pads unnecessarily + slower response)
    """
    scores = session.get("scores", {"anxiety": 0, "depression": 0, "joy": 0})

    # ✅ FIXED: Better base values
    temperature = 0.75
    max_tokens = 350

    anxiety_level = scores["anxiety"]
    depression_level = scores["depression"]
    joy_level = scores["joy"]

    # ✅ FIXED: Gradual curves with proper ranges
    if anxiety_level > 60:
        temperature = 0.55
        max_tokens = 500
    elif anxiety_level > 40:
        temperature = 0.62
        max_tokens = 420
    elif anxiety_level > 25:
        temperature = 0.68
        max_tokens = 380

    if depression_level > 60:
        max_tokens = 600
        temperature = max(0.6, temperature - 0.05)
    elif depression_level > 40:
        max_tokens = 480

    if joy_level > 50:
        temperature = min(0.78, temperature + 0.05)
        max_tokens = 230  # ✅ Happy/light = shorter is natural

    # ✅ FIXED: Safety bounds — 200 min, 700 max
    temperature = max(0.5, min(0.82, temperature))
    max_tokens = max(200, min(700, max_tokens))

    return {
        "temperature": round(temperature, 2),
        "max_tokens": max_tokens,
        "top_p": 0.9
    }

# ══════════════════════════════════════════════════════════════════════════════
# 🤖 FIXED: AI Response Handler — reasoning_effort removed
# ══════════════════════════════════════════════════════════════════════════════

def strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks from Qwen3 response before showing to user."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def get_ai_response(messages: list) -> dict:
    """
    FIXED:
    1. reasoning_effort NOT set — model thinks fully for better responses
    2. <think> blocks stripped before sending to user (hidden thinking)
    3. Adaptive token limits from get_dynamic_parameters()
    """
    try:
        params = get_dynamic_parameters()
        clean_messages = [_clean_message(msg) for msg in messages]

        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + clean_messages,
            temperature=params["temperature"],
            max_tokens=params["max_tokens"],
            top_p=params["top_p"],
        )

        raw_content = response.choices[0].message.content.strip()
        content = strip_thinking(raw_content)  # ✅ Hide thinking, keep clean answer
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
# 📊 Session Scoring System
# ══════════════════════════════════════════════════════════════════════════════

def update_session_scores(user_message: str):
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
# 🗄️ Session Size Management
# ══════════════════════════════════════════════════════════════════════════════

def _get_session_size() -> float:
    session_data = dict(session)
    return len(json.dumps(session_data).encode('utf-8')) / 1024

def _trim_session_if_needed():
    while _get_session_size() > MAX_SESSION_SIZE_KB:
        history = session.get("history", [])
        if len(history) <= 6:
            break
        session["history"] = history[-max(6, len(history) - 4):]
        session.modified = True
        logger.warning("Session trimmed due to size limit")


def initialize_session_state() -> None:
    session.setdefault("history", [])
    session.setdefault("scores", {"anxiety": 0, "depression": 0, "joy": 0})
    session.setdefault("msg_count", 0)
    session.setdefault("started_at", datetime.now().isoformat())
    session.setdefault("crisis_detected", False)


def reset_session_state() -> None:
    session.clear()
    initialize_session_state()
    session.modified = True


def get_json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return data


def sanitize_message_content(value: str, *, max_chars: int = MAX_USER_MESSAGE_CHARS) -> str:
    if not isinstance(value, str):
        return ""
    normalized = re.sub(r"\s+", " ", value).strip()
    return normalized[:max_chars]


def sanitize_history_messages(messages) -> list:
    if not isinstance(messages, list):
        return []

    cleaned_messages = []
    for raw_msg in messages[-MAX_LOAD_SESSION_MESSAGES:]:
        if not isinstance(raw_msg, dict):
            continue
        role = raw_msg.get("role")
        if role not in VALID_HISTORY_ROLES:
            continue
        content = sanitize_message_content(raw_msg.get("content", ""))
        if not content:
            continue
        cleaned_messages.append({"role": role, "content": content})

    return cleaned_messages[-MAX_HISTORY_MESSAGES:]

# ══════════════════════════════════════════════════════════════════════════════
# 🛣️ ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    initialize_session_state()
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
@rate_limit
def chat():
    initialize_session_state()
    data = get_json_body()
    if data is None:
        return jsonify({"error": "invalid_json"}), 400

    user_text = sanitize_message_content(data.get("message", ""))

    if not user_text:
        return jsonify({"error": "empty"}), 400

    # 🚨 CRISIS CHECK
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
    session["history"] = history[-MAX_HISTORY_MESSAGES:]
    session.modified = True

    optimized_history = get_optimized_history()

    # 🤖 GET AI RESPONSE
    ai_response = get_ai_response(optimized_history)
    reply = ai_response["content"]

    history.append({"role": "assistant", "content": reply})

    if len(history) > MAX_HISTORY_MESSAGES:
        history = history[-MAX_HISTORY_MESSAGES:]

    session["history"] = history
    session["msg_count"] = session.get("msg_count", 0) + 1

    # 📊 UPDATE SCORES
    update_session_scores(user_text)

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
    reset_session_state()
    return jsonify({"ok": True})


@app.route("/load_session", methods=["POST"])
def load_session():
    data = get_json_body()
    if data is None:
        return jsonify({"error": "invalid_json"}), 400

    messages = sanitize_history_messages(data.get("messages", []))
    reset_session_state()
    session["history"] = messages
    session["scores"] = {"anxiety": 0, "depression": 0, "joy": 0}
    session["msg_count"] = len(messages)
    session["crisis_detected"] = False
    session.modified = True
    _trim_session_if_needed()
    return jsonify({"ok": True})


@app.route("/health", methods=["GET"])
def health_check():
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
    debug_mode = DEBUG_MODE

    if not debug_mode and app.secret_key == DEFAULT_SECRET_KEY:
        logger.warning("⚠️  WARNING: Using default secret key in production!")

    logger.info(f"🚀 Starting Peacoo AI on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
