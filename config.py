import os
from pathlib import Path
from dotenv import load_dotenv
import MetaTrader5 as mt5

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
MEMORY_FILE = BASE_DIR / "memory.json"
RULES_FILE = BASE_DIR / "new_rules.json"

DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_BASE: str = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

USE_PUTER: bool = os.getenv("USE_PUTER", "false").lower() == "true"
PUTER_AUTH_TOKEN: str = os.getenv("PUTER_AUTH_TOKEN", "")
PUTER_MODEL: str = os.getenv("PUTER_MODEL", "deepseek/deepseek-chat-v3.1")

USE_GROQ: bool = os.getenv("USE_GROQ", "false").lower() == "true"
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-4-scout-17b-16e-instruct")

MT5_LOGIN: int = int(os.getenv("MT5_LOGIN", "0"))
MT5_PASSWORD: str = os.getenv("MT5_PASSWORD", "")
MT5_SERVER: str = os.getenv("MT5_SERVER", "Exness-MT5Trial7")
MT5_PATH: str | None = os.getenv("MT5_PATH") or None

DEFAULT_RISK_PERCENT: float = float(os.getenv("DEFAULT_RISK_PERCENT", "1.0"))
SCAN_INTERVAL_SECONDS: int = int(os.getenv("SCAN_INTERVAL_SECONDS", "30"))
CONFIDENCE_THRESHOLD: int = int(os.getenv("CONFIDENCE_THRESHOLD", "65"))

SYMBOLS: list[str] = [
    s.strip()
    for s in os.getenv("SYMBOLS", "EURUSDm,GBPUSDm,USDJPYm").split(",")
    if s.strip()
]

TIMEFRAMES: list = [mt5.TIMEFRAME_H1, mt5.TIMEFRAME_D1]

EMA_PERIOD: int = 200
RSI_PERIOD: int = 14
ATR_PERIOD: int = 14
VOL_MA_PERIOD: int = 20

AUDIT_TRADE_THRESHOLD: int = int(os.getenv("AUDIT_TRADE_THRESHOLD", "10"))
AUDIT_COOLDOWN_HOURS: int = int(os.getenv("AUDIT_COOLDOWN_HOURS", "12"))
