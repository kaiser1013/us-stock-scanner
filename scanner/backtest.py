from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd


@dataclass
class Trade:
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    symbol: str
    entry_price: float
    exit_price: float
    return_pct: float


@dataclass
class BacktestResult:
    trades: List[Trade]
    equity_curve: pd.Series
    metrics: Dict[str, float]


def calculate_trade_return(
    entry_price: float,
    exit_price: float,
) -> float:
    return (exit_price / entry_price - 1.0) * 100.0


def calculate_max_drawdown(
    equity_curve: pd.Series,
) -> float:
    running_max = equity_curve.cummax()
    drawdown = equity_curve / running_max - 1.0
    return float(drawdown.min() * 100.0)


def calculate_cagr(
    equity_curve: pd.Series,
) -> float:
    years = len(equity_curve) / 252

    if years <= 0:
        return 0.0

    start = float(equity_curve.iloc[0])
    end = float(equity_curve.iloc[-1])

    return ((end / start) ** (1 / years) - 1) * 100


def calculate_sharpe_ratio(
    returns: pd.Series,
) -> float:
    if returns.std() == 0:
        return 0.0

    return float(
        np.sqrt(252) * returns.mean() / returns.std()
    )


def calculate_sortino_ratio(
    returns: pd.Series,
) -> float:
    downside = returns[returns < 0]

    if len(downside) == 0:
        return 0.0

    downside_std = downside.std()

    if downside_std == 0:
        return 0.0

    return float(
        np.sqrt(252) * returns.mean() / downside_std
    )


def calculate_profit_factor(
    trade_returns: pd.Series,
) -> float:
    gains = trade_returns[trade_returns > 0].sum()
    losses = abs(
        trade_returns[trade_returns < 0].sum()
    )

    if losses == 0:
        return 0.0

    return float(gains / losses)


def calculate_expectancy(
    trade_returns: pd.Series,
) -> float:
    if len(trade_returns) == 0:
        return 0.0

    winners = trade_returns[trade_returns > 0]
    losers = trade_returns[trade_returns < 0]

    win_rate = len(winners) / len(trade_returns)

    avg_win = winners.mean() if len(winners) else 0
    avg_loss = abs(losers.mean()) if len(losers) else 0

    return float(
        (win_rate * avg_win)
        - ((1 - win_rate) * avg_loss)
    )


def build_metrics(
    equity_curve: pd.Series,
    trade_returns: pd.Series,
    benchmark_return: float = 0.0,
) -> Dict[str, float]:

    daily_returns = equity_curve.pct_change().dropna()

    total_return = (
        equity_curve.iloc[-1]
        / equity_curve.iloc[0]
        - 1
    ) * 100

    return {
        "WinRate": float(
            (trade_returns > 0).mean() * 100
        ),
        "AverageGain": float(
            trade_returns[trade_returns > 0].mean()
        )
        if (trade_returns > 0).any()
        else 0.0,
        "AverageLoss": float(
            trade_returns[trade_returns < 0].mean()
        )
        if (trade_returns < 0).any()
        else 0.0,
        "ProfitFactor": calculate_profit_factor(
            trade_returns
        ),
        "Expectancy": calculate_expectancy(
            trade_returns
        ),
        "TotalReturn": float(total_return),
        "CAGR": calculate_cagr(
            equity_curve
        ),
        "SharpeRatio": calculate_sharpe_ratio(
            daily_returns
        ),
        "SortinoRatio": calculate_sortino_ratio(
            daily_returns
        ),
        "MaxDrawdown": calculate_max_drawdown(
            equity_curve
        ),
        "BenchmarkReturn": benchmark_return,
        "Alpha": float(
            total_return - benchmark_return
        ),
    }
