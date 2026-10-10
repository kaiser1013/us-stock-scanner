from __future__ import annotations

from typing import Any

import pandas as pd
import pytest

import scanner.replay as replay_module
from scanner.replay import (
    SIGNAL_COLUMNS,
    HistoricalSignal,
    calculate_point_in_time_benchmark_returns,
    evaluate_production_snapshot,
    generate_signal,
    historical_signal_to_dict,
    point_in_time_history,
    replay_symbol,
    replay_universe,
)


def make_history(
    *,
    periods: int = 10,
    start: str = "2024-01-01",
    base_price: float = 100.0,
    volume: int = 2_000_000,
) -> pd.DataFrame:
    dates = pd.date_range(
        start,
        periods=periods,
        freq="D",
    )

    close = pd.Series(
        [
            base_price + index
            for index in range(periods)
        ],
        index=dates,
        dtype=float,
    )

    return pd.DataFrame(
        {
            "Open": close - 0.5,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": volume,
        },
        index=dates,
    )


def make_long_history(
    *,
    periods: int = 300,
    start: str = "2023-01-01",
    base_price: float = 100.0,
    daily_increment: float = 0.25,
    volume: int = 2_000_000,
) -> pd.DataFrame:
    dates = pd.date_range(
        start,
        periods=periods,
        freq="D",
    )

    close = pd.Series(
        [
            base_price
            + index * daily_increment
            for index in range(periods)
        ],
        index=dates,
        dtype=float,
    )

    return pd.DataFrame(
        {
            "Open": close - 0.5,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": volume,
        },
        index=dates,
    )


def make_production_metrics(
    ticker: str = "AAPL",
) -> dict[str, Any]:
    return {
        "Ticker": ticker,
        "Price": 175.0,
        "RSI": 60.0,
        "LastVolume": 2_000_000,
        "AvgVolume": 1_500_000,
        "VolumeSource": (
            "Latest completed session"
        ),
        "VolumeRatio": 1.33,
        "RelativeVolumeLatest": 1.33,
        "RelativeVolumePrevious": 1.20,
        "MA20": 170.0,
        "MA50": 160.0,
        "MA200": 140.0,
        "MACD": 2.0,
        "SignalLine": 1.0,
        "MiddleBB": 170.0,
        "UpperBB": 180.0,
        "RelativeStrength": 12.0,
        "RS21": 4.0,
        "RS63": 12.0,
        "RS126": 9.0,
        "RS252": 7.0,
        "RSComposite": 9.05,
        "Breakout55": True,
        "DistanceToHigh55": 1.5,
        "ADX": 30.0,
        "PlusDI": 35.0,
        "MinusDI": 15.0,
    }


def make_score_result(
    market_regime: str = "BULL",
) -> dict[str, Any]:
    regime_scores = {
        "BULL": 15,
        "NEUTRAL": 7,
        "BEAR": 0,
    }

    regime_score = regime_scores[
        market_regime
    ]

    return {
        "Score": 84.0,
        "Signal": "簸??瞽 BUY",
        "TrendScore": 30,
        "MomentumScore": 20,
        "StrengthScore": 8,
        "VolumeScore": 10,
        "MarketRegime": market_regime,
        "RegimeScore": regime_score,
        "MarketScore": regime_score,
        "ADXScore": 6,
        "RiskPenalty": 0,
    }


def make_risk_result() -> dict[str, Any]:
    return {
        "ATR14": 2.0,
        "StopLoss": 172.0,
        "TakeProfit1": 179.5,
        "TakeProfit2": 181.0,
        "RiskPerShare": 3.0,
        "RewardPerShare": 6.0,
        "RiskReward": 2.0,
        "PositionShares": 33,
        "CapitalRequired": 5_775.0,
        "PlannedRiskAmount": 99.0,
        "TradePlan": "璽?? ACTIONABLE",
    }


def test_point_in_time_history():
    history = make_history()

    result = point_in_time_history(
        history,
        pd.Timestamp("2024-01-05"),
    )

    assert result.index.max() == pd.Timestamp(
        "2024-01-05"
    )
    assert len(result) == 5


def test_point_in_time_history_does_not_modify_input():
    history = make_history()
    original = history.copy(deep=True)

    point_in_time_history(
        history,
        pd.Timestamp("2024-01-05"),
    )

    pd.testing.assert_frame_equal(
        history,
        original,
    )


def test_point_in_time_history_sorts_index():
    history = make_history().sort_index(
        ascending=False
    )

    result = point_in_time_history(
        history,
        pd.Timestamp("2024-01-05"),
    )

    assert result.index.is_monotonic_increasing
    assert result.index.max() == pd.Timestamp(
        "2024-01-05"
    )


def test_generate_signal():
    history = make_history()

    result = generate_signal(
        ticker="AAPL",
        history=history,
        signal_date=pd.Timestamp(
            "2024-01-05"
        ),
    )

    assert result is not None
    assert result.price == pytest.approx(
        104.0
    )


def test_generate_signal_returns_none_when_no_history():
    history = make_history()

    result = generate_signal(
        ticker="AAPL",
        history=history,
        signal_date=pd.Timestamp(
            "2023-01-01"
        ),
    )

    assert result is None


def test_generate_signal_returns_historical_signal():
    history = make_history()

    result = generate_signal(
        ticker="AAPL",
        history=history,
        signal_date=pd.Timestamp(
            "2024-01-05"
        ),
    )

    assert isinstance(
        result,
        HistoricalSignal,
    )


def test_generate_signal_returns_none_without_close_column():
    history = make_history().drop(
        columns=["Close"]
    )

    result = generate_signal(
        ticker="AAPL",
        history=history,
        signal_date=pd.Timestamp(
            "2024-01-05"
        ),
    )

    assert result is None


def test_replay_symbol():
    history = make_history()

    result = replay_symbol(
        ticker="AAPL",
        history=history,
        start_date=pd.Timestamp(
            "2024-01-03"
        ),
        end_date=pd.Timestamp(
            "2024-01-05"
        ),
    )

    assert len(result) == 3


def test_replay_symbol_returns_empty_for_invalid_range():
    history = make_history()

    result = replay_symbol(
        ticker="AAPL",
        history=history,
        start_date=pd.Timestamp(
            "2024-01-05"
        ),
        end_date=pd.Timestamp(
            "2024-01-03"
        ),
    )

    assert result == []


def test_replay_universe():
    history = make_history()

    universe = {
        "AAPL": history,
        "MSFT": history,
    }

    result = replay_universe(
        universe,
        start_date=pd.Timestamp(
            "2024-01-03"
        ),
        end_date=pd.Timestamp(
            "2024-01-05"
        ),
    )

    assert len(result) == 6
    assert list(result.columns) == (
        SIGNAL_COLUMNS
    )


def test_replay_universe_is_deterministically_sorted():
    history = make_history()

    universe = {
        "MSFT": history,
        "AAPL": history,
    }

    result = replay_universe(
        universe,
        start_date=pd.Timestamp(
            "2024-01-03"
        ),
        end_date=pd.Timestamp(
            "2024-01-03"
        ),
    )

    assert result["Ticker"].tolist() == [
        "AAPL",
        "MSFT",
    ]


def test_empty_replay_universe_has_required_columns():
    result = replay_universe(
        {},
        start_date=pd.Timestamp(
            "2024-01-03"
        ),
        end_date=pd.Timestamp(
            "2024-01-05"
        ),
    )

    assert result.empty
    assert list(result.columns) == (
        SIGNAL_COLUMNS
    )


def test_signal_contains_required_fields():
    history = make_history()

    result = generate_signal(
        ticker="AAPL",
        history=history,
        signal_date=pd.Timestamp(
            "2024-01-05"
        ),
        market_regime="BULL",
        regime_score=15,
        rs_composite=10,
        breakout55=True,
    )

    assert result is not None
    assert result.market_regime == "BULL"
    assert result.regime_score == 15
    assert result.rs_composite == 10
    assert result.breakout55 is True


def test_future_rows_do_not_change_signal():
    history = make_history()

    signal_date = pd.Timestamp(
        "2024-01-05"
    )

    original = generate_signal(
        ticker="AAPL",
        history=history,
        signal_date=signal_date,
    )

    history.loc[
        pd.Timestamp("2024-12-31"),
        "Close",
    ] = 99_999

    replayed = generate_signal(
        ticker="AAPL",
        history=history,
        signal_date=signal_date,
    )

    assert original is not None
    assert replayed is not None
    assert original.price == replayed.price


def test_signal_is_repeatable():
    history = make_history()
    signal_date = pd.Timestamp(
        "2024-01-05"
    )

    first = generate_signal(
        ticker="AAPL",
        history=history,
        signal_date=signal_date,
    )

    second = generate_signal(
        ticker="AAPL",
        history=history,
        signal_date=signal_date,
    )

    assert first == second


def test_historical_signal_to_dict():
    history = make_history()

    signal = generate_signal(
        ticker="AAPL",
        history=history,
        signal_date=pd.Timestamp(
            "2024-01-05"
        ),
        score=80.0,
        trade_plan="璽?? ACTIONABLE",
    )

    assert signal is not None

    result = historical_signal_to_dict(
        signal
    )

    assert list(result.keys()) == (
        SIGNAL_COLUMNS
    )
    assert result["Ticker"] == "AAPL"
    assert result["Score"] == 80.0
    assert (
        result["TradePlan"]
        == "璽?? ACTIONABLE"
    )


def test_point_in_time_benchmark_returns():
    benchmark = make_long_history(
        periods=300,
        base_price=100.0,
        daily_increment=0.1,
    )

    signal_date = benchmark.index[252]

    result = (
        calculate_point_in_time_benchmark_returns(
            benchmark,
            signal_date,
        )
    )

    assert result is not None
    assert set(result) == {
        21,
        63,
        126,
        252,
    }


def test_benchmark_returns_require_sufficient_history():
    benchmark = make_long_history(
        periods=252
    )

    result = (
        calculate_point_in_time_benchmark_returns(
            benchmark,
            benchmark.index[-1],
        )
    )

    assert result is None


def test_future_benchmark_rows_do_not_change_returns():
    benchmark = make_long_history(
        periods=300,
        base_price=100.0,
        daily_increment=0.1,
    )

    signal_date = benchmark.index[252]

    original = (
        calculate_point_in_time_benchmark_returns(
            benchmark,
            signal_date,
        )
    )

    modified = benchmark.copy()
    modified.loc[
        benchmark.index[-1],
        "Close",
    ] = 1_000_000.0

    replayed = (
        calculate_point_in_time_benchmark_returns(
            modified,
            signal_date,
        )
    )

    assert original == replayed


def test_evaluate_production_snapshot_uses_all_engines(
    monkeypatch: pytest.MonkeyPatch,
):
    history = make_long_history()
    metrics = make_production_metrics()
    score_result = make_score_result()
    risk_result = make_risk_result()

    calls: list[str] = []

    def fake_calculate_indicators(
        ticker: str,
        snapshot: pd.DataFrame,
        spy_returns: dict[int, float],
    ) -> dict[str, Any]:
        calls.append("indicator")
        assert ticker == "AAPL"
        assert not snapshot.empty
        assert set(spy_returns) == {
            21,
            63,
            126,
            252,
        }
        return metrics

    def fake_run_filters(
        ticker: str,
        supplied_metrics: dict[str, Any],
    ) -> tuple[bool, str]:
        calls.append("filter")
        assert ticker == "AAPL"
        assert supplied_metrics is metrics
        return True, "PASS"

    def fake_calculate_score(
        supplied_metrics: dict[str, Any],
        market_bull: bool,
        market_regime: str | None = None,
    ) -> dict[str, Any]:
        calls.append("score")
        assert supplied_metrics is metrics
        assert market_bull is True
        assert market_regime == "BULL"
        return score_result

    def fake_calculate_risk(
        snapshot: pd.DataFrame,
        supplied_metrics: dict[str, Any],
        score: float,
    ) -> dict[str, Any]:
        calls.append("risk")
        assert not snapshot.empty
        assert supplied_metrics is metrics
        assert score == 84.0
        return risk_result

    monkeypatch.setattr(
        replay_module,
        "calculate_indicators",
        fake_calculate_indicators,
    )
    monkeypatch.setattr(
        replay_module,
        "run_filters",
        fake_run_filters,
    )
    monkeypatch.setattr(
        replay_module,
        "calculate_score",
        fake_calculate_score,
    )
    monkeypatch.setattr(
        replay_module,
        "calculate_risk",
        fake_calculate_risk,
    )

    result = evaluate_production_snapshot(
        ticker="AAPL",
        history=history,
        spy_returns={
            21: 1.0,
            63: 2.0,
            126: 3.0,
            252: 4.0,
        },
        market_regime="BULL",
    )

    assert result is not None
    assert calls == [
        "indicator",
        "filter",
        "score",
        "risk",
    ]
    assert result["Score"] == 84.0
    assert result["RiskReward"] == 2.0
    assert (
        result["TradePlan"]
        == "璽?? ACTIONABLE"
    )


def test_filtered_snapshot_returns_none(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        replay_module,
        "calculate_indicators",
        lambda ticker, history, spy_returns: (
            make_production_metrics(ticker)
        ),
    )

    monkeypatch.setattr(
        replay_module,
        "run_filters",
        lambda ticker, metrics: (
            False,
            "Price filter",
        ),
    )

    result = evaluate_production_snapshot(
        ticker="AAPL",
        history=make_long_history(),
        spy_returns={
            21: 1.0,
            63: 2.0,
            126: 3.0,
            252: 4.0,
        },
        market_regime="BULL",
    )

    assert result is None


def test_indicator_failure_returns_none(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        replay_module,
        "calculate_indicators",
        lambda ticker, history, spy_returns: None,
    )

    result = evaluate_production_snapshot(
        ticker="AAPL",
        history=make_long_history(),
        spy_returns={
            21: 1.0,
            63: 2.0,
            126: 3.0,
            252: 4.0,
        },
        market_regime="BULL",
    )

    assert result is None


def test_risk_failure_returns_none(
    monkeypatch: pytest.MonkeyPatch,
):
    metrics = make_production_metrics()

    monkeypatch.setattr(
        replay_module,
        "calculate_indicators",
        lambda ticker, history, spy_returns: (
            metrics
        ),
    )

    monkeypatch.setattr(
        replay_module,
        "run_filters",
        lambda ticker, supplied_metrics: (
            True,
            "PASS",
        ),
    )

    monkeypatch.setattr(
        replay_module,
        "calculate_score",
        lambda metrics, market_bull,
        market_regime=None: (
            make_score_result(
                market_regime or "BULL"
            )
        ),
    )

    def raise_invalid_atr(
        history: pd.DataFrame,
        supplied_metrics: dict[str, Any],
        score: float,
    ) -> dict[str, Any]:
        raise ValueError("ATR14 is invalid")

    monkeypatch.setattr(
        replay_module,
        "calculate_risk",
        raise_invalid_atr,
    )

    result = evaluate_production_snapshot(
        ticker="AAPL",
        history=make_long_history(),
        spy_returns={
            21: 1.0,
            63: 2.0,
            126: 3.0,
            252: 4.0,
        },
        market_regime="BULL",
    )

    assert result is None


def test_generate_signal_runs_production_integration(
    monkeypatch: pytest.MonkeyPatch,
):
    history = make_long_history()
    benchmark = make_long_history(
        base_price=400.0,
        daily_increment=0.1,
    )

    signal_date = history.index[252]

    production_values = {
        **make_production_metrics(),
        **make_score_result(),
        **make_risk_result(),
    }

    captured_history: list[
        pd.DataFrame
    ] = []

    def fake_evaluate_production_snapshot(
        *,
        ticker: str,
        history: pd.DataFrame,
        spy_returns: dict[int, float],
        market_regime: str,
    ) -> dict[str, Any]:
        captured_history.append(
            history.copy()
        )
        assert ticker == "AAPL"
        assert set(spy_returns) == {
            21,
            63,
            126,
            252,
        }
        assert market_regime == "BULL"
        return production_values

    monkeypatch.setattr(
        replay_module,
        "evaluate_production_snapshot",
        fake_evaluate_production_snapshot,
    )

    result = generate_signal(
        ticker="AAPL",
        history=history,
        benchmark_history=benchmark,
        signal_date=signal_date,
        market_regime="BULL",
    )

    assert result is not None
    assert result.score == 84.0
    assert result.signal == "簸??瞽 BUY"
    assert (
        result.trade_plan
        == "璽?? ACTIONABLE"
    )
    assert result.risk_reward == 2.0
    assert result.market_regime == "BULL"
    assert result.regime_score == 15
    assert result.rs63 == 12.0
    assert result.breakout55 is True

    assert len(captured_history) == 1
    assert (
        captured_history[0].index.max()
        == signal_date
    )


def test_future_stock_rows_do_not_reach_production_engine(
    monkeypatch: pytest.MonkeyPatch,
):
    history = make_long_history()
    benchmark = make_long_history(
        base_price=400.0,
        daily_increment=0.1,
    )

    signal_date = history.index[252]

    maximum_dates: list[pd.Timestamp] = []

    def fake_evaluate_production_snapshot(
        *,
        ticker: str,
        history: pd.DataFrame,
        spy_returns: dict[int, float],
        market_regime: str,
    ) -> dict[str, Any]:
        maximum_dates.append(
            pd.Timestamp(history.index.max())
        )

        return {
            **make_production_metrics(ticker),
            **make_score_result(
                market_regime
            ),
            **make_risk_result(),
        }

    monkeypatch.setattr(
        replay_module,
        "evaluate_production_snapshot",
        fake_evaluate_production_snapshot,
    )

    result = generate_signal(
        ticker="AAPL",
        history=history,
        benchmark_history=benchmark,
        signal_date=signal_date,
        market_regime="BULL",
    )

    assert result is not None
    assert maximum_dates == [
        signal_date
    ]


def test_market_regime_provider_is_used(
    monkeypatch: pytest.MonkeyPatch,
):
    history = make_long_history()
    benchmark = make_long_history(
        base_price=400.0,
        daily_increment=0.1,
    )

    signal_date = history.index[252]

    captured_regimes: list[str] = []

    def regime_provider(
        date: pd.Timestamp,
    ) -> str:
        assert date == signal_date
        return "NEUTRAL"

    def fake_evaluate_production_snapshot(
        *,
        ticker: str,
        history: pd.DataFrame,
        spy_returns: dict[int, float],
        market_regime: str,
    ) -> dict[str, Any]:
        captured_regimes.append(
            market_regime
        )

        return {
            **make_production_metrics(ticker),
            **make_score_result(
                market_regime
            ),
            **make_risk_result(),
        }

    monkeypatch.setattr(
        replay_module,
        "evaluate_production_snapshot",
        fake_evaluate_production_snapshot,
    )

    result = generate_signal(
        ticker="AAPL",
        history=history,
        benchmark_history=benchmark,
        signal_date=signal_date,
        market_regime_provider=regime_provider,
    )

    assert result is not None
    assert captured_regimes == [
        "NEUTRAL"
    ]
    assert result.market_regime == "NEUTRAL"
    assert result.regime_score == 7


def test_invalid_market_regime_raises_value_error():
    history = make_long_history()
    benchmark = make_long_history(
        base_price=400.0,
        daily_increment=0.1,
    )

    with pytest.raises(
        ValueError,
        match="Unsupported market regime",
    ):
        generate_signal(
            ticker="AAPL",
            history=history,
            benchmark_history=benchmark,
            signal_date=history.index[252],
            market_regime="UNKNOWN",
        )


def test_production_signal_requires_benchmark_history():
    history = make_long_history()

    result = generate_signal(
        ticker="AAPL",
        history=history,
        signal_date=history.index[252],
    )

    assert result is not None
    assert result.score == 0.0
    assert result.trade_plan == ""


def test_production_integration_returns_none_for_short_benchmark():
    history = make_long_history()
    short_benchmark = make_long_history(
        periods=100,
        base_price=400.0,
    )

    result = generate_signal(
        ticker="AAPL",
        history=history,
        benchmark_history=short_benchmark,
        signal_date=history.index[252],
    )

    assert result is None

def test_manual_signal_preserves_portfolio_risk_fields():
    history = make_history()
    result = generate_signal(
        ticker="AAPL",
        history=history,
        signal_date=pd.Timestamp("2024-01-05"),
        position_shares=10,
        stop_loss=95.0,
        take_profit_1=107.5,
        take_profit_2=110.0,
    )
    assert result is not None
    assert result.position_shares == 10
    assert result.stop_loss == pytest.approx(95.0)
    assert result.take_profit_1 == pytest.approx(107.5)
    assert result.take_profit_2 == pytest.approx(110.0)


def test_replay_output_is_native_portfolio_contract(monkeypatch: pytest.MonkeyPatch):
    history = make_long_history()
    benchmark = make_long_history(base_price=400.0, daily_increment=0.1)
    monkeypatch.setattr(
        replay_module,
        "evaluate_production_snapshot",
        lambda **kwargs: {
            **make_production_metrics(kwargs["ticker"]),
            **make_score_result(kwargs["market_regime"]),
            **make_risk_result(),
        },
    )
    signal_date = history.index[252]
    result = replay_universe(
        {"AAPL": history},
        signal_date,
        signal_date,
        benchmark_history=benchmark,
    )
    assert list(result.columns) == SIGNAL_COLUMNS
    assert result.loc[0, "PositionShares"] == 33
    assert result.loc[0, "StopLoss"] == pytest.approx(172.0)
    assert result.loc[0, "TakeProfit1"] == pytest.approx(179.5)
    assert result.loc[0, "TakeProfit2"] == pytest.approx(181.0)
