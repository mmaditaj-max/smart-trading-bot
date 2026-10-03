#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Smart Trading Bot - نظام تداول ذكي متكامل
يقوم بتحليل الأسواق الحقيقية وإرسال إشارات شراء/بيع مع نسب ثقة
"""

import os
import sys
import json
import smtplib
import requests
import pandas as pd
from datetime import datetime
from email.mime.text import MIMEText
from dotenv import load_dotenv
from typing import Dict, List, Optional

# =====================================================================
# 1. إعدادات المشروع - Configuration
# =====================================================================

load_dotenv()

BINANCE_BASE_URL = os.getenv("BINANCE_BASE_URL", "https://api.binance.com")
TRADING_SYMBOLS = [
    s.strip()
    for s in os.getenv("TRADING_SYMBOLS", "BTCUSDT,ETHUSDT,BNBUSDT").split(",")
    if s.strip()
]
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

# =====================================================================
# 2. جلب بيانات السوق من Binance - Market Data
# =====================================================================

def fetch_klines(symbol: str, interval: str = TIMEFRAME, limit: int = 200) -> pd.DataFrame:
    """
    جلب بيانات الشموع من Binance
    """
    try:
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
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
        ]
        df = pd.DataFrame(data, columns=columns)
        
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
        df = df.sort_values("open_time").reset_index(drop=True)
        return df
    except Exception as exc:
        print(f"[Error] فشل جلب البيانات ل {symbol}: {exc}")
        return pd.DataFrame()


def fetch_price(symbol: str) -> float:
    """
    جلب السعر الحالي للرمز
    """
    try:
        url = f"{BINANCE_BASE_URL}/api/v3/ticker/price"
        response = requests.get(url, params={"symbol": symbol}, timeout=20)
        response.raise_for_status()
        data = response.json()
        return float(data["price"])
    except Exception as exc:
        print(f"[Error] فشل جلب السعر ل {symbol}: {exc}")
        return 0.0

# =====================================================================
# 3. المؤشرات التقنية - Technical Indicators
# =====================================================================

def ema(series: pd.Series, span: int) -> pd.Series:
    """
    حساب المتوسط المتحرك الأسي
    """
    return series.ewm(span=span, adjust=False).mean()


def rsi(series: pd.Series, periods: int = 14) -> pd.Series:
    """
    حساب مؤشر القوة النسبية (RSI)
    """
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=periods, min_periods=periods).mean()
    avg_loss = loss.rolling(window=periods, min_periods=periods).mean()

    rs = avg_gain / avg_loss.replace(0, pd.NA)
    value = 100 - (100 / (1 + rs))
    return value.fillna(50)


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """
    حساب MACD (Moving Average Convergence Divergence)
    """
    fast_ema = ema(series, fast)
    slow_ema = ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2):
    """
    حساب Bollinger Bands
    """
    sma = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper_band = sma + (std_dev * std)
    lower_band = sma - (std_dev * std)
    return upper_band, sma, lower_band

# =====================================================================
# 4. محرك إنشاء الإشارات - Signal Engine
# =====================================================================

def generate_signal(symbol: str, interval: str = "1h", min_confidence: float = 60) -> Optional[Dict]:
    """
    توليد إشارات شراء/بيع بناءً على المؤشرات التقنية
    """
    df = fetch_klines(symbol, interval=interval, limit=200)
    if df.empty or len(df) < 26:
        return None

    close = df["close"]
    
    # حساب المؤشرات
    ema_fast = ema(close, 12)
    ema_slow = ema(close, 26)
    rsi_value = rsi(close, 14)
    macd_line, signal_line, histogram = macd(close, fast=12, slow=26, signal=9)
    upper_bb, middle_bb, lower_bb = bollinger_bands(close, 20, 2)

    # آخر قيمة
    latest = df.iloc[-1]
    latest_ema_fast = ema_fast.iloc[-1]
    latest_ema_slow = ema_slow.iloc[-1]
    latest_rsi = rsi_value.iloc[-1]
    latest_macd = macd_line.iloc[-1]
    latest_signal = signal_line.iloc[-1]
    latest_hist = histogram.iloc[-1]
    latest_close = float(latest["close"])
    latest_upper_bb = upper_bb.iloc[-1]
    latest_lower_bb = lower_bb.iloc[-1]

    # حساب النقاط
    score = 0
    reasons = []

    # 1. تحليل EMA
    if latest_ema_fast > latest_ema_slow:
        score += 25
        reasons.append("✓ EMA fast > EMA slow (اتجاه صاعد)")
    else:
        score -= 25
        reasons.append("✗ EMA fast < EMA slow (اتجاه هابط)")

    # 2. تحليل RSI
    if latest_rsi < 30:
        score += 18
        reasons.append("✓ RSI في منطقة الإفراط في البيع")
    elif latest_rsi > 70:
        score -= 18
        reasons.append("✗ RSI في منطقة الإفراط في الشراء")
    else:
        score += 8
        reasons.append("~ RSI محايد")

    # 3. تحليل MACD
    if latest_macd > latest_signal:
        score += 25
        reasons.append("✓ MACD فوق خط الإشارة (إشارة صعود)")
    else:
        score -= 25
        reasons.append("✗ MACD تحت خط الإشارة (إشارة هبوط)")

    # 4. تحليل Histogram
    if latest_hist > 0:
        score += 12
        reasons.append("✓ Histogram موجب")
    else:
        score -= 12
        reasons.append("✗ Histogram سالب")

    # 5. تحليل Bollinger Bands
    if latest_close < latest_lower_bb:
        score += 15
        reasons.append("✓ السعر تحت الحد الأدنى (فرصة شراء)")
    elif latest_close > latest_upper_bb:
        score -= 15
        reasons.append("✗ السعر فوق الحد الأعلى (انتبه للبيع)")
    else:
        score += 5
        reasons.append("~ السعر ضمن النطاق")

    # تحديد الإشارة
    buy_threshold = 40
    sell_threshold = -40

    if score >= buy_threshold:
        signal = "BUY"
        confidence = min(98, 50 + abs(score) * 1.2)
    elif score <= sell_threshold:
        signal = "SELL"
        confidence = min(98, 50 + abs(score) * 1.2)
    else:
        signal = "HOLD"
        confidence = 50

    # تطبيق حد أدنى للثقة
    if confidence < min_confidence and signal != "HOLD":
        signal = "HOLD"

    # تحديد مناطق الدخول والخروج
    entry_zone = "بالقرب من الدعم" if signal == "BUY" else "بالقرب من المقاومة" if signal == "SELL" else "انتظر تأكيد"
    stop_loss = "تحت أقل قمة حديثة" if signal == "BUY" else "فوق أعلى قمة حديثة"
    take_profit = "بالقرب من المقاومة" if signal == "BUY" else "بالقرب من الدعم"

    return {
        "timestamp": datetime.now().isoformat(),
        "symbol": symbol,
        "signal": signal,
        "confidence": round(confidence, 2),
        "entry_zone": entry_zone,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "current_price": round(latest_close, 4),
        "reasons": reasons,
        "technical_data": {
            "rsi": round(float(latest_rsi), 2),
            "ema_fast": round(float(latest_ema_fast), 4),
            "ema_slow": round(float(latest_ema_slow), 4),
            "macd": round(float(latest_macd), 4),
            "signal_line": round(float(latest_signal), 4),
            "histogram": round(float(latest_hist), 6),
            "bb_upper": round(float(latest_upper_bb), 4),
            "bb_middle": round(float(middle_bb.iloc[-1]), 4),
            "bb_lower": round(float(latest_lower_bb), 4),
        }
    }

# =====================================================================
# 5. نظام الإشعارات - Notifications
# =====================================================================

def send_email(subject: str, body: str) -> bool:
    """
    إرسال بريد إلكتروني
    """
    if not all([EMAIL_HOST, EMAIL_USER, EMAIL_PASSWORD, EMAIL_TO]):
        print("[📧 Email] الإعدادات غير مكتملة - تم تجاهل الإرسال")
        return False

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO

    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, [EMAIL_TO], msg.as_string())
        server.quit()
        print(f"[✅ Email] تم إرسال البريد بنجاح إلى {EMAIL_TO}")
        return True
    except Exception as exc:
        print(f"[❌ Email] فشل الإرسال: {exc}")
        return False


def send_telegram(message: str) -> bool:
    """
    إرسال رسالة عبر Telegram
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[🤖 Telegram] الإعدادات غير مكتملة - تم تجاهل الإرسال")
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
        print(f"[✅ Telegram] تم إرسال الرسالة بنجاح")
        return True
    except Exception as exc:
        print(f"[❌ Telegram] فشل الإرسال: {exc}")
        return False


def format_signal_message(signal_data: Dict) -> tuple:
    """
    تنسيق الإشارة للإرسال عبر البريد والتيليجرام
    """
    symbol = signal_data["symbol"]
    sig = signal_data["signal"]
    confidence = signal_data["confidence"]
    price = signal_data["current_price"]
    entry = signal_data["entry_zone"]
    stop = signal_data["stop_loss"]
    tp = signal_data["take_profit"]
    reasons = "\n".join(signal_data["reasons"])
    
    tech = signal_data["technical_data"]
    rsi_val = tech["rsi"]
    ema_f = tech["ema_fast"]
    ema_s = tech["ema_slow"]
    
    # رسالة Telegram
    telegram_msg = (
        f"<b>📊 إشارة تداول - {symbol}</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"<b>الإشارة:</b> {sig}\n"
        f"<b>نسبة الثقة:</b> {confidence}%\n"
        f"<b>السعر الحالي:</b> {price}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"<b>منطقة الدخول:</b> {entry}\n"
        f"<b>وقف الخسارة:</b> {stop}\n"
        f"<b>الهدف:</b> {tp}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"<b>المؤشرات:</b>\n"
        f"• RSI: {rsi_val}\n"
        f"• EMA Fast: {ema_f}\n"
        f"• EMA Slow: {ema_s}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"<b>الأسباب:</b>\n{reasons}"
    )
    
    # رسالة البريد
    email_body = (
        f"إشارة تداول جديدة\n"
        f"{'=' * 40}\n\n"
        f"الرمز: {symbol}\n"
        f"الإشارة: {sig}\n"
        f"نسبة الثقة: {confidence}%\n"
        f"السعر الحالي: {price}\n\n"
        f"منطقة الدخول: {entry}\n"
        f"وقف الخسارة: {stop}\n"
        f"الهدف: {tp}\n\n"
        f"المؤشرات:\n"
        f"RSI: {rsi_val}\n"
        f"EMA Fast: {ema_f}\n"
        f"EMA Slow: {ema_s}\n\n"
        f"الأسباب:\n{reasons}\n\n"
        f"الوقت: {signal_data['timestamp']}"
    )
    
    return telegram_msg, email_body

# =====================================================================
# 6. محرك المراقبة الرئيسي - Main Engine
# =====================================================================

def run_scan() -> List[Dict]:
    """
    تشغيل المسح الشامل على جميع الأزواج
    """
    print(f"\n{'='*60}")
    print(f"🤖 بوت التداول الذكي - Smart Trading Bot")
    print(f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    results = []
    
    for symbol in TRADING_SYMBOLS:
        print(f"🔍 جاري تحليل {symbol}...")
        try:
            signal = generate_signal(symbol, interval=TIMEFRAME, min_confidence=MIN_CONFIDENCE)
            if signal:
                results.append(signal)
                
                # طباعة النتائج
                print(f"\n✅ {symbol}")
                print(f"   الإشارة: {signal['signal']}")
                print(f"   الثقة: {signal['confidence']}%")
                print(f"   السعر: {signal['current_price']}")
                
                # إرسال الإشعارات إذا كانت الإشارة قوية
                if signal["signal"] in {"BUY", "SELL"}:
                    telegram_msg, email_body = format_signal_message(signal)
                    send_telegram(telegram_msg)
                    send_email(
                        f"🚨 إشارة تداول - {symbol} {signal['signal']}",
                        email_body
                    )
        except Exception as exc:
            print(f"❌ خطأ في {symbol}: {exc}")
    
    # طباعة ملخص النتائج
    print(f"\n{'='*60}")
    print(f"📋 ملخص النتائج:")
    print(f"{'='*60}")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"{'='*60}\n")
    
    return results


def main():
    """
    الدالة الرئيسية
    """
    print("\n🚀 جاري بدء البوت...")
    print(f"📈 الأزواج المراقبة: {', '.join(TRADING_SYMBOLS)}")
    print(f"⏱️  الإطار الزمني: {TIMEFRAME}")
    print(f"📊 حد الثقة الأدنى: {MIN_CONFIDENCE}%\n")
    
    run_scan()


# =====================================================================
# 7. نقطة البداية
# =====================================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 تم إيقاف البوت بواسطة المستخدم.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        sys.exit(1)
