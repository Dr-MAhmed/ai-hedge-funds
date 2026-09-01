# execution.py

import MetaTrader5 as mt5

from config import SL_PERCENT, TP_PERCENT


def execute_trade(symbol, signal):
    """
    Execute a BUY or SELL market order on MetaTrader 5.

    Args:
        symbol (str): MT5 symbol, e.g. "XAUUSDm"
        signal (str): "BUY" or "SELL"

    Returns:
        dict: Trade execution result.
    """

    # Validate signal
    if signal not in {"BUY", "SELL"}:
        raise ValueError(
            f"Invalid signal: {signal}. Expected BUY or SELL."
        )

    # Make sure the symbol is available
    if not mt5.symbol_select(symbol, True):
        raise RuntimeError(
            f"Failed to select symbol {symbol}: {mt5.last_error()}"
        )

    # Get symbol information
    symbol_info = mt5.symbol_info(symbol)

    if symbol_info is None:
        raise RuntimeError(
            f"Failed to get symbol information for {symbol}: "
            f"{mt5.last_error()}"
        )

    # CRITICAL:
    # Get the correct number of decimal places for this asset.
    digits = symbol_info.digits

    # Get current market price
    tick = mt5.symbol_info_tick(symbol)

    if tick is None:
        raise RuntimeError(
            f"Failed to get current price for {symbol}: "
            f"{mt5.last_error()}"
        )

    # Determine order type and entry price
    if signal == "BUY":
        order_type = mt5.ORDER_TYPE_BUY
        price = tick.ask

        # BUY:
        # SL below entry
        # TP above entry
        stop_loss = price * (1 - SL_PERCENT)
        take_profit = price * (1 + TP_PERCENT)

    else:
        order_type = mt5.ORDER_TYPE_SELL
        price = tick.bid

        # SELL:
        # SL above entry
        # TP below entry
        stop_loss = price * (1 + SL_PERCENT)
        take_profit = price * (1 - TP_PERCENT)

    # CRITICAL:
    # Round SL and TP according to the symbol's actual digits.
    stop_loss = round(stop_loss, digits)
    take_profit = round(take_profit, digits)
    price = round(price, digits)

    # Default lot size.
    # This can later be replaced with AI/risk-based position sizing.
    volume = 0.01

    # Build MT5 trade request
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "sl": stop_loss,
        "tp": take_profit,
        "deviation": 20,
        "magic": 20260901,
        "comment": "AI Hedge Fund Bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    # Send order
    result = mt5.order_send(request)

    if result is None:
        raise RuntimeError(
            f"MT5 order_send() failed: {mt5.last_error()}"
        )

    # Return useful execution information
    return {
        "retcode": result.retcode,
        "order": result.order,
        "deal": result.deal,
        "symbol": symbol,
        "signal": signal,
        "volume": volume,
        "price": price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "comment": result.comment,
        "raw_result": result,
    }