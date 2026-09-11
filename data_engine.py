import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
import config


def initialize_mt5() -> bool:
    print("[SYSTEM] Initializing MetaTrader 5 connection...")
    path_arg = {"path": config.MT5_PATH} if config.MT5_PATH else {}
    if not mt5.initialize(**path_arg):
        print(f"[SYSTEM] MT5 initialize failed: {mt5.last_error()}")
        return False

    if config.MT5_LOGIN and config.MT5_LOGIN != 0:
        if not mt5.login(
            config.MT5_LOGIN,
            password=config.MT5_PASSWORD,
            server=config.MT5_SERVER,
        ):
            print(f"[SYSTEM] MT5 login failed: {mt5.last_error()}")
            mt5.shutdown()
            return False

    info = mt5.account_info()
    if info:
        print(
            f"[SYSTEM] MT5 Connected | Server: {info.server} | "
            f"Login: {info.login} | Balance: {info.balance:.2f} | "
            f"Equity: {info.equity:.2f}"
        )
    return True


def calculate_indicators(df: pd.DataFrame) -> dict:
    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["tick_volume"]

    ema_200 = close.ewm(span=config.EMA_PERIOD, adjust=False).mean()

    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / config.RSI_PERIOD, min_periods=config.RSI_PERIOD).mean()
    avg_loss = loss.ewm(alpha=1 / config.RSI_PERIOD, min_periods=config.RSI_PERIOD).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))

    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.ewm(span=config.ATR_PERIOD, adjust=False).mean()

    vol_ma = volume.rolling(config.VOL_MA_PERIOD).mean()
    relative_volume = volume / vol_ma.replace(0, np.nan)

    recent_bars = 10
    price_trend = {
        "trend_direction": "UP" if close.iloc[-1] > close.iloc[-recent_bars] else "DOWN",
        "price_change_pct": round(
            ((close.iloc[-1] - close.iloc[-recent_bars]) / close.iloc[-recent_bars]) * 100, 4
        ),
        "recent_high": round(float(high.iloc[-recent_bars:].max()), 6),
        "recent_low": round(float(low.iloc[-recent_bars:].min()), 6),
        "bar_count": recent_bars,
    }

    return {
        "ema_200": round(float(ema_200.iloc[-1]), 6),
        "rsi": round(float(rsi.iloc[-1]), 2),
        "atr": round(float(atr.iloc[-1]), 6),
        "relative_volume": round(float(relative_volume.iloc[-1]), 2)
            if not np.isnan(relative_volume.iloc[-1]) else 1.0,
        "tick_volume": int(volume.iloc[-1]),
        "price_trend": price_trend,
    }


def fetch_multi_timeframe_data(symbol: str) -> dict:
    if not mt5.symbol_select(symbol, True):
        print(f"[DATA] Failed to select {symbol}")
        return {}

    tick = mt5.symbol_info_tick(symbol)
    info = mt5.symbol_info(symbol)
    acct = mt5.account_info()

    if not tick or not info or not acct:
        print(f"[DATA] Missing tick/info/account for {symbol}")
        return {}

    h1_rates = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_H1, datetime.now(), 250)
    d1_rates = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_D1, datetime.now(), 250)

    if h1_rates is None or len(h1_rates) == 0:
        print(f"[DATA] No H1 data for {symbol}")
        return {}
    if d1_rates is None or len(d1_rates) == 0:
        print(f"[DATA] No D1 data for {symbol}")
        return {}

    h1_df = pd.DataFrame(h1_rates)
    d1_df = pd.DataFrame(d1_rates)

    h1_indicators = calculate_indicators(h1_df)
    d1_indicators = calculate_indicators(d1_df)

    return {
        "symbol": symbol,
        "bid": tick.bid,
        "ask": tick.ask,
        "spread": info.spread,
        "equity": acct.equity,
        "balance": acct.balance,
        "h1_data": h1_indicators,
        "daily_data": d1_indicators,
    }


def fetch_correlated_asset_prices(current_symbol: str, all_symbols: list[str]) -> dict:
    prices = {}
    for sym in all_symbols:
        if sym == current_symbol:
            continue
        tick = mt5.symbol_info_tick(sym)
        if tick:
            prices[sym] = {"bid": tick.bid, "ask": tick.ask}
    return prices
