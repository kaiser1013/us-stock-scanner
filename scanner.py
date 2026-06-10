import os
import smtplib
import pandas as pd
import yfinance as yf

import time

def safe_download(ticker):

    for i in range(3):

        print(f"{ticker}: attempt {i+1}")

        df = yf.download(
            ticker,
            period="6mo",
            interval="1d",
            auto_adjust=True,
            progress=False
        )

        if df is not None and not df.empty:
            return df

        time.sleep(1)

    return pd.DataFrame()

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

USE_SP500 = True

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
        url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"

        df = pd.read_csv(url)

        tickers = df["Symbol"].str.replace(".", "-", regex=False).tolist()

        print(f"Loaded S&P500 list: {len(tickers)} stocks")

        return tickers

    except Exception as e:

        print(f"S&P500 load failed: {e}")

        print("Using fallback list")

        return TICKERS
        
# =====================================
# 分析股票
# =====================================

def analyze_stock(ticker, market_bull, spy_return):
    
    try:

        df = safe_download(ticker)

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
        # Layer 1: Liquidity Filter（流動性）
        # ==========================

        if current_price < 20:
            print(f"{ticker}: Price filter")
            return None

        if avg_volume < 1000000:
            print(f"{ticker}: Volume filter")
            return None

        # ==========================
        # Layer 2: Trend Filter（方向）
        # ==========================

        if current_price < ma20:
            print(f"{ticker}: Below MA20")
            return None  # 明顯 downtrend 唔要
            
        ma50 = close.rolling(50).mean().iloc[-1]
        
        if ma20 < ma50:
            return None  # 中期 downtrend

        # ==========================
        # RSI
        # ==========================

        rsi = RSIIndicator(close=close, window=14).rsi().iloc[-1]
        rsi = float(rsi)

        # ==========================
        # MACD
        # ==========================

        macd = MACD(close)

        macd_line = macd.macd().iloc[-1]
        signal_line = macd.macd_signal().iloc[-1]

        if pd.isna(macd_line) or pd.isna(signal_line):
            return None

        # ==========================
        # Bollinger
        # ==========================

        bb = BollingerBands(close)

        middle_band = float(
            bb.bollinger_mavg().iloc[-1]
        )

        # ==========================
        # Layer 3: Momentum Confirmation（入場訊號）
        # ==========================

        if rsi < 40:
            return None  # 無 momentum

        if rsi > 80:
            return None  # 太 overbought（避免追高）

        if volume_ratio < 0.8:
            return None  # 無資金流入唔要

        if macd_line < signal_line-0.1:
            return None

        # ==========================
        # Relative Strength
        # ==========================

        stock_return = (
            close.iloc[-1]
            / close.iloc[-63]
            - 1
        ) * 100

        relative_strength = stock_return - spy_return

        if relative_strength < -5:
            return None
            
        # ==========================
        # Score
        # ==========================

        score = 0

        if relative_strength > 20:
            score += 20
        
        elif relative_strength > 10:
            score += 15

        elif relative_strength > 0:
            score += 10
        
        if current_price > ma20:
            score += 25
        
        if volume_ratio > 1.5:
            score += 20
        
        if 50 < rsi < 70:
            score += 15

        if macd_line > signal_line:
            score += 25

        if current_price > middle_band:
            score += 15

        market_bonus=0

        if market_bull:
            market_bonus=10

        score+=market_bonus

        if score < 50:
            return None

        if score >= 80:
            signal = "🔥 STRONG BUY"
        elif score >= 65:
            signal = "🟡 WATCH"
        else:
            signal = "NO TRADE"

        return {
            "Ticker": ticker,
            "Score": score,
            "RS": round(relative_strength, 2),
            "Signal": signal,
            "Price": round(current_price, 2),
            "RSI": round(rsi, 2),
            "VolumeRatio": round(volume_ratio, 2),
            "MA20": round(float(ma20), 2),
            "MA50": round(ma50,2),
            "MACD": round(macd_line,2),
            "SignalLine": round(signal_line,2),
            "MiddleBB": round(middle_band,2)
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

def build_email_body(
    df,
    market_bull,
    spy_price,
    spy_ma200
):
    market_status = "🟢 BULL" if market_bull else "🔴 BEAR"

    body = f"""
    MARKET STATUS

    {market_status}

    SPY:
    {spy_price:.2f}

    SPY MA200:
    {spy_ma200:.2f}

    Passed:
    {len(df)}

    ====================

    """
    body += "📈 DAILY TRADE SIGNALS\n\n"

    for row in df.itertuples():

        body += f"""
{row.Signal}
Ticker: {row.Ticker}
Score: {row.Score}
Price: {row.Price}
RSI: {row.RSI}
Vol: {row.VolumeRatio}

-------------------
"""

    body += "\nGenerated by GitHub Actions"

    return body


# =====================================
# Send Email
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
    if attachment:

        with open(attachment,"rb") as file:

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

        # ==========================
        # MARKET REGIME FILTER
        # ==========================

        spy = yf.download("^GSPC",period="1y",interval="1d",auto_adjust=True,progress=False)
        if isinstance(spy.columns, pd.MultiIndex):
            spy.columns = spy.columns.get_level_values(0)
        
        spy_close = spy["Close"].squeeze()
        
        spy_price = float(spy_close.iloc[-1])
        
        spy_return = (
            spy_close.iloc[-1] /
            spy_close.iloc[-63] - 1
        ) * 100
        
        spy_ma200 = float(
            spy_close.rolling(200).mean().iloc[-1]
        )
        
        market_bull = spy_price > spy_ma200

        print(f"Market Bull: {market_bull}")

    # ==========================
    # Bear Market Protection
    # ==========================
    
    if spy_price < spy_ma200:
    
        print("Bear market detected")
    
        body = f"""
    MARKET STATUS
    
    🔴 BEAR
    
    SPY:
    {spy_price:.2f}
    
    SPY MA200:
    {spy_ma200:.2f}
    
    Market below MA200.
    
    No swing trades today.
    
    Generated by GitHub Actions.
    """
    
        send_email(
            "🔴 Bear Market Alert",
            body,
            None
        )
    
        return
            
        print(
            f"Loaded {len(tickers)} test stocks"
        )

    for ticker in tickers:

        print(f"Processing {ticker}")

        result = analyze_stock(ticker, market_bull, spy_return)

        if result:

            print(f"{ticker} passed filter")

            results.append(result)

        # 避免 Yahoo Finance rate limit

        time.sleep(0.2)
            
    if len(results)==0:

        body=f"""
    MARKET STATUS

    {"🟢 BULL" if market_bull else "🔴 BEAR"}

    SPY:
    {spy_price:.2f}

    SPY MA200:
    {spy_ma200:.2f}

    No stocks passed today's filters.

    Generated by GitHub Actions.
    """

        send_email(
            "📉 Daily Scanner - No Candidates",
            body,
            None
        )

        return

    df = pd.DataFrame(results)

    df = df.sort_values(
        by="Score",
        ascending=False
    )

    trades = df[df["Signal"] == "🔥 STRONG BUY"]

    top20=trades.copy()

    if len(top20)<20:

        watch=df[
            df["Signal"]=="🟡 WATCH"
        ]
    
        remain=20-len(top20)
    
        top20=pd.concat([
            top20,
            watch.head(remain)
        ])

    top20.insert(
        0,
        "Rank",
        range(1, len(top20) + 1)
    )

    print(top20)

    print(f"Passed stocks: {len(df)}")
    print("Creating Excel...")

    excel_file = export_excel(top20)

    email_body = build_email_body(
        top20,
        market_bull,
        spy_price,
        spy_ma200
    )
    
    print("Sending Email...")
    
    send_email(
        "📈 Daily Stock Scanner Top 20",
        email_body,
        excel_file
    )


if __name__ == "__main__":
    main()
