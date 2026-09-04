# config.py

# Symbols to trade
SYMBOLS = [
    "XAUUSDm",
    "USTECm",
    "BTCUSDm",
]

# Risk management
SL_PERCENT = 0.002   # 0.2%
TP_PERCENT = 0.004   # 0.4%

# Free AI provider settings
# Verified working backend: g4f with Gemini (works without a local API key).
G4F_PROVIDER_NAME = "Gemini"
G4F_MODEL = "gemini-2.0-flash"

# Legacy values kept for older diagnostics/test files.
GROQ_API_KEY = ""
GROQ_MODEL = "g4f-fallback"