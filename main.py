# main.py

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import MetaTrader5 as mt5
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

import config
from data_engine import fetch_multi_timeframe_data
from ai_brain import get_ai_decision
from execution import execute_trade


# ============================================================
# LIFESPAN HANDLER
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    Handles startup and shutdown events.
    """
    # Startup
    if not mt5.initialize():
        print(
            "[ERROR] MetaTrader 5 initialization failed:",
            mt5.last_error(),
        )
    else:
        print("[MT5] MetaTrader 5 initialized successfully.")

    asyncio.create_task(trading_loop())

    yield

    # Shutdown
    bot_state["is_running"] = False
    mt5.shutdown()
    print("[MT5] MetaTrader 5 connection closed.")


app = FastAPI(
    title="AI Hedge Fund Bot",
    description="Automated AI trading bot using DeepSeek and MetaTrader 5",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# GLOBAL BOT STATE
# ============================================================

bot_state = {
    "is_running": False,
    "interval": 30,
    "equity": 0.0,
    "last_logic": "",
    "last_confidence": 0,
    "trade_history": [],
}


# ============================================================
# REQUEST MODEL
# ============================================================

class ControlRequest(BaseModel):
    action: str | None = None
    interval: int | None = None


# ============================================================
# BOT CONTROL
# ============================================================

@app.get("/")
async def serve_frontend():
    """
    Serve the AI Hedge Fund dashboard HTML.
    """
    html_path = Path(__file__).parent / "templates" / "index.html"
    return FileResponse(html_path, media_type="text/html")


@app.get("/favicon.ico")
async def favicon():
    """
    Serve a simple favicon response to prevent 404 errors.
    """
    return {"status": "ok"}


@app.post("/api/control")
async def control_bot(request: ControlRequest):
    """
    Start/stop the bot and optionally update the trading interval.

    Example:
    {
        "action": "start",
        "interval": 30
    }

    Or:

    {
        "action": "stop"
    }
    """

    if request.action is not None:
        action = request.action.lower()

        if action == "start":
            bot_state["is_running"] = True

        elif action == "stop":
            bot_state["is_running"] = False

        else:
            return {
                "success": False,
                "message": "Invalid action. Use 'start' or 'stop'.",
            }

    if request.interval is not None:
        if request.interval < 1:
            return {
                "success": False,
                "message": "Interval must be at least 1 second.",
            }

        bot_state["interval"] = request.interval

    return {
        "success": True,
        "message": "Bot state updated.",
        "state": bot_state,
    }


# ============================================================
# BOT STATUS
# ============================================================

@app.get("/api/status")
async def get_status():
    """
    Return the current bot state.
    """

    return bot_state


# ============================================================
# TRADING LOOP
# ============================================================

async def trading_loop():
    """
    Main asynchronous trading loop.

    When the bot is running:
        1. Loop through all configured symbols.
        2. Fetch D1/H1 market data.
        3. Ask DeepSeek for a trading decision.
        4. Execute BUY/SELL decisions.
        5. Record executed trades.
        6. Wait for the configured interval.
    """

    while True:

        # ----------------------------------------------------
        # Only trade when the bot is running
        # ----------------------------------------------------
        if not bot_state["is_running"]:
            await asyncio.sleep(1)
            continue

        # ----------------------------------------------------
        # Loop through configured symbols sequentially
        # ----------------------------------------------------
        for symbol in config.SYMBOLS:

            # Allow the bot to stop during a symbol cycle
            if not bot_state["is_running"]:
                break

            try:
                print(f"[BOT] Processing {symbol}")

                # ------------------------------------------------
                # 1. Fetch market data
                # ------------------------------------------------
                market_data = await asyncio.to_thread(
                    fetch_multi_timeframe_data,
                    symbol,
                )

                # Update equity
                bot_state["equity"] = market_data["equity"]

                # ------------------------------------------------
                # 2. Get AI decision
                # ------------------------------------------------
                decision = await asyncio.to_thread(
                    get_ai_decision,
                    market_data,
                    symbol,
                )

                signal = decision["signal"]
                confidence = decision["confidence_score"]
                logic = decision["logic"]

                # Update latest AI information
                bot_state["last_logic"] = logic
                bot_state["last_confidence"] = confidence

                print(
                    f"[AI] {symbol} | "
                    f"{signal} | "
                    f"Confidence: {confidence}"
                )

                # ------------------------------------------------
                # 3. Execute BUY/SELL
                # ------------------------------------------------
                if signal in {"BUY", "SELL"}:

                    result = await asyncio.to_thread(
                        execute_trade,
                        symbol,
                        signal,
                    )

                    # ------------------------------------------------
                    # 4. Record executed trade
                    # ------------------------------------------------
                    trade = {
                        "time": datetime.now(
                            timezone.utc
                        ).isoformat(),

                        "asset": symbol,

                        "signal": signal,

                        "logic": logic,
                    }

                    bot_state["trade_history"].append(trade)

                    print(
                        f"[TRADE] Executed {signal} on {symbol}"
                    )

                else:
                    print(
                        f"[AI] {symbol}: HOLD - no trade executed."
                    )

            except Exception as e:
                print(
                    f"[ERROR] {symbol}: {str(e)}"
                )
                import traceback
                traceback.print_exc()

        # ----------------------------------------------------
        # Respect configured trading interval
        # ----------------------------------------------------
        await asyncio.sleep(
            bot_state["interval"]
        )