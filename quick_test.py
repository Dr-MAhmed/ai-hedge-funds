import requests
from config import OPENROUTER_API_KEY, OPENROUTER_MODEL

print("Testing OpenRouter API Connection...")
print(f"Model: {OPENROUTER_MODEL}")
print()

response = requests.post(
    "https://openrouter.io/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": "Say one word: OK"}],
        "max_tokens": 10
    },
    timeout=15
)

print(f"Response Status: {response.status_code}")
print()

if response.status_code == 200:
    print("✅ SUCCESS! API is working!")
    data = response.json()
    if "choices" in data and len(data["choices"]) > 0:
        msg = data["choices"][0]["message"]["content"]
        print(f"AI Response: {msg}")
    print("\nYour bot should now work properly!")
    print("Run: uvicorn main:app --reload")
elif response.status_code == 401:
    print("❌ Authentication Error (401)")
    print("Your API key is invalid or expired")
    print("Get a new one at: https://openrouter.io/keys")
elif response.status_code == 404:
    print("❌ Model Not Found (404)")
    print("The model might not exist or have a typo")
    print("Try other models:")
    print("  - meta-llama/llama-3-8b-instruct")
    print("  - mistralai/mistral-7b-instruct")
else:
    print(f"❌ Error: {response.status_code}")
    print(f"Response: {response.text[:500]}")
