from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from scanner.indicator import (
    select_completed_volume_index,
)


def create_sample_volume_df():
    """
    Create 40 business-day sample volume history.
    """
    
    dates = pd.date_range(
        "2026-01-01",
        periods=40,
        freq="B",
    )
    
    return pd.DataFrame(
        {
            "Volume": range(40)
        },
        index=dates,
    )
    
def test_before_cutoff_uses_previous_session():
    """
    Before 16:15 NY time the scanner
    should use the previous completed session.
    """
    
    df = create_sample_volume_df()
    
    latest_day = df.index[-1]
    
    now = datetime(
        latest_day.year,
        latest_day.month,
        latest_day.day,
        15,
        0,
        tzinfo=ZoneInfo(
            "America/New_York"
        ),
    )
    
    position, source = (
        select_completed_volume_index(
            df,
            now=now,
        )
    )
    
    assert position == -2
    
    assert (
        source
        == "Previous completed session"
    )
    
def test_after_cutoff_uses_latest_session():
    """
    After 16:15 NY time the scanner
    should use latest completed session.
    """
    
    df = create_sample_volume_df()
    
    latest_day = df.index[-1]
    
    now = datetime(
        latest_day.year,
        latest_day.month,
        latest_day.day,
        16,
        30,
        tzinfo=ZoneInfo(
            "America/New_York"
        ),
    )
    
    position, source = (
        select_completed_volume_index(
            df,
            now=now,
        )
    )
    
    assert position == -1
    
    assert (
        source
        == "Latest completed session"
    )
    
def test_after_market_close_uses_latest():
    """
    Evening run should use
    latest completed session.
    """
    
    df = create_sample_volume_df()
    
    latest_day = df.index[-1]
    
    now = datetime(
        latest_day.year,
        latest_day.month,
        latest_day.day,
        20,
        0,
        tzinfo=ZoneInfo(
            "America/New_York"
        ),
    )
    position, source = (
        select_completed_volume_index(
            df,
            now=now,
        )
    )
    
    assert position == -1
    assert source == "Latest completed session"
    
def test_return_types():
    """
    Ensure output types remain stable.
    """
    
    df = create_sample_volume_df()
    
    latest_day = df.index[-1]
    
    now = datetime(
        latest_day.year,
        latest_day.month,
        latest_day.day,
        16,
        30,
        tzinfo=ZoneInfo(
            "America/New_York"
        ),
    )
    
    position, source = (
        select_completed_volume_index(
            df,
            now=now,
        )
    )
    
    assert isinstance(position, int)
    assert isinstance(source, str)
