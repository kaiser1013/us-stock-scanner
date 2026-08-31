from datetime import datetime, time
from zoneinfo import ZoneInfo

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, ADXIndicator
from ta.volatility import BollingerBands

from download import safe_last

MARKET_TIMEZONE = ZoneInfo("America/New_York")
MARKET_DATA_READY_TIME = time(16, 15)
VOLUME_LOOKBACK = 20

def _normalise_index_date(index_value):
    """Return a New York calendar date from a pandas index value."""
    timestamp = pd.Timestamp(index_value)
    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_convert(MARKET_TIMEZONE)
    return timestamp.date()
    
def select_completed_volume_index(df, now=None):
    """
    Select the latest completed daily volume bar automatically.
    
    If today's daily bar exists before 16:15 New York time, it is'treated as
    intraday and the previous session is used. Otherwise the latest bar is used.
    """
    
    if len(df) < VOLUME_LOOKBACK + 2:
        raise ValueError("Insufficient data for completed-volume selection")
    
    now_ny = now or datetime.now(MARKET_TIMEZONE)
    if now_ny.tzinfo is None:
        now_ny = now_ny.replace(tzinfo=MARKET_TIMEZONE)
    else:
        now_ny = now_ny.astimezone(MARKET_TIMEZONE)
    
    latest_date = _normalise_index_date(df.index[-1])
    current_date = now_ny.date()
    
    has_intraday_daily_bar = (
        latest_date == current_date
        and now_ny.weekday() < 5
        and now_ny.time() < MARKET_DATA_READY_TIME
    )
    
    if has_intraday_daily_bar:
        return -2, "Previous completed session"
    
    return -1, "Latest completed session"
    
def calculate_volume_metrics(df, now=None):
    """Calculate v3-ready completed-session relative-volume metrics."""
    volume = df["Volume"].astype(float)
    selected_position, volume_source = select_completed_volume_index(df, now=now)
    
    selected_absolute_position = len(volume) + selected_position
    if selected_absolute_position < VOLUME_LOOKBACK:
        raise ValueError("Insufficient history for 20-session average volume")
    
    historical_volume = volume.iloc[
        selected_absolute_position - VOLUME_LOOKBACK: selected_absolute_position
    ]
    avg_volume = float(historical_volume.mean())
    selected_volume = float(volume.iloc[selected_absolute_position])
    latest_raw_volume = float(volume.iloc[-1])
    previous_volume = float(volume.iloc[-2])
    
    if pd.isna(avg_volume) or avg_volume <= 0:
        raise ValueError( "Average volume is invalid")
    
    volume_ratio = selected_volume / avg_volume
    relative_volume_latest = latest_raw_volume / avg_volume
    relative_volume_previous = previous_volume / avg_volume
    
    return {
        "LastVolume": int(selected_volume),
        "AvgVolume": int(avg_volume),
        "VolumeSource": volume_source,
        "VolumeRatio": round(volume_ratio, 2),
        "RelativeVolumeLatest": round(relative_volume_latest, 2),
        "RelativeVolumePrevious": round(relative_volume_previous, 2),
    }

def calculate_indicators(ticker, df, spy_return):
    """Calculate the technical and volume metrics used by the scanner."""
    if df is None or df.empty:
        print(f"{ticker}: No data")
        return None
    if "Close" not in df.columns or df["Close"].isna().all():
        print(f"{ticker}: Close all NaN")
        return None
    if len(df) < 210:
        print(f"{ticker}: insufficient data {len(df)}")
        return None

    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    
    current_price = float(close.iloc[-1])
    ma20 = safe_last(close.rolling(20).mean())
    ma50 = safe_last(close.rolling(50).mean())
    ma200 = safe_last(close.rolling(200).mean())
    
    if ma20 is None or ma50 is None or ma200 is None:
        print(f"{ticker}: moving average NaN")
        return None

    try:
        volume_metrics = calculate_volume_metrics(df)
    except ValueError as error:
        print(f"{ticker}: {error}")
        return None

    print(
        f"{ticker} | VolumeSource={volume_metrics['VolumeSource']} | "
        f"LastVol={volume_metrics['LastVolume']:,.0f} | "
        f"AvgVol={volume_metrics['AvgVolume']:,.0f} | "
        f"VolRatio={volume_metrics['VolumeRatio']:.2f}"
    )

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

    # ==========================
    # BOLLINGER
    # ==========================
    
    bb = BollingerBands(close)
    middle_band = bb.bollinger_mavg().iloc[-1]
    upper_band = bb. bollinger_hband().iloc[-1]
    if pd.isna(middle_band) or pd.isna(upper_band):
        print(f"{ticker}: Bollinger NaN")
        return None

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

    adx = 0.0 if pd.isna(adx) else float(adx)
    plus_di = 0.0 if pd.isna(plus_di) else float(plus_di)
    minus_di = 0.0 if pd.isna(minus_di) else float(minus_di)

    print(
        f"{ticker} | Price={current_price:.2f} | MA20={ma20:.2f} | "
        f"AvgVol={volume_metrics['AvgVolume']:,.0f} | "
        f"VolRatio={volume_metrics['VolumeRatio']:.2f}"
    )
        
    return {
        "Ticker": ticker,
        "Price": current_price,
        "RSI": rsi,
        "LastVolume": volume_metrics["LastVolume"],
        "AvgVolume": volume_metrics["AvgVolume"],
        "VolumeSource": volume_metrics["VolumeSource"],
        "VolumeRatio": volume_metrics["VolumeRatio"],
        "RelativeVolumeLatest": volume_metrics["RelativeVolumeLatest"],
        "RelativeVolumePrevious": volume_metrics["RelativeVolumePrevious"],
        "MA20": ma20,
        "MA50": ma50,
        "MA200": ma200,
        "MACD": float(macd_line),
        "SignalLine": float(signal_line),
        "MiddleBB": float(middle_band),
        "UpperBB": float(upper_band),
        "RelativeStrength": float(relative_strength),
        "ADX": adx,
        "PlusDI": plus_di,
        "MinusDI": minus_di
    }
    