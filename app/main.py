import json

from app.config import MIN_CONFIDENCE, TRADING_SYMBOLS, TIMEFRAME
from app.notifications.email_sender import send_email
from app.notifications.telegram_sender import send_telegram
from app.signal_engine import generate_signal


def run_scan():
    results = []
    for symbol in TRADING_SYMBOLS:
        try:
            signal = generate_signal(symbol, interval=TIMEFRAME, min_confidence=MIN_CONFIDENCE)
            if signal:
                results.append(signal)
        except Exception as exc:
            print(f"[Error] {symbol}: {exc}")

    print(json.dumps(results, ensure_ascii=False, indent=2))

    for item in results:
        if item["signal"] in {"BUY", "SELL"}:
            message = (
                f"<b>{item['symbol']}</b>\n"
                f"الإشارة: <b>{item['signal']}</b>\n"
                f"نسبة الثقة: <b>{item['confidence']}%</b>\n"
                f"السعر: {item['price']}\n"
                f"منطقة الدخول: {item['entry_zone']}\n"
                f"وقف الخسارة: {item['stop_loss']}\n"
                f"الأهداف: {item['take_profit']}\n"
                f"المؤشرات: {', '.join(item['reasons'])}"
            )
            send_telegram(message)
            send_email(
                f"Trading Signal - {item['symbol']} {item['signal']}",
                f"الرمز: {item['symbol']}\n"
                f"الإشارة: {item['signal']}\n"
                f"نسبة الثقة: {item['confidence']}%\n"
                f"السعر: {item['price']}\n"
                f"منطقة الدخول: {item['entry_zone']}\n"
                f"وقف الخسارة: {item['stop_loss']}\n"
                f"الأهداف: {item['take_profit']}\n"
                f"الأسباب: {', '.join(item['reasons'])}\n"
            )

    return results


if __name__ == "__main__":
    run_scan()
