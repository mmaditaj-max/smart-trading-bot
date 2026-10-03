# Smart Trading Bot

بوت تداول ذكي يساعدك على:
- جمع بيانات السوق الحقيقية من Binance
- تحليل الاتجاه باستخدام مؤشرات تقنيّة مثل EMA و RSI و MACD
- إنتاج إشارات شراء/بيع مع نسبة ثقة
- إرسال التنبيهات عبر البريد الإلكتروني أو تيليغرام
- تشغيل محاكاة/تجربة بلائحة مناسبة

ملاحظة: لا يوجد نظام تداول يضمن أرباحاً ثابتة. هذا المشروع مخصص للتعلم والبحث والتحليل، ويجب استخدامه مع إدارة مخاطرة صارمة وباختبار شامل قبل التشغيل الحقيقي.

## المميزات
- تحليل أزواج العملات مثل BTC/USDT و ETH/USDT
- فحص الاتجاه عبر فترات زمنية متعددة
- حساب إشارات شراء/بيع
- تحديد مناطق الدخول والتوقف
- تنبيهات عبر البريد أو Telegram
- إعدادات قابلة للتخصيص عبر ملف .env

## هيكل المشروع

```text
smart-trading-bot/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── main.py
│   ├── data/
│   │   ├── __init__.py
│   │   └── market_data.py
│   ├── strategies/
│   │   ├── __init__.py
│   │   └── technical.py
│   ├── notifications/
│   │   ├── __init__.py
│   │   ├── email_sender.py
│   │   └── telegram_sender.py
│   └── signal_engine.py
├── .env.example
├── requirements.txt
├── README.md
└── .gitignore
```

## المتطلبات
- Python 3.10+
- pip
- حساب Binance
- (اختياري) إعدادات بريد إلكتروني أو Telegram

## التثبيت

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# أو
.venv\Scripts\activate     # Windows

pip install -r requirements.txt
cp .env.example .env
```

## إعداد المتغيرات
افتح ملف `.env` وقم بتعديله:

```env
BINANCE_BASE_URL=https://api.binance.com
TRADING_SYMBOLS=BTCUSDT,ETHUSDT,BNBUSDT
TIMEFRAME=1h
RISK_PER_TRADE=0.02
MIN_CONFIDENCE=60
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_TO=receiver@gmail.com
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_CHAT_ID
```

## التشغيل

```bash
python -m app.main
```

## مثال على الإشارة

```json
{
  "symbol": "BTCUSDT",
  "signal": "BUY",
  "confidence": 83.5,
  "entry_zone": "near support",
  "stop_loss": "below recent low",
  "take_profit": "near resistance",
  "reasons": [
    "EMA fast > EMA slow",
    "RSI oversold recovery",
    "MACD bullish crossover"
  ]
}
```

## ملاحظات مهمة
- استخدم بيانات مالية حقيقية فقط بعد اختبار الاستراتيجية.
- لا تضع أحجام صفقة كبيرة جدًا.
- استخدم `stop loss` و `take profit` بشكل دائم.
- يفضّل البدء بـ `paper trading` قبل التشغيل الحقيقي.

## التطوير المستقبلي
- دعم أكثر من بورصة
- دعم أكثر من إطار زمني
- نظام backtesting
- قاعدة بيانات SQLite/PostgreSQL
- لوحة تحكم ويب
- جدولة التشغيل

## الترخيص
هذا المشروع مخصص للاستخدام التعليمي والبحثي.
