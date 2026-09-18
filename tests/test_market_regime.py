from collections import Counter

import pandas as pd
import pytest

from scanner.download import (
    REGIME_NEUTRAL_BAND,
    REGIME_SCORES,
    classify_market_regime,
)

from scanner.scanner import (
    build_email_body,
    build_report_frames,
)


# ==========================================================
# Regime Classification
# ==========================================================

def test_bull_regime():
    assert classify_market_regime(
        spy_price=104,
        spy_ma200=100,
    ) == "BULL"


def test_neutral_regime():
    assert classify_market_regime(
        spy_price=101,
        spy_ma200=100,
    ) == "NEUTRAL"


def test_bear_regime():
    assert classify_market_regime(
        spy_price=96,
        spy_ma200=100,
    ) == "BEAR"


# ==========================================================
# Regime Score Validation
# ==========================================================

def test_regime_score_bull():
    assert REGIME_SCORES["BULL"] == 15


def test_regime_score_neutral():
    assert REGIME_SCORES["NEUTRAL"] == 7


def test_regime_score_bear():
    assert REGIME_SCORES["BEAR"] == 0


def test_neutral_band_default():
    assert REGIME_NEUTRAL_BAND == 0.03


# ==========================================================
# Boundary Validation
# ==========================================================

def test_upper_boundary_is_neutral():
    assert (
        classify_market_regime(
            spy_price=103.0,
            spy_ma200=100.0,
        )
        == "NEUTRAL"
    )


def test_above_upper_boundary_is_bull():
    assert (
        classify_market_regime(
            spy_price=103.01,
            spy_ma200=100.0,
        )
        == "BULL"
    )


def test_lower_boundary_is_neutral():
    assert (
        classify_market_regime(
            spy_price=97.0,
            spy_ma200=100.0,
        )
        == "NEUTRAL"
    )


def test_below_lower_boundary_is_bear():
    assert (
        classify_market_regime(
            spy_price=96.99,
            spy_ma200=100.0,
        )
        == "BEAR"
    )


# ==========================================================
# Error Handling
# ==========================================================

def test_invalid_ma200():
    with pytest.raises(ValueError):
        classify_market_regime(
            spy_price=100,
            spy_ma200=0,
        )


# ==========================================================
# Report Summary Validation
# ==========================================================

def test_summary_contains_market_regime():

    frames = build_report_frames(
        top20=pd.DataFrame(),
        total_scanned=100,
        status_counts=Counter({"Passed": 10}),
        rejection_counts=Counter(),
        all_failure_counts=Counter(),
        breadth_counts=Counter(),
        market_bull=True,
        spy_price=500,
        spy_ma200=450,
        market_regime="NEUTRAL",
    )

    summary_df = frames[1]

    regime_row = summary_df.loc[
        summary_df["Metric"] == "Market Regime"
    ]

    score_row = summary_df.loc[
        summary_df["Metric"] == "Regime Score"
    ]

    assert regime_row.iloc[0]["Value"] == "NEUTRAL"
    assert score_row.iloc[0]["Value"] == 7


# ==========================================================
# Email Validation
# ==========================================================

def test_email_contains_market_regime():

    body = build_email_body(
        top20=pd.DataFrame(),
        total_scanned=100,
        status_counts=Counter({"Passed": 5}),
        rejection_counts=Counter(),
        breadth_counts=Counter(),
        market_bull=True,
        spy_price=500,
        spy_ma200=450,
        market_regime="BULL",
    )

    assert "Market Regime" in body
    assert "BULL" in body
    assert "Regime Score" in body
    assert "15" in body


def test_email_contains_neutral_regime():

    body = build_email_body(
        top20=pd.DataFrame(),
        total_scanned=100,
        status_counts=Counter(),
        rejection_counts=Counter(),
        breadth_counts=Counter(),
        market_bull=True,
        spy_price=500,
        spy_ma200=450,
        market_regime="NEUTRAL",
    )

    assert "NEUTRAL" in body
    assert "Regime Score: 7" in body


def test_email_contains_bear_regime():

    body = build_email_body(
        top20=pd.DataFrame(),
        total_scanned=100,
        status_counts=Counter(),
        rejection_counts=Counter(),
        breadth_counts=Counter(),
        market_bull=False,
        spy_price=400,
        spy_ma200=450,
        market_regime="BEAR",
    )

    assert "BEAR" in body
    assert "Regime Score: 0" in body


# ==========================================================
# Empty Top20 Regression
# ==========================================================

def test_empty_top20_has_regime_columns():

    frames = build_report_frames(
        top20=pd.DataFrame(),
        total_scanned=0,
        status_counts=Counter(),
        rejection_counts=Counter(),
        all_failure_counts=Counter(),
        breadth_counts=Counter(),
        market_bull=True,
        spy_price=500,
        spy_ma200=450,
        market_regime="BULL",
    )

    top20 = frames[0]

    assert "MarketRegime" in top20.columns
    assert "RegimeScore" in top20.columns
