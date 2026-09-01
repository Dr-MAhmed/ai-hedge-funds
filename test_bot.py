#!/usr/bin/env python3
"""
Diagnostic script to test bot components.
"""

import json
import requests
import config

print("=" * 60)
print("AI HEDGE FUND BOT - DIAGNOSTIC TEST")
print("=" * 60)

# Test 1: Check API Key Format
print("\n[1] Checking OpenRouter API Key...")
api_key = config.OPENROUTER_API_KEY
print(f"    API Key: {api_key[:20]}...{api_key[-10:]}")

if api_key.startswith("ssk-"):
    print("    ❌ ERROR: API key has extra 's' at the beginning!")
    print("    ❌ Should start with 'sk-or-v1-' not 'ssk-or-v1-'")
    print("    👉 SOLUTION: Remove the first 's' from your API key")
elif api_key.startswith("sk_your"):
    print("    ❌ ERROR: API key not set!")
    print("    👉 SOLUTION: Add your real OpenRouter API key")
elif api_key.startswith("sk-or-v1"):
    print("    ✅ API key format looks correct")
else:
    print("    ⚠️  API key format unexpected, may still work")

# Test 2: Check Model
print("\n[2] Checking Model...")
model = config.OPENROUTER_MODEL
print(f"    Model: {model}")
if ":free" in model:
    print("    ✅ Using free model")
else:
    print("    ⚠️  May incur charges if not free model")

# Test 3: Test AI Brain
print("\n[3] Testing AI Brain API Connection...")

system_prompt = """You are a trading bot. Respond with JSON only:
{
    "signal": "BUY",
    "confidence_score": 75,
    "logic": "Test response."
}
"""

test_payload = {
    "model": model,
    "messages": [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": "Test message",
        },
    ],
    "temperature": 0.1,
    "max_tokens": 500,
}

headers = {
    "Authorization": f"Bearer {api_key}",
    "HTTP-Referer": "http://localhost:8000",
    "X-Title": "AI Hedge Fund Bot Test",
    "Content-Type": "application/json",
}

try:
    response = requests.post(
        "https://openrouter.io/api/v1/chat/completions",
        headers=headers,
        json=test_payload,
        timeout=10,
    )
    
    print(f"    Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("    ✅ API Connection Successful!")
        data = response.json()
        if "choices" in data and len(data["choices"]) > 0:
            print("    ✅ Response received")
            content = data["choices"][0]["message"]["content"]
            print(f"    Response: {content[:100]}...")
        else:
            print("    ⚠️  Unexpected response format")
            print(f"    Response: {json.dumps(data, indent=2)[:200]}")
    elif response.status_code == 401:
        print("    ❌ Authentication Failed (401)")
        print("    ❌ API key is invalid or has wrong format")
        print(f"    Response: {response.text[:200]}")
    elif response.status_code == 429:
        print("    ❌ Rate Limited (429)")
        print("    👉 Try again in a few moments or upgrade plan")
    else:
        print(f"    ❌ API Error: {response.status_code}")
        print(f"    Response: {response.text[:200]}")
        
except requests.exceptions.Timeout:
    print("    ❌ Request Timeout - Check internet connection")
except requests.exceptions.ConnectionError:
    print("    ❌ Connection Error - Check internet")
except Exception as e:
    print(f"    ❌ Error: {str(e)}")

# Test 4: Check Symbols
print("\n[4] Checking Trading Symbols...")
symbols = config.SYMBOLS
print(f"    Symbols: {symbols}")
if len(symbols) > 0:
    print(f"    ✅ {len(symbols)} symbols configured")
else:
    print("    ❌ No symbols configured")

# Test 5: Summary
print("\n" + "=" * 60)
print("ISSUES FOUND:")
print("=" * 60)

issues = []

if api_key.startswith("ssk-"):
    issues.append("❌ API key has extra 's' - REMOVE IT!")
elif api_key.startswith("sk_your"):
    issues.append("❌ API key not set - ADD YOUR REAL KEY!")

if len(issues) == 0:
    print("✅ No issues found - Bot should work!")
else:
    print("\n".join(issues))

print("\n" + "=" * 60)
print("NEXT STEPS:")
print("=" * 60)
print("1. Fix your API key (remove extra 's')")
print("2. Run the bot with: uvicorn main:app --reload")
print("3. Check this script output in terminal for errors")
print("=" * 60)
