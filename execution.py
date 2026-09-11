import MetaTrader5 as mt5
import config


def calculate_position_size(
    symbol: str,
    stop_loss_price: float,
    risk_percent: float,
    equity: float,
) -> float:
    info = mt5.symbol_info(symbol)
    if not info:
        raise ValueError(f"Cannot get symbol info for {symbol}")

    price = info.ask
    monetary_risk = equity * (risk_percent / 100.0)

    sl_distance = abs(price - stop_loss_price)
    if sl_distance == 0:
        sl_distance = info.point * 100

    tick_value = info.trade_tick_value
    tick_size = info.trade_tick_size

    if tick_size == 0 or tick_value == 0:
        volume = info.volume_min
    else:
        risk_per_lot = (sl_distance / tick_size) * tick_value
        if risk_per_lot == 0:
            volume = info.volume_min
        else:
            volume = monetary_risk / risk_per_lot

    volume = max(volume, info.volume_min)
    volume = min(volume, info.volume_max)

    step = info.volume_step
    if step > 0:
        volume = round(volume / step) * step

    volume = round(volume, 2)
    return volume


def get_open_positions(symbol: str = None) -> list[dict]:
    if symbol:
        positions = mt5.positions_get(symbol=symbol)
    else:
        positions = mt5.positions_get()

    if positions is None:
        return []

    result = []
    for pos in positions:
        result.append({
            "ticket": pos.ticket,
            "symbol": pos.symbol,
            "side": "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL",
            "volume": pos.volume,
            "price_open": pos.price_open,
            "price_current": pos.price_current,
            "sl": pos.sl,
            "tp": pos.tp,
            "profit": pos.profit,
            "swap": pos.swap,
            "time": pos.time,
        })
    return result


def close_position(ticket: int) -> dict:
    position = mt5.positions_get(ticket=ticket)
    if not position:
        return {"success": False, "error": f"Position {ticket} not found"}

    pos = position[0]
    tick = mt5.symbol_info_tick(pos.symbol)
    if not tick:
        return {"success": False, "error": f"No tick data for {pos.symbol}"}

    if pos.type == mt5.ORDER_TYPE_BUY:
        order_type = mt5.ORDER_TYPE_SELL
        price = tick.bid
    else:
        order_type = mt5.ORDER_TYPE_BUY
        price = tick.ask

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": pos.symbol,
        "volume": pos.volume,
        "type": order_type,
        "position": ticket,
        "price": price,
        "deviation": 30,
        "magic": 999999,
        "comment": "AUDIT_CLOSE",
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result is None:
        return {"success": False, "error": f"order_send returned None: {mt5.last_error()}"}

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        return {"success": False, "error": f"Close failed: {result.comment} (code {result.retcode})"}

    print(f"[TRADE] Closed position {ticket} | {pos.symbol} | P/L: {pos.profit:.2f}")
    return {
        "success": True,
        "deal": result.deal,
        "order": result.order,
        "price": result.price,
        "volume": pos.volume,
        "symbol": pos.symbol,
    }


def execute_trade(
    symbol: str,
    signal: str,
    stop_loss: float,
    take_profit: float,
    risk_percent: float,
) -> dict:
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        raise ValueError(f"No tick data for {symbol}")

    acct = mt5.account_info()
    if not acct:
        raise ValueError("Cannot get account info")

    volume = calculate_position_size(symbol, stop_loss, risk_percent, acct.equity)
    print(f"[TRADE] Position sizing: {symbol} volume={volume} | risk={risk_percent}%")

    if signal == "BUY":
        order_type = mt5.ORDER_TYPE_BUY
        price = tick.ask
    else:
        order_type = mt5.ORDER_TYPE_SELL
        price = tick.bid

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "sl": stop_loss,
        "tp": take_profit,
        "deviation": 30,
        "magic": 999999,
        "comment": "AI_HEDGE",
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result is None:
        raise RuntimeError(f"order_send returned None: {mt5.last_error()}")

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        raise RuntimeError(
            f"Trade failed: {result.comment} (code {result.retcode})"
        )

    print(
        f"[TRADE] Executed {signal} {symbol} | Deal #{result.deal} | "
        f"Price: {result.price} | Volume: {volume} | SL: {stop_loss} | TP: {take_profit}"
    )

    return {
        "deal": result.deal,
        "order": result.order,
        "price": result.price,
        "volume": volume,
        "sl": stop_loss,
        "tp": take_profit,
        "symbol": symbol,
        "signal": signal,
    }
