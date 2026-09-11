import asyncio
import json
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import config
import data_engine
import ai_brain
import execution
import memory_store
import auditor


class BotState:
    def __init__(self):
        self.is_running = False
        self.interval = config.SCAN_INTERVAL_SECONDS
        self.risk_percent = config.DEFAULT_RISK_PERCENT
        self.equity = 0.0
        self.balance = 0.0
        self.last_logic = ""
        self.last_confidence = 0
        self.last_signal = "HOLD"
        self.last_entry_price = None
        self.last_stop_loss = None
        self.last_take_profit = None
        self.trade_history = []
        self.open_positions = []
        self.learned_rules = []
        self.last_audit_at = None
        self.loop_count = 0


bot_state = BotState()


class ControlRequest(BaseModel):
    action: str = ""
    interval: int | None = None
    risk_percent: float | None = None


class CloseRequest(BaseModel):
    ticket: int


class AuditRequest(BaseModel):
    force: bool = False


@asynccontextmanager
async def lifespan(application: FastAPI):
    print("[SYSTEM] Starting AI Hedge Fund Engine...")
    mt5_ok = data_engine.initialize_mt5()
    if not mt5_ok:
        print("[SYSTEM] CRITICAL: MT5 connection failed. Dashboard available but trading disabled.")

    memory_store.reconcile_closed_trades()
    doc = auditor.load_rules_document()
    bot_state.learned_rules = doc.get("rules", [])
    bot_state.last_audit_at = doc.get("last_audit_at")
    print(f"[SYSTEM] Loaded {len(bot_state.learned_rules)} active rules")

    if doc.get("last_audit_at"):
        last = datetime.fromisoformat(doc["last_audit_at"])
        print(f"[SYSTEM] Last audit: {last}")

    task = asyncio.create_task(trading_loop())
    yield
    task.cancel()


app = FastAPI(title="AI Hedge Fund", lifespan=lifespan)
templates = Jinja2Templates(directory=str(config.BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/api/status")
async def api_status():
    try:
        acct = __import__("MetaTrader5", fromlist=["account_info"]).account_info()
        if acct:
            bot_state.equity = acct.equity
            bot_state.balance = acct.balance
    except Exception:
        pass

    bot_state.open_positions = execution.get_open_positions()
    memory = memory_store.load_trade_memory()
    confirmed = [t for t in memory if t.get("status") in ("CONFIRMED", "CLOSED")]
    bot_state.trade_history = confirmed[-100:]

    doc = auditor.load_rules_document()
    bot_state.learned_rules = doc.get("rules", [])
    bot_state.last_audit_at = doc.get("last_audit_at")

    return JSONResponse({
        "is_running": bot_state.is_running,
        "interval": bot_state.interval,
        "risk_percent": bot_state.risk_percent,
        "equity": bot_state.equity,
        "balance": bot_state.balance,
        "last_signal": bot_state.last_signal,
        "last_confidence": bot_state.last_confidence,
        "last_logic": bot_state.last_logic,
        "last_entry_price": bot_state.last_entry_price,
        "last_stop_loss": bot_state.last_stop_loss,
        "last_take_profit": bot_state.last_take_profit,
        "open_positions": bot_state.open_positions,
        "trade_history": bot_state.trade_history[-50:],
        "learned_rules": bot_state.learned_rules,
        "last_audit_at": bot_state.last_audit_at,
        "loop_count": bot_state.loop_count,
    })


@app.post("/api/control")
async def api_control(req: ControlRequest):
    if req.action == "start":
        bot_state.is_running = True
        print("[SYSTEM] Engine STARTED")
    elif req.action == "stop":
        bot_state.is_running = False
        print("[SYSTEM] Engine STOPPED")

    if req.interval is not None and req.interval > 0:
        bot_state.interval = req.interval
    if req.risk_percent is not None and req.risk_percent > 0:
        bot_state.risk_percent = req.risk_percent

    return JSONResponse({"ok": True, "is_running": bot_state.is_running})


@app.post("/api/close")
async def api_close(req: CloseRequest):
    result = execution.close_position(req.ticket)
    return JSONResponse(result)


@app.post("/api/audit")
async def api_audit(req: AuditRequest):
    result = auditor.run_audit(force=req.force)
    return JSONResponse(result)


@app.get("/api/rules")
async def api_rules():
    doc = auditor.load_rules_document()
    return JSONResponse(doc)


async def trading_loop():
    while True:
        try:
            if not bot_state.is_running:
                await asyncio.sleep(2)
                continue

            bot_state.loop_count += 1
            print(f"\n[SYSTEM] === Scan Cycle #{bot_state.loop_count} ===")

            for symbol in config.SYMBOLS:
                try:
                    print(f"[SYSTEM] Analyzing {symbol}...")
                    market_data = data_engine.fetch_multi_timeframe_data(symbol)
                    if not market_data:
                        print(f"[SYSTEM] No data for {symbol}, skipping")
                        continue

                    correlated = data_engine.fetch_correlated_asset_prices(
                        symbol, config.SYMBOLS
                    )
                    market_data["correlated_prices"] = correlated

                    decision = ai_brain.get_ai_decision(market_data, symbol)
                    signal = decision.get("signal", "HOLD")
                    confidence = decision.get("confidence_score", 0)
                    sl = decision.get("stop_loss", 0)
                    tp = decision.get("take_profit", 0)
                    logic = decision.get("logic", "")

                    bot_state.last_signal = signal
                    bot_state.last_confidence = confidence
                    bot_state.last_logic = logic
                    bot_state.last_entry_price = market_data.get("ask")
                    bot_state.last_stop_loss = sl
                    bot_state.last_take_profit = tp

                    if signal in ("BUY", "SELL"):
                        existing = execution.get_open_positions(symbol)

                        same_dir = [
                            p for p in existing
                            if (signal == "BUY" and p["side"] == "BUY")
                            or (signal == "SELL" and p["side"] == "SELL")
                        ]
                        if same_dir:
                            print(
                                f"[DUPLICATE PREVENTED] Already {signal} {symbol}, skipping"
                            )
                            continue

                        opp_dir = [
                            p for p in existing
                            if (signal == "BUY" and p["side"] == "SELL")
                            or (signal == "SELL" and p["side"] == "BUY")
                        ]
                        for pos in opp_dir:
                            print(
                                f"[REVERSAL] Closing {pos['side']} {symbol} "
                                f"(ticket {pos['ticket']}) before {signal}"
                            )
                            execution.close_position(pos["ticket"])

                        try:
                            trade_result = execution.execute_trade(
                                symbol=symbol,
                                signal=signal,
                                stop_loss=sl,
                                take_profit=tp,
                                risk_percent=bot_state.risk_percent,
                            )

                            trade_record = {
                                "ticket": trade_result["deal"],
                                "order": trade_result["order"],
                                "symbol": symbol,
                                "side": signal,
                                "entry_price": trade_result["price"],
                                "sl": sl,
                                "tp": tp,
                                "volume": trade_result["volume"],
                                "risk_percent": bot_state.risk_percent,
                                "market_context": {
                                    "h1_data": market_data.get("h1_data"),
                                    "daily_data": market_data.get("daily_data"),
                                    "correlated_prices": correlated,
                                },
                            }
                            memory_store.append_trade_memory(trade_record)
                            print(
                                f"[TRADE] {signal} {symbol} executed successfully"
                            )

                        except Exception as e:
                            print(f"[TRADE] Execution error for {symbol}: {e}")

                    else:
                        print(f"[AI] {symbol}: HOLD (confidence: {confidence})")

                except Exception as e:
                    print(f"[SYSTEM] Error analyzing {symbol}: {e}")

            reconciled = memory_store.reconcile_closed_trades()
            if reconciled > 0:
                print(f"[SYSTEM] Reconciled {reconciled} trades after scan")

            doc = auditor.load_rules_document()
            needs_audit = False
            if not doc.get("last_audit_at"):
                needs_audit = True
            else:
                last = datetime.fromisoformat(doc["last_audit_at"])
                hours = (datetime.now() - last).total_seconds() / 3600
                if hours >= config.AUDIT_COOLDOWN_HOURS:
                    needs_audit = True

            if needs_audit:
                print("[AUDITOR] Audit triggered after scan cycle")
                audit_result = auditor.run_audit()
                print(f"[AUDITOR] Result: {audit_result.get('status', 'unknown')}")

            print(f"[SYSTEM] Scan complete. Sleeping {bot_state.interval}s...")
            await asyncio.sleep(bot_state.interval)

        except asyncio.CancelledError:
            print("[SYSTEM] Trading loop cancelled")
            break
        except Exception as e:
            print(f"[SYSTEM] Trading loop error: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
