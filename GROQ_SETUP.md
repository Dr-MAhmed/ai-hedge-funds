# 🚀 Groq Free AI Setup Guide

## What is Groq?
**Groq** provides **free AI models** with:
- ✅ No credit card required
- ✅ Generous free tier (perfect for trading bots)
- ✅ **Very fast inference** (critical for real-time trading)
- ✅ Multiple models: Llama 3.1, Mixtral
- ✅ 24/7 availability

---

## Step 1: Get Your Free Groq API Key

1. **Go to Groq Console:**
   - Visit: https://console.groq.com/keys
   - Or start at: https://groq.com

2. **Sign Up (Free):**
   - Click "Sign Up"
   - Enter email and password
   - Verify email
   - Accept terms

3. **Get API Key:**
   - Go to "API Keys" section
   - Click "Create New API Key"
   - Copy your key (starts with `gsk_`)
   - **Keep it safe** (don't share in git repos)

---

## Step 2: Add API Key to Bot

1. **Open** `config.py` in your project:
   ```
   c:\Users\Muhammad Ahmed\Desktop\ai hedge funds\config.py
   ```

2. **Replace this line:**
   ```python
   GROQ_API_KEY = "gsk_your_free_api_key_here"
   ```

   **With your actual key:**
   ```python
   GROQ_API_KEY = "gsk_xxxxxxxxxxxxxxxxxxxx"
   ```

3. **Save the file**

---

## Step 3: Verify Setup

The bot is already configured to use Groq! Here's what changed:

### In `config.py`:
```python
GROQ_API_KEY = "gsk_your_api_key"
GROQ_MODEL = "llama-3.1-8b-instant"  # Fast, free model
```

### In `ai_brain.py`:
- API endpoint: `https://api.groq.com/openai/v1/chat/completions`
- Model: LLama 3.1 8B (fastest free option)
- Temperature: 0.1 (consistent trading decisions)

---

## Step 4: Start Trading

1. **Make sure uvicorn is running:**
   ```bash
   cd "c:\Users\Muhammad Ahmed\Desktop\ai hedge funds"
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Open dashboard:**
   - http://localhost:8000

3. **Click "Initialize Engine"** to start trading

---

## Available Groq Models

Free tier includes:

| Model | Speed | Quality | Best For |
|-------|-------|---------|----------|
| **llama-3.1-8b-instant** | ⚡⚡⚡ Very Fast | ⭐⭐⭐⭐ | **Trading (default)** |
| llama-3.1-70b-versatile | ⚡⚡ Fast | ⭐⭐⭐⭐⭐ Excellent | Deep analysis |
| mixtral-8x7b-32768 | ⚡ Balanced | ⭐⭐⭐⭐ | Balanced |

**To change models**, edit `config.py`:
```python
GROQ_MODEL = "llama-3.1-70b-versatile"  # For deeper analysis
```

---

## Free Tier Limits

- **Requests per minute:** ~30 (plenty for 30s intervals)
- **Tokens:** Generous allocation
- **Cost:** $0
- **Upgrade:** Optional if you need more

---

## Troubleshooting

### Error: "Invalid API key"
- ✅ Make sure key starts with `gsk_`
- ✅ Check for extra spaces in config.py
- ✅ Generate new key at https://console.groq.com/keys

### Error: "Rate limit exceeded"
- ✅ Increase trading interval (30s → 1hr in UI)
- ✅ Groq gives higher limits for paid plans

### Error: "Groq API request failed"
- ✅ Check internet connection
- ✅ Verify API key is valid
- ✅ Check Groq status: https://status.groq.com

---

## Benefits of Groq

| Feature | Groq | Others |
|---------|------|--------|
| **Free Tier** | Yes, generous | Limited |
| **No Credit Card** | ✅ | ❌ Most need CC |
| **Speed** | ⚡ Fastest | Slower |
| **24/7 Bot Support** | Perfect | Rate limited |
| **Trading Use Case** | Optimized | Generic |

---

## Next Steps

1. ✅ Get API key from Groq console
2. ✅ Add key to `config.py`
3. ✅ Run bot with `uvicorn`
4. ✅ Open http://localhost:8000
5. ✅ Click "Initialize Engine"
6. ✅ Watch AI trade in real-time

Your bot is **now using free AI**! 🎉

---

## Support

**Groq Community:** https://discord.gg/groq  
**Groq Docs:** https://console.groq.com/docs  
**Status:** https://status.groq.com
