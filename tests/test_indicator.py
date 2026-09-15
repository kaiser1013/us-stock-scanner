from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

import scanner.indicator as indicator


SPY_RETURNS = {
    21: 2.0,
    63: 5.0,
    126: 8.0,
    252: 12.0,
}


def create_ohlcv_dataframe(
    periods=320,
    start_price=100.0,
    daily_change=0.25,
    base_volume=1_000_000,
):
    """Create deterministic OHLCV data for indicator tests."""

    dates = pd.date_range(
        "2024-01-02",
        periods=periods,
        freq="B",
    )

    close = np.array(
        [
            start_price + daily_change * index
            for index in range(periods)
        ],
        dtype=float,
    )

    open_price = close - 0.25
    high = close + 1.0
    low = close - 1.0

    volume = np.array(
        [
            base_volume + index * 1_000
            for index in range(periods)
        ],
        dtype=float,
    )

    return pd.DataFrame(
        {
            "Open": open_price,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        },
        index=dates,
    )


def create_declining_dataframe(
    periods=320,
    start_price=300.0,
    daily_change=0.25,
    base_volume=1_000_000,
):
    """Create deterministic declining OHLCV data."""

    dates = pd.date_range(
        "2024-01-02",
        periods=periods,
        freq="B",
    )

    close = np.array(
        [
            start_price - daily_change * index
            for index in range(periods)
        ],
        dtype=float,
    )

    volume = np.array(
        [
            base_volume + index * 1_000
            for index in range(periods)
        ],
        dtype=float,
    )

    return pd.DataFrame(
        {
            "Open": close + 0.25,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": volume,
        },
        index=dates,
    )


def create_variable_dataframe(
    periods=320,
    base_price=100.0,
    base_volume=1_000_000,
):
    """Create non-linear OHLCV data suitable for technical indicators."""

    dates = pd.date_range(
        "2024-01-02",
        periods=periods,
        freq="B",
    )

    index_values = np.arange(periods, dtype=float)

    close = (
        base_price
        + index_values * 0.20
        + np.sin(index_values / 5.0) * 2.0
    )

    high = close + 1.5
    low = close - 1.5
    open_price = close - 0.20

    volume = (
        base_volume
        + index_values * 1_000
        + np.cos(index_values / 7.0) * 50_000
    )

    return pd.DataFrame(
        {
            "Open": open_price,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        },
        index=dates,
    )


def call_calculate_indicators(
    dataframe,
    spy_returns=None,
):
    """Call calculate_indicators using the current scanner interface."""

    benchmark_returns = (
        SPY_RETURNS
        if spy_returns is None
        else spy_returns
    )

    return indicator.calculate_indicators(
        "TEST",
        dataframe,
        benchmark_returns,
    )


# ============================================================
# Index-date normalisation
# ============================================================


def test_normalise_index_date_returns_date():
    timestamp = pd.Timestamp("2026-09-10")

    result = indicator._normalise_index_date(timestamp)

    assert result == timestamp.date()


def test_normalise_index_date_converts_timezone():
    timestamp = pd.Timestamp(
        "2026-09-11 01:00:00",
        tz="UTC",
    )

    result = indicator._normalise_index_date(timestamp)

    assert result.isoformat() == "2026-09-10"


# ============================================================
# Completed-session Volume Engine
# ============================================================


def test_before_market_data_ready_uses_previous_session():
    dataframe = create_ohlcv_dataframe(periods=30)

    current_time = datetime(
        2024,
        2,
        12,
        15,
        30,
        tzinfo=ZoneInfo("America/New_York"),
    )

    assert dataframe.index[-1].date() == current_time.date()

    selected_index, source = (
        indicator.select_completed_volume_index(
            dataframe,
            now=current_time,
        )
    )

    assert selected_index == -2
    assert source == "Previous completed session"


def test_after_market_data_ready_uses_latest_session():
    dataframe = create_ohlcv_dataframe(periods=30)

    current_time = datetime(
        2024,
        2,
        12,
        16,
        30,
        tzinfo=ZoneInfo("America/New_York"),
    )

    assert dataframe.index[-1].date() == current_time.date()

    selected_index, source = (
        indicator.select_completed_volume_index(
            dataframe,
            now=current_time,
        )
    )

    assert selected_index == -1
    assert source == "Latest completed session"


def test_historical_latest_bar_is_completed():
    dataframe = create_ohlcv_dataframe(periods=30)

    current_time = datetime(
        2026,
        9,
        10,
        15,
        30,
        tzinfo=ZoneInfo("America/New_York"),
    )

    selected_index, source = (
        indicator.select_completed_volume_index(
            dataframe,
            now=current_time,
        )
    )

    assert selected_index == -1
    assert source == "Latest completed session"


def test_naive_datetime_is_treated_as_new_york_time():
    dataframe = create_ohlcv_dataframe(periods=30)

    current_time = datetime(
        2024,
        2,
        12,
        15,
        30,
    )

    selected_index, source = (
        indicator.select_completed_volume_index(
            dataframe,
            now=current_time,
        )
    )

    assert selected_index == -2
    assert source == "Previous completed session"


def test_weekend_uses_latest_completed_session():
    dataframe = create_ohlcv_dataframe(periods=30)

    current_time = datetime(
        2024,
        2,
        17,
        12,
        0,
        tzinfo=ZoneInfo("America/New_York"),
    )

    selected_index, source = (
        indicator.select_completed_volume_index(
            dataframe,
            now=current_time,
        )
    )

    assert selected_index == -1
    assert source == "Latest completed session"


def test_volume_selection_requires_minimum_history():
    dataframe = create_ohlcv_dataframe(
        periods=indicator.VOLUME_LOOKBACK + 1,
    )

    with pytest.raises(
        ValueError,
        match="Insufficient data",
    ):
        indicator.select_completed_volume_index(dataframe)


def test_volume_index_returns_expected_types():
    dataframe = create_ohlcv_dataframe(periods=30)

    selected_index, source = (
        indicator.select_completed_volume_index(dataframe)
    )

    assert isinstance(selected_index, int)
    assert isinstance(source, str)


# ============================================================
# Volume metric calculation
# ============================================================


def test_calculate_volume_metrics_returns_required_fields():
    dataframe = create_ohlcv_dataframe(periods=30)

    result = indicator.calculate_volume_metrics(dataframe)

    expected_fields = {
        "LastVolume",
        "AvgVolume",
        "VolumeSource",
        "VolumeRatio",
        "RelativeVolumeLatest",
        "RelativeVolumePrevious",
    }

    assert expected_fields == set(result)


def test_volume_metrics_use_latest_completed_session():
    dataframe = create_ohlcv_dataframe(periods=30)

    current_time = datetime(
        2024,
        2,
        12,
        16,
        30,
        tzinfo=ZoneInfo("America/New_York"),
    )

    result = indicator.calculate_volume_metrics(
        dataframe,
        now=current_time,
    )

    expected_average = int(
        dataframe["Volume"].iloc[-21:-1].mean()
    )
    expected_latest = int(dataframe["Volume"].iloc[-1])

    assert result["LastVolume"] == expected_latest
    assert result["AvgVolume"] == expected_average
    assert result["VolumeSource"] == "Latest completed session"
    assert result["VolumeRatio"] == pytest.approx(
        round(expected_latest / expected_average, 2)
    )


def test_volume_metrics_use_previous_completed_session():
    dataframe = create_ohlcv_dataframe(periods=30)

    current_time = datetime(
        2024,
        2,
        12,
        15,
        30,
        tzinfo=ZoneInfo("America/New_York"),
    )

    result = indicator.calculate_volume_metrics(
        dataframe,
        now=current_time,
    )

    expected_average = int(
        dataframe["Volume"].iloc[-22:-2].mean()
    )
    expected_selected = int(dataframe["Volume"].iloc[-2])

    assert result["LastVolume"] == expected_selected
    assert result["AvgVolume"] == expected_average
    assert result["VolumeSource"] == "Previous completed session"
    assert result["VolumeRatio"] == pytest.approx(
        round(expected_selected / expected_average, 2)
    )


def test_relative_volume_latest_uses_latest_raw_volume():
    dataframe = create_ohlcv_dataframe(periods=30)
    dataframe.loc[dataframe.index[-1], "Volume"] = 5_000_000

    current_time = datetime(
        2024,
        2,
        12,
        15,
        30,
        tzinfo=ZoneInfo("America/New_York"),
    )

    result = indicator.calculate_volume_metrics(
        dataframe,
        now=current_time,
    )

    assert result["RelativeVolumeLatest"] > 1.0
    assert result["LastVolume"] == int(
        dataframe["Volume"].iloc[-2]
    )


def test_volume_metrics_return_expected_types():
    dataframe = create_ohlcv_dataframe(periods=30)

    result = indicator.calculate_volume_metrics(dataframe)

    assert isinstance(result["LastVolume"], int)
    assert isinstance(result["AvgVolume"], int)
    assert isinstance(result["VolumeSource"], str)
    assert isinstance(result["VolumeRatio"], float)
    assert isinstance(result["RelativeVolumeLatest"], float)
    assert isinstance(result["RelativeVolumePrevious"], float)


def test_volume_metrics_reject_zero_average_volume():
    dataframe = create_ohlcv_dataframe(periods=30)
    dataframe["Volume"] = 0.0

    with pytest.raises(
        ValueError,
        match="Average volume is invalid",
    ):
        indicator.calculate_volume_metrics(dataframe)


def test_volume_metrics_reject_nan_average_volume():
    dataframe = create_ohlcv_dataframe(periods=30)
    dataframe["Volume"] = np.nan

    with pytest.raises(
        ValueError,
        match="Average volume is invalid",
    ):
        indicator.calculate_volume_metrics(dataframe)


def test_volume_metrics_reject_missing_volume_column():
    dataframe = create_ohlcv_dataframe(periods=30)
    dataframe = dataframe.drop(columns=["Volume"])

    with pytest.raises(KeyError):
        indicator.calculate_volume_metrics(dataframe)


# ============================================================
# Period return calculation
# ============================================================


def test_calculate_period_return_matches_manual_result():
    close = pd.Series(
        [
            100.0,
            105.0,
            110.0,
            121.0,
        ]
    )

    result = indicator.calculate_period_return(
        close,
        sessions=3,
    )

    assert result == pytest.approx(21.0)


def test_calculate_period_return_can_be_negative():
    close = pd.Series(
        [
            100.0,
            95.0,
            90.0,
        ]
    )

    result = indicator.calculate_period_return(
        close,
        sessions=2,
    )

    assert result == pytest.approx(-10.0)


def test_calculate_period_return_requires_history():
    close = pd.Series([100.0, 101.0])

    with pytest.raises(
        ValueError,
        match="Insufficient history",
    ):
        indicator.calculate_period_return(
            close,
            sessions=2,
        )


# ============================================================
# Relative Strength calculation
# ============================================================


def test_relative_strength_returns_required_fields():
    dataframe = create_ohlcv_dataframe()

    result = indicator.calculate_relative_strength_metrics(
        dataframe["Close"],
        SPY_RETURNS,
    )

    expected_fields = {
        "RS21",
        "RS63",
        "RS126",
        "RS252",
        "RSComposite",
    }

    assert expected_fields == set(result)


def test_relative_strength_values_are_floats():
    dataframe = create_ohlcv_dataframe()

    result = indicator.calculate_relative_strength_metrics(
        dataframe["Close"],
        SPY_RETURNS,
    )

    for value in result.values():
        assert isinstance(value, float)
        assert np.isfinite(value)


def test_relative_strength_equals_stock_return_minus_benchmark():
    dataframe = create_ohlcv_dataframe()
    close = dataframe["Close"]

    result = indicator.calculate_relative_strength_metrics(
        close,
        SPY_RETURNS,
    )

    expected_rs63 = (
        indicator.calculate_period_return(close, 63)
        - SPY_RETURNS[63]
    )

    assert result["RS63"] == pytest.approx(expected_rs63)


def test_rs_composite_uses_production_weights():
    dataframe = create_ohlcv_dataframe()

    result = indicator.calculate_relative_strength_metrics(
        dataframe["Close"],
        SPY_RETURNS,
    )

    expected_composite = (
        result["RS21"] * 0.15
        + result["RS63"] * 0.50
        + result["RS126"] * 0.25
        + result["RS252"] * 0.10
    )

    assert result["RSComposite"] == pytest.approx(
        expected_composite,
        rel=1e-9,
    )


def test_rs_composite_matches_configured_weights():
    dataframe = create_ohlcv_dataframe()

    result = indicator.calculate_relative_strength_metrics(
        dataframe["Close"],
        SPY_RETURNS,
    )

    expected_composite = sum(
        result[f"RS{lookback}"]
        * indicator.RS_COMPOSITE_WEIGHTS[lookback]
        for lookback in indicator.RS_LOOKBACKS
    )

    assert result["RSComposite"] == pytest.approx(
        expected_composite
    )


def test_positive_stock_trend_produces_positive_rs():
    dataframe = create_ohlcv_dataframe(
        daily_change=0.50,
    )

    zero_benchmark = {
        21: 0.0,
        63: 0.0,
        126: 0.0,
        252: 0.0,
    }

    result = indicator.calculate_relative_strength_metrics(
        dataframe["Close"],
        zero_benchmark,
    )

    assert result["RS21"] > 0
    assert result["RS63"] > 0
    assert result["RS126"] > 0
    assert result["RS252"] > 0
    assert result["RSComposite"] > 0


def test_declining_stock_produces_negative_rs():
    dataframe = create_declining_dataframe()

    zero_benchmark = {
        21: 0.0,
        63: 0.0,
        126: 0.0,
        252: 0.0,
    }

    result = indicator.calculate_relative_strength_metrics(
        dataframe["Close"],
        zero_benchmark,
    )

    assert result["RS21"] < 0
    assert result["RS63"] < 0
    assert result["RS126"] < 0
    assert result["RS252"] < 0
    assert result["RSComposite"] < 0


def test_stronger_benchmark_reduces_relative_strength():
    dataframe = create_ohlcv_dataframe()

    zero_benchmark = {
        21: 0.0,
        63: 0.0,
        126: 0.0,
        252: 0.0,
    }

    strong_benchmark = {
        21: 20.0,
        63: 20.0,
        126: 20.0,
        252: 20.0,
    }

    zero_result = (
        indicator.calculate_relative_strength_metrics(
            dataframe["Close"],
            zero_benchmark,
        )
    )
    strong_result = (
        indicator.calculate_relative_strength_metrics(
            dataframe["Close"],
            strong_benchmark,
        )
    )

    assert (
        zero_result["RSComposite"]
        > strong_result["RSComposite"]
    )


def test_relative_strength_rejects_missing_benchmark_return():
    dataframe = create_ohlcv_dataframe()

    incomplete_benchmark = {
        21: 2.0,
        63: 5.0,
        126: 8.0,
    }

    with pytest.raises(
        ValueError,
        match="Missing benchmark returns",
    ):
        indicator.calculate_relative_strength_metrics(
            dataframe["Close"],
            incomplete_benchmark,
        )


def test_relative_strength_requires_253_prices():
    dataframe = create_ohlcv_dataframe(periods=252)

    with pytest.raises(
        ValueError,
        match="Insufficient history",
    ):
        indicator.calculate_relative_strength_metrics(
            dataframe["Close"],
            SPY_RETURNS,
        )


# ============================================================
# Full indicator calculation
# ============================================================


def test_calculate_indicators_returns_dictionary():
    dataframe = create_variable_dataframe()

    result = call_calculate_indicators(dataframe)

    assert isinstance(result, dict)


def test_calculate_indicators_returns_required_fields():
    dataframe = create_variable_dataframe()

    result = call_calculate_indicators(dataframe)

    assert result is not None

    expected_fields = {
        "Ticker",
        "Price",
        "RSI",
        "LastVolume",
        "AvgVolume",
        "VolumeSource",
        "VolumeRatio",
        "RelativeVolumeLatest",
        "RelativeVolumePrevious",
        "MA20",
        "MA50",
        "MA200",
        "MACD",
        "SignalLine",
        "MiddleBB",
        "UpperBB",
        "RelativeStrength",
        "RS21",
        "RS63",
        "RS126",
        "RS252",
        "RSComposite",
        "ADX",
        "PlusDI",
        "MinusDI",
    }

    assert expected_fields == set(result)


def test_calculate_indicators_preserves_ticker():
    dataframe = create_variable_dataframe()

    result = indicator.calculate_indicators(
        "AAPL",
        dataframe,
        SPY_RETURNS,
    )

    assert result is not None
    assert result["Ticker"] == "AAPL"


def test_price_equals_latest_close():
    dataframe = create_variable_dataframe()

    result = call_calculate_indicators(dataframe)

    assert result is not None
    assert result["Price"] == pytest.approx(
        dataframe["Close"].iloc[-1]
    )


def test_ma20_matches_manual_calculation():
    dataframe = create_variable_dataframe()

    result = call_calculate_indicators(dataframe)

    expected = dataframe["Close"].rolling(20).mean().iloc[-1]

    assert result is not None
    assert result["MA20"] == pytest.approx(expected)


def test_ma50_matches_manual_calculation():
    dataframe = create_variable_dataframe()

    result = call_calculate_indicators(dataframe)

    expected = dataframe["Close"].rolling(50).mean().iloc[-1]

    assert result is not None
    assert result["MA50"] == pytest.approx(expected)


def test_ma200_matches_manual_calculation():
    dataframe = create_variable_dataframe()

    result = call_calculate_indicators(dataframe)

    expected = dataframe["Close"].rolling(200).mean().iloc[-1]

    assert result is not None
    assert result["MA200"] == pytest.approx(expected)


def test_uptrend_has_ordered_moving_averages():
    dataframe = create_ohlcv_dataframe(
        daily_change=0.50,
    )

    result = call_calculate_indicators(dataframe)

    assert result is not None
    assert result["Price"] > result["MA20"]
    assert result["MA20"] > result["MA50"]
    assert result["MA50"] > result["MA200"]


def test_downtrend_has_reverse_moving_averages():
    dataframe = create_declining_dataframe()

    result = call_calculate_indicators(dataframe)

    assert result is not None
    assert result["Price"] < result["MA20"]
    assert result["MA20"] < result["MA50"]
    assert result["MA50"] < result["MA200"]


def test_rsi_is_within_valid_range():
    dataframe = create_variable_dataframe()

    result = call_calculate_indicators(dataframe)

    assert result is not None
    assert 0 <= result["RSI"] <= 100


def test_macd_values_are_finite():
    dataframe = create_variable_dataframe()

    result = call_calculate_indicators(dataframe)

    assert result is not None
    assert np.isfinite(result["MACD"])
    assert np.isfinite(result["SignalLine"])


def test_bollinger_values_are_finite():
    dataframe = create_variable_dataframe()

    result = call_calculate_indicators(dataframe)

    assert result is not None
    assert np.isfinite(result["MiddleBB"])
    assert np.isfinite(result["UpperBB"])
    assert result["UpperBB"] >= result["MiddleBB"]


def test_bollinger_middle_band_matches_ma20():
    dataframe = create_variable_dataframe()

    result = call_calculate_indicators(dataframe)

    assert result is not None
    assert result["MiddleBB"] == pytest.approx(
        result["MA20"],
        rel=1e-9,
    )


def test_adx_values_are_non_negative():
    dataframe = create_variable_dataframe()

    result = call_calculate_indicators(dataframe)

    assert result is not None
    assert result["ADX"] >= 0
    assert result["PlusDI"] >= 0
    assert result["MinusDI"] >= 0


def test_full_result_relative_strength_alias_equals_rs63():
    dataframe = create_variable_dataframe()

    result = call_calculate_indicators(dataframe)

    assert result is not None
    assert result["RelativeStrength"] == pytest.approx(
        result["RS63"]
    )


def test_full_result_rs_composite_matches_production_weights():
    dataframe = create_variable_dataframe()

    result = call_calculate_indicators(dataframe)

    assert result is not None

    expected_composite = (
        result["RS21"] * 0.15
        + result["RS63"] * 0.50
        + result["RS126"] * 0.25
        + result["RS252"] * 0.10
    )

    assert result["RSComposite"] == pytest.approx(
        expected_composite
    )


def test_full_result_volume_fields_are_valid():
    dataframe = create_variable_dataframe()

    result = call_calculate_indicators(dataframe)

    assert result is not None
    assert result["LastVolume"] > 0
    assert result["AvgVolume"] > 0
    assert result["VolumeRatio"] > 0
    assert result["RelativeVolumeLatest"] > 0
    assert result["RelativeVolumePrevious"] > 0
    assert result["VolumeSource"]


def test_calculate_indicators_does_not_modify_input():
    dataframe = create_variable_dataframe()
    original = dataframe.copy(deep=True)

    call_calculate_indicators(dataframe)

    pd.testing.assert_frame_equal(
        dataframe,
        original,
    )


def test_calculate_indicators_accepts_integer_volume():
    dataframe = create_variable_dataframe()
    dataframe["Volume"] = dataframe["Volume"].astype(int)

    result = call_calculate_indicators(dataframe)

    assert result is not None
    assert result["AvgVolume"] > 0


# ============================================================
# Full indicator failure handling
# ============================================================


def test_calculate_indicators_returns_none_for_none():
    result = call_calculate_indicators(None)

    assert result is None


def test_calculate_indicators_returns_none_for_empty_dataframe():
    result = call_calculate_indicators(pd.DataFrame())

    assert result is None


def test_calculate_indicators_returns_none_without_close_column():
    dataframe = create_ohlcv_dataframe()
    dataframe = dataframe.drop(columns=["Close"])

    result = call_calculate_indicators(dataframe)

    assert result is None


def test_calculate_indicators_returns_none_when_close_is_all_nan():
    dataframe = create_ohlcv_dataframe()
    dataframe["Close"] = np.nan

    result = call_calculate_indicators(dataframe)

    assert result is None


def test_calculate_indicators_returns_none_for_short_history():
    dataframe = create_ohlcv_dataframe(periods=252)

    result = call_calculate_indicators(dataframe)

    assert result is None


def test_calculate_indicators_returns_none_for_invalid_volume():
    dataframe = create_variable_dataframe()
    dataframe["Volume"] = 0.0

    result = call_calculate_indicators(dataframe)

    assert result is None


def test_calculate_indicators_returns_none_for_missing_spy_return():
    dataframe = create_variable_dataframe()

    incomplete_benchmark = {
        21: 2.0,
        63: 5.0,
        126: 8.0,
    }

    result = call_calculate_indicators(
        dataframe,
        incomplete_benchmark,
    )

    assert result is None


def test_calculate_indicators_returns_none_for_nan_latest_close():
    dataframe = create_variable_dataframe()
    dataframe.loc[dataframe.index[-1], "Close"] = np.nan

    result = call_calculate_indicators(dataframe)

    assert result is None
