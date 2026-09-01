import requests
from config import GROQ_API_KEY, GROQ_MODEL

print("Testing Groq API Connection...")
print(f"API Key: {GROQ_API_KEY[:20]}...")
print(f"Model: {GROQ_MODEL}")
print()

if GROQ_API_KEY == "gsk_your_free_api_key_here":
    print("❌ ERROR: API key is still a placeholder!")
    print("Get a free key at: https://console.groq.com/keys")
    exit(1)

try:
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": "Say: SUCCESS"}],
            "max_tokens": 10
        },
        timeout=15
    )

    if response.status_code == 200:
        print("✅ SUCCESS! Groq API is working!")
        data = response.json()
        msg = data["choices"][0]["message"]["content"]
        print(f"AI Response: {msg}")
        print()
        print("Your bot is ready to trade!")
        print("Run: uvicorn main:app --reload")
    else:
        print(f"❌ Error {response.status_code}")
        print(f"Details: {response.text[:300]}")
        
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("Check your API key at: https://console.groq.com/keys")
