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

def _normalise_yfinance_columns(df):
    """Handle yfinance MultiIndex columns and return standard OHLCV columns."""
    if df is None or df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df
    
def safe_download(ticker, period="1y", interval="1d", retries=3, sleep_seconds=1):
    """Download market data with retry, empty-data protection and Close validation."""
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
            df = _normalise_yfinance_columns(df)
            
            if df is None or df.empty:
                print(f"{ticker}: empty download")
                continue
            if "Close" not in df.columns:
                print(f"{ticker}: Missing Close")
                continue
            if df["Close"].isna().all():
                print(f"{ticker}: ALL Close NaN")
                continue
            
            return df
        except Exception as error:
            print(f"{ticker} download error: {error}")
        time.sleep(sleep_seconds)
    return None

# =====================================
# S&P500 股票池
# =====================================

def get_sp500_tickers():
    """Load S&P500 tickers. Fall back to test list if external list fails."""
    try:
        df = pd.read_csv(SP500_URL)
        tickers = df["Symbol"].str.replace(".","-", regex=False).tolist()
        print(f"Loaded S&P500 list: {len(tickers)} stocks")
        return tickers
    except Exception as error:
        print(f"S&P500 load failed: {error}")
        print("Using fallback list")
        return TICKERS

def get_market_context():
    """Download S&P500 index data and calculate market regime context."""
    spy = safe_download("^GSPC", period="1y", interval="1d")
    if spy is None or spy.empty:
        raise ValueError("Unable to download market context for ^GSPC")

    spy_close = spy["Close"].squeeze()
    if len(spy_close) < 200:
        raise ValueError("Insufficient market data for MA200")

    spy_price = float(spy_close.iloc[-1])
    spy_ma200 = float(spy_close.rolling(200).mean().iloc[-1])

    if pd.isna(spy_ma200):
        raise ValueError("SPY MA200 is NaN")
    
    spy_return = 0
    if len(spy_close) >= 63:
        spy_return = (spy_close.iloc[-1] / spy_close.iloc[-63] - 1) * 100

    market_bull = spy_price > spy_ma200

    return {
        "spy_price": spy_price,
        "spy_ma200": spy_ma200,
        "spy_return": spy_return,
        "market_bull": market_bull,
    }
