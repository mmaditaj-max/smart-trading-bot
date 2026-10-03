from app.data.market_data import fetch_klines
from app.strategies.technical import ema, macd, rsi


def generate_signal(symbol: str, interval: str = "1h", min_confidence: float = 60):
    df = fetch_klines(symbol, interval=interval, limit=200)
    if df.empty:
        return None

    close = df["close"]
    ema_fast = ema(close, 12)
    ema_slow = ema(close, 26)
    rsi_value = rsi(close, 14)
    macd_line, signal_line, histogram = macd(close, fast=12, slow=26, signal=9)

    latest = df.iloc[-1]
    latest_ema_fast = ema_fast.iloc[-1]
    latest_ema_slow = ema_slow.iloc[-1]
    latest_rsi = rsi_value.iloc[-1]
    latest_macd = macd_line.iloc[-1]
    latest_signal = signal_line.iloc[-1]
    latest_hist = histogram.iloc[-1]

    score = 0
    reasons = []

    if latest_ema_fast > latest_ema_slow:
        score += 25
        reasons.append("EMA fast > EMA slow")
    else:
        score -= 25
        reasons.append("EMA fast < EMA slow")

    if latest_rsi < 30:
        score += 18
        reasons.append("RSI in oversold zone")
    elif latest_rsi > 70:
        score -= 18
        reasons.append("RSI in overbought zone")
    else:
        score += 8
        reasons.append("RSI neutral")

    if latest_macd > latest_signal:
        score += 25
        reasons.append("MACD bullish crossover")
    else:
        score -= 25
        reasons.append("MACD bearish crossover")

    if latest_hist > 0:
        score += 12
        reasons.append("Histogram positive")
    else:
        score -= 12
        reasons.append("Histogram negative")

    buy_threshold = 40
    sell_threshold = -40

    if score >= buy_threshold:
        signal = "BUY"
        confidence = min(95, 50 + abs(score) * 1.2)
    elif score <= sell_threshold:
        signal = "SELL"
        confidence = min(95, 50 + abs(score) * 1.2)
    else:
        signal = "HOLD"
        confidence = 50

    if confidence < min_confidence and signal != "HOLD":
        signal = "HOLD"
        confidence = min_confidence

    entry_zone = "near support" if signal == "BUY" else "near resistance" if signal == "SELL" else "wait for confirmation"
    stop_loss = "below recent low" if signal == "BUY" else "above recent high"
    take_profit = "near resistance" if signal == "BUY" else "near support"

    return {
        "symbol": symbol,
        "signal": signal,
        "confidence": round(confidence, 2),
        "entry_zone": entry_zone,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "price": float(latest["close"]),
        "reasons": reasons,
        "rsi": round(float(latest_rsi), 2),
        "ema_fast": round(float(latest_ema_fast), 4),
        "ema_slow": round(float(latest_ema_slow), 4),
        "macd": round(float(latest_macd), 4),
        "signal_line": round(float(latest_signal), 4),
    }
