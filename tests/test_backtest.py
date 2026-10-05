import pytest
import pandas as pd

from scanner.backtest import (
    calculate_trade_return,
    calculate_max_drawdown,
    calculate_profit_factor,
    calculate_expectancy,
    build_metrics,
)


def test_trade_return_positive():
    result = calculate_trade_return(
        100,
        120,
    )

    assert result == pytest.approx(
        20.0
    )


def test_trade_return_negative():
    result = calculate_trade_return(
        100,
        80,
    )

    assert result == pytest.approx(
        -20.0
    )


def test_max_drawdown():
    equity = pd.Series(
        [
            100,
            120,
            90,
            95,
            150,
        ]
    )

    result = calculate_max_drawdown(
        equity
    )

    assert round(result, 2) == -25.00


def test_profit_factor():
    returns = pd.Series(
        [
            10,
            -5,
            20,
            -5,
        ]
    )

    result = calculate_profit_factor(
        returns
    )

    assert result == 3.0


def test_expectancy():
    returns = pd.Series(
        [
            10,
            20,
            -5,
            -5,
        ]
    )

    result = calculate_expectancy(
        returns
    )

    assert result == 5.0


def test_build_metrics_contains_required_metrics():
    equity = pd.Series(
        [
            100000,
            101000,
            103000,
            102000,
            105000,
        ]
    )

    trades = pd.Series(
        [
            10,
            -5,
            15,
        ]
    )

    result = build_metrics(
        equity,
        trades,
        benchmark_return=8.0,
    )

    required = {
        "WinRate",
        "AverageGain",
        "AverageLoss",
        "ProfitFactor",
        "Expectancy",
        "TotalReturn",
        "CAGR",
        "SharpeRatio",
        "SortinoRatio",
        "MaxDrawdown",
        "BenchmarkReturn",
        "Alpha",
    }

    assert required.issubset(
        result.keys()
    )


def test_alpha_calculation():
    equity = pd.Series(
        [
            100,
            120,
        ]
    )

    trades = pd.Series([20])

    metrics = build_metrics(
        equity,
        trades,
        benchmark_return=10,
    )

    assert metrics["Alpha"] == pytest.approx(
        10.0
    )
