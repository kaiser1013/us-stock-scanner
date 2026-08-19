import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, ADXIndicator
from ta.volatility import BollingerBands
from download import safe_last

def calculate_indicators(ticker, df, spy_return):
    """Calculate all scanner indicators and return a single metrics dictionary."""
    if df is None or df.empty:
        print(f"{ticker}: No data")
        return None
    if "Close" not in df.columns or df["Close"].isna().all():
        print(f"{ticker}: Close all NaN")
        return None
    if len(df) < 210:
        print(f"{ticker}: insufficient data {len(df)}")
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]
    
    current_price = float(close.iloc[-1])
    ma20 = safe_last(close.rolling(20).mean())
    ma50 = safe_last(close.rolling(50).mean())
    ma200 = safe_last(close.rolling(200).mean())
    avg_volume = safe_last(volume.rolling(20).mean())
    
    if ma20 is None or ma50 is None or ma200 is None or avg_volume is None:
        print(f"{ticker}: Indicator NaN")
        return None
    if avg_volume <- 0:
        print(f"{ticker}: Avg volume invalid")
        return None
    
    volume_ratio = float(volume.iloc[-1] / avg_volume)

    # ==========================
    # RSI
    # ==========================
    
    rsi = RSIIndicator(close=close, window=14).rsi().iloc[-1]
    if pd.isna(rsi):
        print(f"{ticker}: RSI NaN")
        return None
    rsi = float(rsi)

    # ==========================
    # MACD
    # ==========================
    
    macd = MACD(close)
    macd_line = macd.macd().iloc[-1]
    signal_line = macd.macd_signal().iloc[-1]
    if pd.isna(macd_line) or pd.isna(signal_line):
        print (f"{ticker}: MACD NaN")
        return None
    macd_line = float(macd_line)
    signal_line = float(signal_line)

    # ==========================
    # BOLLINGER
    # ==========================
    
    bb = BollingerBands(close)
    middle_band = bb.bollinger_mavg().iloc[-1]
    upper_band = bb. bollinger_hband().iloc[-1]
    if pd.isna(middle_band) or pd.isna(upper_band):
        print(f"{ticker}: Bollinger NaN")
        return None
    middle_band = float(middle_band)
    upper_band = float(upper_band)

    # ==========================
    # RELATIVE STRENGTH
    # ==========================
    
    stock_return = (close.iloc[-1] / close.iloc[-63] - 1) * 100
    relative_strength = stock_return - spy_return

    # ==========================
    # ADX
    # ==========================
    
    adx_indicator = ADXIndicator(high=high, low=low, close=close, window=14)
    adx = adx_indicator.adx().iloc[-1]
    plus_di = adx_indicator.adx_pos().iloc[-1]
    minus_di = adx_indicator.adx_neg().iloc[-1]

    adx = 0 if pd.isna(adx) else float(adx)
    plus_di = 0 if pd.isna(plus_di) else float(plus_di)
    minus_di = 0 if pd.isna(minus_di) else float(minus_di)

    print(
        f"{ticker} | Price={current_price:.2f} | MA20={ma20:.2f} | "
        f"AvgVol={avg_volume:,.0f} | VolRatio={volume_ratio:.2f}"
    )
        
    return {
        "Ticker": ticker,
        "Price": current_price,
        "RSI": rsi,
        "VolumeRatio": volume_ratio,
        "MA20": ma20,
        "MA50": ma50,
        "MA200": ma200,
        "AvgVolume": avg_volume,
        "MACD": macd_line,
        "SignalLine": signal_line,
        "MiddleBB": middle_band,
        "UpperBB": upper_band,
        "RelativeStrength": float(relative_strength),
        "ADX": adx,
        "PlusDI": plus_di,
        "MinusDI": minus_di,
    }
    
