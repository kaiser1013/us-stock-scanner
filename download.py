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
    
def safe_download(ticker, period="1y", interval="1d", retries=3, sleep_seconds=1):
    """Download price data with retry and basic OHLCV validation."""
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
        tickers = df["Symbol"].str.replace(".","-", regex=False).tolist()
        print(f"Loaded S&P500 list: {len(tickers)} stocks")
        return tickers
    except Exception as error:
        print(f"S&P500 load failed: {error}")
        print("Using fallback ticker list")
        return TICKERS

def get_market_context():
    """Calculate the S&P500 market regime and 63-session return."""
    spy = safe_download("^GSPC", period="1y", interval="1d")
    if spy is None or spy.empty:
        raise ValueError("Unable to download market context for ^GSPC")

    spy_close = spy["Close"].astype(float)
    if len(spy_close) < 200:
        raise ValueError("Insufficient ^GSPC history for MA200")

    spy_price = float(spy_close.iloc[-1])
    spy_ma200 = float(spy_close.rolling(200).mean().iloc[-1])
    spy_return = (spy_close.iloc[-1] / spy_close.iloc[-63] - 1) * 100

    return {
        "spy_price": spy_price,
        "spy_ma200": spy_ma200,
        "spy_return": spy_return,
        "market_bull": spy_price > spy_ma200,
    }
