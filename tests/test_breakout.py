import math

import pandas as pd
import pytest

from scanner.indicator import BREAKOUT_LOOKBACK, calculate_breakout_metrics
from scanner.scanner import rank_results


def make_price_series(
    prior_high=100.0,
    latest_close=101.0,
    latest_high=102.0,
    lookback=BREAKOUT_LOOKBACK,
):
    """Create close and high series with a controlled prior breakout level."""
    index = pd.RangeIndex(lookback + 1)
    
    filler_high = prior_high - max(
        abs(prior_high) * 0.05,
        1.0,
    )

    close = pd.Series(
        [filler_high] * lookback + [latest_close],
        index=index,
        dtype=float,
    )
    
    high = pd.Series(
        [filler_high] * (lookback - 1) + [prior_high, latest_high],
        index=index,
        dtype=float,
    )

    return close, high


def make_rank_candidate(
    ticker,
    trade_plan,
    score,
    risk_reward,
    breakout55,
    distance_to_high55,
):
    """Create the minimum candidate structure required by rank_results()."""
    return {
        "Ticker": ticker,
        "TradePlan": trade_plan,
        "Score": score,
        "RiskReward": risk_reward,
        "Breakout55": breakout55,
        "DistanceToHigh55": distance_to_high55,
    }


def test_breakout_lookback_is_55():
    assert BREAKOUT_LOOKBACK == 55


def test_breakout55_true_above_prior_high():
    close, high = make_price_series(
        prior_high=100.0,
        latest_close=101.0,
    )

    result = calculate_breakout_metrics(close, high)

    assert result["Breakout55"] is True


def test_breakout55_false_below_prior_high():
    close, high = make_price_series(
        prior_high=100.0,
        latest_close=99.0,
    )

    result = calculate_breakout_metrics(close, high)

    assert result["Breakout55"] is False


def test_breakout55_true_when_close_equals_prior_high():
    close, high = make_price_series(
        prior_high=100.0,
        latest_close=100.0,
    )

    result = calculate_breakout_metrics(close, high)

    assert result["Breakout55"] is True
    assert result["DistanceToHigh55"] == pytest.approx(0.0)


def test_distance_to_high55_is_positive_above_prior_high():
    close, high = make_price_series(
        prior_high=100.0,
        latest_close=105.0,
    )

    result = calculate_breakout_metrics(close, high)

    assert result["DistanceToHigh55"] == pytest.approx(5.0)


def test_distance_to_high55_is_negative_below_prior_high():
    close, high = make_price_series(
        prior_high=100.0,
        latest_close=95.0,
    )

    result = calculate_breakout_metrics(close, high)

    assert result["DistanceToHigh55"] == pytest.approx(-5.0)


def test_distance_to_high55_uses_percentage_formula():
    close, high = make_price_series(
        prior_high=120.0,
        latest_close=126.0,
    )

    result = calculate_breakout_metrics(close, high)
    expected = (126.0 / 120.0 - 1.0) * 100

    assert math.isclose(
        result["DistanceToHigh55"],
        expected,
        rel_tol=1e-12,
        abs_tol=1e-12,
    )


def test_latest_high_is_excluded_from_reference_window():
    close, high = make_price_series(
        prior_high=100.0,
        latest_close=105.0,
        latest_high=500.0,
    )

    result = calculate_breakout_metrics(close, high)

    assert result["Breakout55"] is True
    assert result["DistanceToHigh55"] == pytest.approx(5.0)


def test_only_prior_lookback_sessions_are_used():
    lookback = 55
    close = pd.Series([90.0] * (lookback + 2), dtype=float)
    high = pd.Series(
        [500.0] + [95.0] * (lookback - 1) + [100.0, 101.0],
        dtype=float,
    )
    close.iloc[-1] = 105.0

    result = calculate_breakout_metrics(close, high, lookback=lookback)

    assert result["Breakout55"] is True
    assert result["DistanceToHigh55"] == pytest.approx(5.0)


def test_breakout_metrics_return_expected_fields_and_types():
    close, high = make_price_series()

    result = calculate_breakout_metrics(close, high)

    assert set(result) == {
        "Breakout55",
        "DistanceToHigh55",
    }
    assert isinstance(result["Breakout55"], bool)
    assert isinstance(result["DistanceToHigh55"], float)


def test_breakout_rejects_short_close_history():
    close = pd.Series([90.0] * BREAKOUT_LOOKBACK, dtype=float)
    high = pd.Series([95.0] * (BREAKOUT_LOOKBACK + 1), dtype=float)

    with pytest.raises(
        ValueError,
        match="Insufficient history",
    ):
        calculate_breakout_metrics(close, high)


def test_breakout_rejects_short_high_history():
    close = pd.Series([90.0] * (BREAKOUT_LOOKBACK + 1), dtype=float)
    high = pd.Series([95.0] * BREAKOUT_LOOKBACK, dtype=float)

    with pytest.raises(
        ValueError,
        match="Insufficient history",
    ):
        calculate_breakout_metrics(close, high)


@pytest.mark.parametrize("lookback", [0, -1, -55])
def test_breakout_rejects_non_positive_lookback(lookback):
    close, high = make_price_series()

    with pytest.raises(
        ValueError,
        match="Breakout lookback must be positive",
    ):
        calculate_breakout_metrics(
            close,
            high,
            lookback=lookback,
        )


def test_breakout_rejects_nan_latest_close():
    close, high = make_price_series()
    close.iloc[-1] = float("nan")

    with pytest.raises(
        ValueError,
        match="Breakout reference price is invalid",
    ):
        calculate_breakout_metrics(close, high)


def test_breakout_rejects_nan_prior_high_window():
    close, high = make_price_series()
    high.iloc[:-1] = float("nan")

    with pytest.raises(
        ValueError,
        match="Breakout reference price is invalid",
    ):
        calculate_breakout_metrics(close, high)


def test_breakout_rejects_zero_prior_high():
    close, high = make_price_series(
        prior_high=0.0,
        latest_close=1.0,
    )
    high.iloc[:-1] = 0.0

    with pytest.raises(
        ValueError,
        match="Breakout reference price is invalid",
    ):
        calculate_breakout_metrics(close, high)


def test_breakout_rejects_negative_prior_high():
    close, high = make_price_series(
        prior_high=-1.0,
        latest_close=1.0,
    )
    high.iloc[:-1] = -1.0

    with pytest.raises(
        ValueError,
        match="Breakout reference price is invalid",
    ):
        calculate_breakout_metrics(close, high)


def test_custom_lookback_is_supported():
    close, high = make_price_series(
        prior_high=50.0,
        latest_close=52.5,
        lookback=10,
    )

    result = calculate_breakout_metrics(
        close,
        high,
        lookback=10,
    )

    assert result["Breakout55"] is True
    assert result["DistanceToHigh55"] == pytest.approx(5.0)

def test_breakout_fields_do_not_change_score_order():

    candidates = [
        make_rank_candidate(
            ticker="LOW_SCORE_BREAKOUT",
            trade_plan="PASS",
            score=80,
            risk_reward=3.0,
            breakout55=True,
            distance_to_high55=20.0,
        ),
        make_rank_candidate(
            ticker="HIGH_SCORE_NON_BREAKOUT",
            trade_plan="PASS",
            score=90,
            risk_reward=1.0,
            breakout55=False,
            distance_to_high55=-5.0,
        ),
    ]

    ranked = rank_results(candidates)

    assert ranked.iloc[0]["Ticker"] == "HIGH_SCORE_NON_BREAKOUT"
    assert ranked.iloc[1]["Ticker"] == "LOW_SCORE_BREAKOUT"
    
def test_breakout_columns_preserved_after_ranking():
    
    candidates = [
        make_rank_candidate(
            ticker="AAA",
            trade_plan="PASS",
            score=80,
            risk_reward=3.0,
            breakout55=True,
            distance_to_high55=10.0,
        ),
    ]
    
    ranked = rank_results(candidates)
    
    assert "Breakout55" in ranked.columns
    assert "DistanceToHigh55" in ranked.columns
    
    assert bool(ranked.iloc[0]["Breakout55"]) is True
    assert ranked.iloc[0]["DistanceToHigh55"] == 10.0
