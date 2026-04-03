# 🤖 Peacoo AI — Mental Wellness Companion

> *A safe, judgment-free space to talk through whatever is on your mind.*

![Made with Python](https://img.shields.io/badge/Made%20with-Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Powered by Groq](https://img.shields.io/badge/Powered%20by-Groq-00A67E?style=for-the-badge)
![Flask](https://img.shields.io/badge/Backend-Flask-000000?style=for-the-badge&logo=flask)
![Made with ❤️](https://img.shields.io/badge/Made%20with-%E2%9D%A4%EF%B8%8F-red?style=for-the-badge)

---

## 🌐 Live Demo
👉 [https://peacoo-ai.onrender.com](https://peacoo-ai.onrender.com)

---

## 💚 What is Peacoo?

Peacoo is an AI-powered mental wellness chatbot that talks like a warm, caring friend — not a robot or a therapist. It listens without judgment, responds with empathy, and gently guides you through difficult emotions.

Built for people who just need someone (or something) to talk to.

---

## ✨ Features

- 🤖 **Friendly AI responses** — soft, informal, human-like tone
- 💬 **Chat history** — your past sessions saved locally
- 🫁 **Breathing exercise** — type `breathe` for guided box breathing
- 🌿 **Grounding exercise** — type `ground` for 5-4-3-2-1 technique
- 📓 **Journaling prompt** — type `journal` for a guided prompt
- 💬 **Motivational quote** — type `quote`
- 🚨 **Crisis detection** — instant helpline response, never goes to AI
- 📱 **Mobile friendly** — works on any device

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python + Flask |
| AI Model | Llama 3.3 70B via Groq API |
| Frontend | HTML + CSS + Vanilla JS |
| Hosting | Render.com |

---

## 🚀 Run Locally

**Step 1 — Clone the repo**
```bash
git clone https://github.com/vector1729/peacoo_ai.git
cd peacoo_ai
```

**Step 2 — Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 3 — Get free Groq API key**

Go to [console.groq.com](https://console.groq.com) → Sign up free → Create API Key

**Step 4 — Set environment variables**
```bash
# Mac/Linux
export GROQ_API_KEY="gsk_your_key_here"
export SECRET_KEY="any-random-string"

# Windows
set GROQ_API_KEY=gsk_your_key_here
set SECRET_KEY=any-random-string
```

**Step 5 — Run**
```bash
python app.py
```

Open **http://localhost:5000** 🎉

---

## 🌐 Deploy on Render (Free)

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Add environment variables:
   - `GROQ_API_KEY` → your Groq key
   - `SECRET_KEY` → any random string
5. Start command: `gunicorn app:app`
6. Deploy → get your public URL ✅

---

## 🆘 Crisis Helplines

If you or someone you know is in crisis:

| | Helpline | Number |
|--|---------|--------|
| 🇮🇳 | iCall India | 9152987821 |
| 🇮🇳 | Vandrevala Foundation | 1860-2662-345 *(24/7)* |
| 🌍 | International | [findahelpline.com](https://findahelpline.com) |

---

## ⚠️ Disclaimer

Peacoo is an AI companion and is **not** a substitute for professional mental health care. If you are experiencing a mental health crisis, please contact a licensed professional or the helplines listed above.

---

## 📁 Project Structure

```
peacoo_ai/
├── app.py              ← Flask backend + Groq API
├── templates/
│   └── index.html      ← Chat UI
├── requirements.txt
├── render.yaml
└── README.md
```

---

<div align="center">

Made with ❤️ by **Anshu Chaudhary**

</div>
