import time

import pandas as pd
import yfinance as yf

USE_SP500 = True

# =====================================
# 測試股票池
# =====================================

TICKERS = [
    "AAPL",
    "GOOGL",
    "MSFT",
    "NVDA",
    "TSLA",
    "AMZN",
    "META",
    "AMD",
    "AVGO",
    "NFLX"
]

SP500_URL = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"

def safe_last(series):
    """Return the latest valid numeric value from a pandas Series."""
    if series is None or len(series) == 0:
        return None
    value = series.iloc[-1]
    return None if pd.isna(value) else float(value)

def normalise_yfinance_columns(df):
    """Flatten yfinance MultiIndex columns into standard OHLCV names."""
    if df is None or df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    return df
    
def safe_download(
    ticker,
    period="2y",
    interval="1d",
    retries=3,
    sleep_seconds=1
):
    """Download price data with retry and basic OHLCV validation.
    
    v2.5 users two years by default so 252-session relative strength has
    sufficient history while retaining the v2.4.1 validation behaviour.
    """
    required_columns = {"Close", "High", "Low", "Volume"}
    for attempt in range(retries):
        try:
            print(f"{ticker}: attempt {attempt + 1}")
            df = yf.download(
                ticker,
                period=period, 
                interval=interval, 
                auto_adjust=True, 
                progress=False,
            )
            df = normalise_yfinance_columns(df)
            
            if df is None or df.empty:
                print(f"{ticker}: empty download")
                continue

            missing = required_columns.difference(df.columns)
            if missing:
                print(f"{ticker}: missing columns {sorted(missing)}")
                continue
                
            if df["Close"].isna().all():
                print(f"{ticker}: All Close values are NaN")
                continue
            
            return df.dropna(subset=["Close"]).copy()
        except Exception as error:
            print(f"{ticker} download error: {error}")
        time.sleep(sleep_seconds)
    return None

# =====================================
# S&P500 股票池
# =====================================

def get_sp500_tickers():
    """Load the S&P500 universe, with the test list as failback."""
    try:
        df = pd.read_csv(SP500_URL)
        tickers = (
            df["Symbol"]
            .astype(str)
            .str.replace(".", "-", regex=False)
            .tolist()
        )
        print(f"Loaded S&P500 list: {len(tickers)} stocks")
        return tickers
    except Exception as error:
        print(f"S&P500 load failed: {error}")
        print("Using fallback ticker list")
        return TICKERS
        
def calculate_period_return(close, sessions):
    """Return percentage performance over a completed session lookback."""
    if close is None or len(close) < sessions + 1:
        raise ValueError(f"Insufficient history for {sessions}-session return")
    return float((close.iloc[-1] / close.iloc[-(sessions + 1)] - 1) * 100)

def get_market_context():
    """Calculate market regime and multi-horizon SPY returns.
    
    The v2.4.1 keys are preserved for backwards compatibility. New v2.5 keys
    provide benchmark returns for 21, 63, 126 and 252 sessions.
    """
    spy = safe_download("^GSPC", period="2y", interval="1d")
    if spy is None or spy.empty:
        raise ValueError("Unable to download market context for ^GSPC")

    spy_close = spy["Close"].astype(float)
    if len(spy_close) < 253:
        raise ValueError("Insufficient ^GSPC history for v2.5 market context")

    spy_price = float(spy_close.iloc[-1])
    spy_ma200 = float(spy_close.rolling(200).mean().iloc[-1])
    spy_returns = {
        21: calculate_period_return(spy_close, 21),
        63: calculate_period_return(spy_close, 63),
        126: calculate_period_return(spy_close, 126),
        252: calculate_period_return(spy_close, 252),
    }
        
    return {
        "spy_price": spy_price,
        "spy_ma200": spy_ma200,
        "spy_return": spy_returns[63],
        "spy_returns": spy_returns,
        "market_bull": spy_price > spy_ma200,
    }
