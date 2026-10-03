import requests

from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Telegram] التكوين غير كامل، تم تجاهل الإشعار.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        response = requests.post(url, data=payload, timeout=20)
        response.raise_for_status()
        print("[Telegram] تم إرسال الإشعار بنجاح.")
        return True
    except Exception as exc:
        print(f"[Telegram] فشل إرسال الإشعار: {exc}")
        return False
