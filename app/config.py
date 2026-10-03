import os
from dotenv import load_dotenv

load_dotenv()

BINANCE_BASE_URL = os.getenv("BINANCE_BASE_URL", "https://api.binance.com")
TRADING_SYMBOLS = [s.strip() for s in os.getenv("TRADING_SYMBOLS", "BTCUSDT,ETHUSDT,BNBUSDT").split(",") if s.strip()]
TIMEFRAME = os.getenv("TIMEFRAME", "1h")
RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", "0.02"))
MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "60"))

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_TO = os.getenv("EMAIL_TO")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
