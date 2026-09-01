# config.py

# Symbols to trade
SYMBOLS = [
    "XAUUSDm",
    "EURUSDm",
    "GBPUSDm",
    "BTCUSDm",
]

# Risk management
SL_PERCENT = 0.002   # 0.2%
TP_PERCENT = 0.004   # 0.4%

# Groq API (Free tier - no credit card required)
# Get your free API key at: https://console.groq.com/keys
# 1. Sign up at https://console.groq.com
# 2. Go to API Keys section
# 3. Copy your API key below
GROQ_API_KEY = "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"

# Verified working model for this key: qwen/qwen3.8-27b
# Earlier models like llama-3.1-8b-instant returned 404 because they are not available on this account.
GROQ_MODEL = "qwen/qwen3.8-27b"