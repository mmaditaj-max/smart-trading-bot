import requests
import pandas as pd

from app.config import BINANCE_BASE_URL, TIMEFRAME


def fetch_klines(symbol: str, interval: str = TIMEFRAME, limit: int = 200):
    url = f"{BINANCE_BASE_URL}/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
    }
    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()

    columns = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_asset_volume",
        "number_of_trades",
        "taker_buy_base_asset_volume",
        "taker_buy_quote_asset_volume",
        "ignore",
    ]
    df = pd.DataFrame(data, columns=columns)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
    df = df.sort_values("open_time").reset_index(drop=True)
    return df


def fetch_price(symbol: str):
    url = f"{BINANCE_BASE_URL}/api/v3/ticker/price"
    response = requests.get(url, params={"symbol": symbol}, timeout=20)
    response.raise_for_status()
    data = response.json()
    return float(data["price"])
