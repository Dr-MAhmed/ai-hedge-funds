# data_engine.py

import MetaTrader5 as mt5
from config import SYMBOLS


def fetch_multi_timeframe_data(symbol):
    """
    Fetch market data for a symbol from MetaTrader 5.

    Returns:
        dict containing:
            - symbol
            - daily_data: Last 10 Daily candles as raw CSV text
            - hourly_data: Last 24 H1 candles as raw CSV text
            - equity: Current account equity
            - ask_price: Current ask price
    """

    # Make sure the symbol is available in MT5
    if not mt5.symbol_select(symbol, True):
        raise RuntimeError(f"Failed to select symbol: {symbol}")

    # -------------------------
    # Daily timeframe
    # -------------------------
    daily_rates = mt5.copy_rates_from_pos(
        symbol,
        mt5.TIMEFRAME_D1,
        0,
        10
    )

    if daily_rates is None or len(daily_rates) == 0:
        raise RuntimeError(
            f"Failed to fetch Daily data for {symbol}: {mt5.last_error()}"
        )

    # -------------------------
    # 1-Hour timeframe
    # -------------------------
    hourly_rates = mt5.copy_rates_from_pos(
        symbol,
        mt5.TIMEFRAME_H1,
        0,
        24
    )

    if hourly_rates is None or len(hourly_rates) == 0:
        raise RuntimeError(
            f"Failed to fetch H1 data for {symbol}: {mt5.last_error()}"
        )

    # Convert NumPy structured arrays to raw CSV text
    daily_columns = daily_rates.dtype.names
    hourly_columns = hourly_rates.dtype.names

    daily_csv = ",".join(daily_columns) + "\n"

    for row in daily_rates:
        daily_csv += ",".join(str(row[column]) for column in daily_columns)
        daily_csv += "\n"

    hourly_csv = ",".join(hourly_columns) + "\n"

    for row in hourly_rates:
        hourly_csv += ",".join(str(row[column]) for column in hourly_columns)
        hourly_csv += "\n"

    # -------------------------
    # Current market/account data
    # -------------------------
    account_info = mt5.account_info()

    if account_info is None:
        raise RuntimeError(
            f"Failed to retrieve account information: {mt5.last_error()}"
        )

    tick = mt5.symbol_info_tick(symbol)

    if tick is None:
        raise RuntimeError(
            f"Failed to retrieve tick data for {symbol}: {mt5.last_error()}"
        )

    return {
        "symbol": symbol,
        "daily_data": daily_csv,
        "hourly_data": hourly_csv,
        "equity": account_info.equity,
        "ask_price": tick.ask,
    }


if __name__ == "__main__":
    # Initialize MetaTrader 5
    if not mt5.initialize():
        raise RuntimeError(
            f"MT5 initialization failed: {mt5.last_error()}"
        )

    try:
        for symbol in SYMBOLS:
            data = fetch_multi_timeframe_data(symbol)

            print(f"\n{'=' * 60}")
            print(f"SYMBOL: {data['symbol']}")
            print(f"EQUITY: {data['equity']}")
            print(f"ASK PRICE: {data['ask_price']}")

            print("\n--- DAILY DATA ---")
            print(data["daily_data"])

            print("--- H1 DATA ---")
            print(data["hourly_data"])

    finally:
        mt5.shutdown()