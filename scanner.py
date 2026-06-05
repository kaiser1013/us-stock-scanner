import os
import smtplib
import pandas as pd
import yfinance as yf

from datetime import datetime

from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# =====================================

# 掃描模式

# =====================================

USE_SP500 = False

# =====================================
# 測試股票池
# =====================================

TICKERS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "META",
    "GOOGL",
    "TSLA",
    "AMD",
    "AVGO",
    "NFLX"
]

# =====================================
# S&P500 股票池
# =====================================

import requests
import pandas as pd
from io import StringIO

def get_sp500_tickers():
    try:

    # Wikipedia 版本
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/137.0 Safari/537.36"
        )
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    table = pd.read_html(
        StringIO(response.text)
    )[0]

    tickers = table["Symbol"].tolist()

    tickers = [
        ticker.replace(".", "-")
        for ticker in tickers
    ]

    return tickers

except Exception as e:

    print(f"Failed loading S&P500 list: {e}")

    return [

            "AAPL","MSFT","NVDA","AMZN","META",

            "GOOGL","AVGO","AMD","TSLA","PLTR"
    ]
# =====================================
# 分析股票
# =====================================

def analyze_stock(ticker):

    try:

        df = yf.download(
        ticker,
        period="6mo",
        interval="1d",
        auto_adjust=True,
        progress=False
        )

        if df.empty:
            print(f"{ticker}: No data")
            return None
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
    
        close = df["Close"]
        volume = df["Volume"]

        current_price = float(close.iloc[-1])

        ma20 = close.rolling(20).mean().iloc[-1]

        avg_volume = volume.rolling(20).mean().iloc[-1]

        if avg_volume <= 0:
            return None
        if pd.isna(ma20) or pd.isna(avg_volume):
            return None

        volume_ratio = float(volume.iloc[-1] / avg_volume)
        
        print(
            f"{ticker} | "
            f"Price={current_price:.2f} | "
            f"MA20={ma20:.2f} | "
            f"AvgVol={avg_volume:,.0f} | "
            f"VolRatio={volume_ratio:.2f}"
        )


        # ==========================
        # 第一層過濾
        # ==========================

        if current_price < 5:
            return None

        if avg_volume < 500000:
            return None

        # ==========================
        # RSI
        # ==========================

        rsi = float(
            RSIIndicator(close=close)
            .rsi()
            .iloc[-1]
        )

        # ==========================
        # MACD
        # ==========================

        macd = MACD(close)

        macd_line = float(
            macd.macd().iloc[-1]
        )

        signal_line = float(
            macd.macd_signal().iloc[-1]
        )

        # ==========================
        # Bollinger
        # ==========================

        bb = BollingerBands(close)

        middle_band = float(
            bb.bollinger_mavg().iloc[-1]
        )

        # ==========================
        # Score
        # ==========================

        score = 0

        if current_price > ma20:
            score += 20

        if volume_ratio > 1.2:
            score += 20

        if rsi > 50:
            score += 20

        if macd_line > signal_line:
            score += 20

        if current_price > middle_band:
            score += 20

        return {
            "Ticker": ticker,
            "Score": score,
            "Price": round(current_price, 2),
            "RSI": round(rsi, 2),
            "VolumeRatio": round(volume_ratio, 2),
            "MA20": round(float(ma20), 2)
        }

    except Exception as e:

        print(f"Error processing {ticker}: {e}")

        return None


# =====================================
# Excel
# =====================================

def export_excel(df):

    today = datetime.today().strftime("%Y%m%d")

    filename = f"stock_scan_{today}.xlsx"

    df.to_excel(
        filename,
        index=False
    )

    return filename


# =====================================
# Email內容
# =====================================

def build_email_body(df):

    body = """
📈 DAILY STOCK SCANNER

Top Candidates

"""

    for idx, row in enumerate(df.itertuples(), start=1):

        body += f"""
#{idx} {row.Ticker}

Score: {row.Score}
Price: ${row.Price}
RSI: {row.RSI}
Volume Ratio: {row.VolumeRatio}

----------------------------

"""

    body += "\nGenerated by GitHub Actions"

    return body


# =====================================
# Email
# =====================================

def send_email(subject, body, attachment):

    email_user = os.environ["EMAIL_USER"]
    email_password = os.environ["EMAIL_PASSWORD"]
    email_to = os.environ["EMAIL_TO"]

    msg = MIMEMultipart()

    msg["From"] = email_user
    msg["To"] = email_to
    msg["Subject"] = subject

    msg.attach(
        MIMEText(body, "plain")
    )

    with open(attachment, "rb") as file:

        part = MIMEBase(
            "application",
            "octet-stream"
        )

        part.set_payload(file.read())

    encoders.encode_base64(part)

    part.add_header(
        "Content-Disposition",
        f"attachment; filename={attachment}"
    )

    msg.attach(part)

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465
    ) as server:

        server.login(
            email_user,
            email_password
        )

        server.send_message(msg)

    print("Email sent successfully")


# =====================================
# Main
# =====================================

import time
def main():

    print("Scanning stocks...")

    results = []

    if USE_SP500:

        tickers = get_sp500_tickers()

        print(
            f"Loaded {len(tickers)} S&P500 stocks"
        )

    else:

        tickers = TICKERS

        print(
            f"Loaded {len(tickers)} test stocks"
        )

    for ticker in tickers:

        print(f"Processing {ticker}")

        result = analyze_stock(ticker)

        if result:

            print(f"{ticker} passed filter")

            results.append(result)

        # 避免 Yahoo Finance rate limit

        time.sleep(0.5)
            
    if len(results) == 0:

        print("No stocks passed filters")

        return

    df = pd.DataFrame(results)

    df = df.sort_values(
        by="Score",
        ascending=False
    )

    top20 = df.head(20)

    top20.insert(
        0,
        "Rank",
        range(1, len(top20) + 1)
    )

    print(top20)

    print(f"Passed stocks: {len(df)}")
    print("Creating Excel...")

    excel_file = export_excel(top20)

    email_body = build_email_body(top20)
    
    print("Sending Email...")
    
    send_email(
        "📈 Daily Stock Scanner Top 20",
        email_body,
        excel_file
    )


if __name__ == "__main__":
    main()
