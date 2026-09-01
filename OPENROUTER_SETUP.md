# 🚀 OpenRouter Free AI Setup Guide

## What is OpenRouter?
**OpenRouter** provides **free AI models** with:
- ✅ $5 free credits on signup (covers hours of trading)
- ✅ No credit card required for free tier
- ✅ Multiple models (Claude, Llama, Mistral, Qwen)
- ✅ OpenAI-compatible API (easy to use)
- ✅ Supports both free and paid models
- ✅ 24/7 availability

---

## Step 1: Get Your Free OpenRouter API Key

1. **Go to OpenRouter:**
   - Visit: https://openrouter.io
   - Or directly to keys: https://openrouter.io/keys

2. **Sign Up (Free):**
   - Click "Sign In" or "Get Started"
   - Use email, Google, or GitHub
   - No credit card needed!
   - You get **$5 free credits** on signup

3. **Get API Key:**
   - Go to "Keys" page: https://openrouter.io/keys
   - Click "Create Key"
   - Copy your key (starts with `sk_`)
   - **Keep it safe** (don't share in public repos)

---

## Step 2: Add API Key to Bot

1. **Open** `config.py` in your project:
   ```
   c:\Users\Muhammad Ahmed\Desktop\ai hedge funds\config.py
   ```

2. **Find this line:**
   ```python
   OPENROUTER_API_KEY = "sk_your_openrouter_api_key_here"
   ```

3. **Replace with your actual key:**
   ```python
   OPENROUTER_API_KEY = "sk_xxxxxxxxxxxxxxxxxxxxxxxx"
   ```

4. **Save the file**

---

## Step 3: Verify Setup

The bot is now configured to use OpenRouter! Here's what changed:

### In `config.py`:
```python
OPENROUTER_API_KEY = "sk_your_api_key"
OPENROUTER_MODEL = "meta-llama/llama-2-70b-chat:free"  # Free model
```

### In `ai_brain.py`:
- API endpoint: `https://openrouter.io/api/v1/chat/completions`
- Model: Llama 2 70B (free tier)
- Temperature: 0.1 (consistent trading decisions)
- Supports multiple free models

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

## Available OpenRouter Free Models

Free tier models available:

| Model | Speed | Quality | Free? | Best For |
|-------|-------|---------|-------|----------|
| **meta-llama/llama-2-70b-chat:free** | ⚡⚡ Fast | ⭐⭐⭐⭐ Good | ✅ | **Trading (default)** |
| mistralai/mistral-7b-instruct:free | ⚡⚡⚡ Very Fast | ⭐⭐⭐ | ✅ | Quick analysis |
| meta-llama/llama-3-8b-instruct:free | ⚡⚡⚡ Very Fast | ⭐⭐⭐ | ✅ | Speed focused |
| google/flan-t5-xl:free | ⚡⚡⚡ Ultra Fast | ⭐⭐ Basic | ✅ | Minimal resources |

### To use a different free model, edit `config.py`:

```python
# Very fast option
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct:free"

# Better quality but slower
OPENROUTER_MODEL = "meta-llama/llama-2-70b-chat:free"

# Ultra fast for testing
OPENROUTER_MODEL = "google/flan-t5-xl:free"
```

---

## Free Tier Limits & Pricing

### Free Credits:
- **Signup bonus:** $5 free
- **Typical usage:** ~100-200 trades on $5
- **Renewal:** No auto-renewal, buy as needed

### Pricing Examples (per 1M tokens):
- Llama 2 70B: $0.70 input, $0.90 output
- Mistral 7B: Very cheap
- Cost for trading: Minimal (~$0.01-0.05 per analysis)

### Rate Limits:
- Requests: Generous for trading bot
- No strict limits on free tier
- Upgrade if you exceed limits

---

## Advanced: Paid Models (Optional)

OpenRouter also supports premium models:
- Claude 3.5 Sonnet (best quality)
- GPT-4 Turbo (powerful)
- Llama 2 (more options)

Simply change `OPENROUTER_MODEL` to use them!

---

## Troubleshooting

### Error: "Invalid API key"
- ✅ Make sure key starts with `sk_`
- ✅ Check for extra spaces in config.py
- ✅ Generate new key at https://openrouter.io/keys
- ✅ Copy exact key from OpenRouter dashboard

### Error: "Out of credits"
- ✅ Add payment method or use free credits
- ✅ OpenRouter shows credit usage in dashboard
- ✅ Choose cheaper free model (Mistral 7B)

### Error: "Rate limit exceeded"
- ✅ Increase trading interval (30s → 1hr in UI)
- ✅ Use faster model to complete quicker
- ✅ Upgrade to paid tier for higher limits

### Error: "OpenRouter API request failed"
- ✅ Check internet connection
- ✅ Verify API key is valid
- ✅ Check OpenRouter status: https://status.openrouter.io

---

## Benefits of OpenRouter

| Feature | OpenRouter | Groq | Others |
|---------|-----------|------|--------|
| **Free Tier** | $5 credits | Limited | Very limited |
| **No Credit Card** | ✅ | ✅ | ❌ Most need CC |
| **Model Variety** | ✅ 50+ | ❌ Few | ✅ Many |
| **Claude Support** | ✅ | ❌ | ✅ Expensive |
| **Trading Bot** | ✅ Good | ✅ Great | ✅ Works |
| **Upgrade Path** | ✅ Easy | ✅ Easy | Varies |

---

## Next Steps

1. ✅ Get free API key from OpenRouter
2. ✅ Add key to `config.py`
3. ✅ Choose your favorite free model
4. ✅ Run bot with `uvicorn`
5. ✅ Open http://localhost:8000
6. ✅ Click "Initialize Engine"
7. ✅ Watch AI trade in real-time!

Your bot is **now using FREE AI**! 🎉

---

## Support

**OpenRouter Docs:** https://openrouter.io/docs  
**API Reference:** https://openrouter.io/api/v1  
**Status Page:** https://status.openrouter.io  
**Discord:** https://discord.gg/openrouter

---

## Quick Model Recommendations

- **Best Free (balanced):** `meta-llama/llama-2-70b-chat:free`
- **Fastest Free:** `mistralai/mistral-7b-instruct:free`
- **Budget:** `google/flan-t5-xl:free`
- **Best Paid:** `claude-3-5-sonnet` (requires credits)
