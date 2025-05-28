
# crypto_ai_pattern_alert.py

import os
import time
import requests
import pandas as pd
import numpy as np
import mplfinance as mpf
from datetime import datetime
from sklearn.linear_model import LinearRegression

# =============== CONFIGURATION ==================
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
TELEGRAM_CHANNEL_ID = "@YOUR_CHANNEL_ID"
INTERVAL_SECONDS = 900  # 15 minutes
SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT", "DOGEUSDT",
    "ADAUSDT", "AVAXUSDT", "LTCUSDT", "LINKUSDT", "MATICUSDT", "DOTUSDT",
    "TRXUSDT", "ATOMUSDT", "NEARUSDT", "UNIUSDT", "XMRUSDT", "ETCUSDT",
    "IMXUSDT", "SUIUSDT", "APTUSDT", "FILUSDT", "INJUSDT", "GRTUSDT",
    "RNDRUSDT", "THETAUSDT", "AAVEUSDT", "OPUSDT", "ARBUSDT", "SEIUSDT"
]
TIMEFRAMES = {"1h": "1h", "4h": "4h"}
DATA_LIMIT = 100
BINANCE_API = "https://api.binance.com/api/v3/klines"
# ================================================

def send_telegram_message(message, image_path=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto" if image_path else f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHANNEL_ID}
    files = None

    if image_path:
        data["caption"] = message
        files = {"photo": open(image_path, "rb")}
    else:
        data["text"] = message

    requests.post(url, data=data, files=files)

def fetch_binance_data(symbol, interval):
    url = f"{BINANCE_API}?symbol={symbol}&interval={interval}&limit={DATA_LIMIT}"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data, columns=[
        "timestamp", "Open", "High", "Low", "Close", "Volume",
        "Close time", "Quote asset volume", "Number of trades",
        "Taker buy base", "Taker buy quote", "Ignore"
    ])
    df["Date"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("Date", inplace=True)
    df = df[["Open", "High", "Low", "Close", "Volume"]].astype(float)
    return df

def detect_wedge_pattern(df):
    lows = df["Low"].values
    highs = df["High"].values
    x = np.arange(len(df)).reshape(-1, 1)

    low_model = LinearRegression().fit(x, lows)
    high_model = LinearRegression().fit(x, highs)

    low_slope = low_model.coef_[0]
    high_slope = high_model.coef_[0]

    breakout = False
    direction = None
    latest_close = df["Close"].iloc[-1]
    expected_high = high_model.predict([[len(df)-1]])[0]
    expected_low = low_model.predict([[len(df)-1]])[0]

    if latest_close > expected_high:
        breakout = True
        direction = "up"
    elif latest_close < expected_low:
        breakout = True
        direction = "down"

    return {
        "found": abs(high_slope - low_slope) > 0.001,
        "breakout": breakout,
        "direction": direction,
        "high_line": (high_model.coef_[0], high_model.intercept_),
        "low_line": (low_model.coef_[0], low_model.intercept_)
    }

def plot_chart(df, symbol, pattern_result, interval):
    df_plot = df.copy()
    filename = f"{symbol}_{interval}.png"
    lines = []

    if pattern_result["found"]:
        x_vals = np.arange(len(df_plot))
        high_line = pattern_result["high_line"][0] * x_vals + pattern_result["high_line"][1]
        low_line = pattern_result["low_line"][0] * x_vals + pattern_result["low_line"][1]
        df_plot["high_line"] = high_line
        df_plot["low_line"] = low_line
        add_plot = [
            mpf.make_addplot(df_plot["high_line"], color="orange"),
            mpf.make_addplot(df_plot["low_line"], color="orange")
        ]
    else:
        add_plot = []

    mpf.plot(df_plot, type="candle", volume=False, style="charles",
             title=f"{symbol} [{interval}]",
             addplot=add_plot,
             savefig=filename)
    return filename

def check_and_alert():
    for symbol in SYMBOLS:
        for label, interval in TIMEFRAMES.items():
            try:
                df = fetch_binance_data(symbol, interval)
                pattern = detect_wedge_pattern(df)
                if pattern["found"] and pattern["breakout"]:
                    chart = plot_chart(df, symbol, pattern, interval)
caption = f"📉 Wedge Breakout detected!\nSymbol: {symbol}\nTimeframe: {tf}\nBreakout Price: {price}"
Symbol: {symbol}
Interval: {interval.upper()}
Direction: {pattern['direction'].upper()}"
                    send_telegram_message(caption, chart)
                    print(f"Alert sent for {symbol} [{interval}]")
            except Exception as e:
                print(f"Error with {symbol} [{interval}]:", e)

if __name__ == "__main__":
    while True:
        print(f"Running wedge breakout scan... {datetime.utcnow()} UTC")
        check_and_alert()
        time.sleep(INTERVAL_SECONDS)
