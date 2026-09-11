import json
from datetime import datetime
from config import MEMORY_FILE
import MetaTrader5 as mt5


def _load() -> list[dict]:
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def _save(data: list[dict]) -> None:
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def append_trade_memory(record: dict) -> None:
    data = _load()
    record.setdefault("created_at", datetime.now().isoformat())
    record.setdefault("status", "CONFIRMED")
    data.append(record)
    _save(data)
    print(f"[MEMORY] Recorded trade {record.get('ticket', 'N/A')} for {record.get('symbol', 'N/A')}")


def load_trade_memory() -> list[dict]:
    return _load()


def reconcile_closed_trades() -> int:
    data = _load()
    reconciled_count = 0

    for i, rec in enumerate(data):
        if rec.get("status") != "CONFIRMED":
            continue
        if rec.get("exit_deal"):
            continue

        ticket = rec.get("ticket") or rec.get("order")
        if not ticket:
            continue

        try:
            deals = mt5.history_deals_get(
                position=0,
                group=f"*{rec.get('symbol', '')}*",
            )
            if deals is None or len(deals) == 0:
                continue

            for deal in deals:
                if deal.position_id != ticket:
                    continue
                if deal.entry != mt5.DEAL_ENTRY_OUT:
                    continue

                profit = deal.profit
                if profit > 0:
                    outcome = "WIN"
                elif profit < 0:
                    outcome = "LOSS"
                else:
                    outcome = "BREAKEVEN"

                data[i]["exit_deal"] = deal.ticket
                data[i]["exit_price"] = deal.price
                data[i]["exit_time"] = datetime.fromtimestamp(deal.time).isoformat()
                data[i]["realized_pnl"] = profit
                data[i]["outcome"] = outcome
                data[i]["status"] = "CLOSED"
                reconciled_count += 1
                print(
                    f"[MEMORY] Reconciled deal #{deal.ticket} | "
                    f"{rec['symbol']} {rec.get('side','?')} | P/L: {profit:.2f} | {outcome}"
                )
                break

        except Exception as e:
            print(f"[MEMORY] Error reconciling ticket {ticket}: {e}")

    if reconciled_count > 0:
        _save(data)

    return reconciled_count
