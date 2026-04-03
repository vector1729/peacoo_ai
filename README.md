# 🧠 Peacoo AI — Mental Health Companion

Web-based mental health chatbot powered by **Groq API (free)** + **Flask** + **Llama 3.3 70B**.

---

## 📁 Project Structure

```
peacoo-web/
├── app.py              ← Flask backend + Groq API
├── templates/
│   └── index.html      ← Full chat UI
├── requirements.txt
├── render.yaml         ← Render.com deploy config
└── README.md
```

---

## 🚀 Step 1 — Get Free Groq API Key

1. Go to **https://console.groq.com**
2. Sign up (free, no credit card)
3. Click **API Keys → Create API Key**
4. Copy the key (starts with `gsk_...`)

---

## 💻 Step 2 — Run Locally (to test)

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your API key
export GROQ_API_KEY="gsk_your_key_here"   # Windows: set GROQ_API_KEY=gsk_...
export SECRET_KEY="any-random-string"

# 4. Run
python app.py
```

Open **http://localhost:5000** in your browser.

---

## 🌐 Step 3 — Deploy on Render (free public URL)

### Option A — Using render.yaml (easiest)

1. Push this folder to a **GitHub repo** (can be private)
2. Go to **https://render.com** → Sign up free
3. Click **New → Web Service → Connect GitHub repo**
4. Render auto-detects `render.yaml`
5. Add environment variable:
   - Key: `GROQ_API_KEY`
   - Value: your key from Step 1
6. Click **Deploy**
7. In ~2 minutes you get a URL like `https://peacoo-ai.onrender.com`

### Option B — Manual setup on Render

| Setting | Value |
|---------|-------|
| Environment | Python |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2` |

Add env vars: `GROQ_API_KEY` + `SECRET_KEY` (any random string)

---

## ⚠️ Important Notes

- **Free Render tier** spins down after 15 min inactivity — first load may take ~30s
- **Groq free tier** allows ~30 requests/min — enough for normal use
- **Crisis detection** never hits the API — always instant, local
- Session history is stored server-side in Flask session (resets on new visit)

---

## 🔧 Customise

### Change AI model
In `app.py`, line:
```python
MODEL = "llama-3.3-70b-versatile"
```
Options (all free on Groq):
- `llama-3.3-70b-versatile` — best quality (default)
- `llama-3.1-8b-instant` — faster, lighter
- `gemma2-9b-it` — Google's model, good for empathy

### Change bot personality
Edit `SYSTEM_PROMPT` in `app.py` — this is the "brain".

### Add your own crisis numbers
Edit `CRISIS_RESPONSE` in `app.py`.

---

## 🛡️ Safety Features

- ✅ Crisis keyword detection (runs before any API call)
- ✅ Therapist nudge every 8 messages when distress detected  
- ✅ Session memory (last 10 exchanges sent as context)
- ✅ Anxiety/depression/joy scoring (visual bars in header)
- ✅ Disclaimer shown to every user

---

Built with ❤️ by Anshu Chaudhary
