from pathlib import Path

import pandas as pd
import pytest

import scanner.walkforward as walkforward_module
from scanner.benchmark import BenchmarkResult
from scanner.portfolio import PortfolioConfig
from scanner.walkforward import (
    EvaluationResult,
    WalkForwardConfig,
    WalkForwardWindow,
    build_walkforward_report,
    build_walkforward_summary,
    evaluate_real_engines,
    export_walkforward_report,
    factor_results_to_frame,
    generate_windows,
    results_to_frame,
    run_walkforward,
    run_walkforward_strategy,
    run_walkforward_window,
)


def make_evaluator(calls: list[tuple[int, str]]):
    def evaluator(window: WalkForwardWindow, sample: str) -> EvaluationResult:
        calls.append((window.window_id, sample))
        multiplier = float(window.window_id if sample == "test" else 0.5)
        return EvaluationResult(
            metrics={"TotalReturn": 0.10 * multiplier, "SharpeRatio": multiplier},
            trade_count=window.window_id,
            benchmark_metrics={"alpha": 0.02 * multiplier, "beta": 1.0},
            factor_metrics={"RSComposite_Positive_total_return": 0.03 * multiplier},
        )

    return evaluator


def window(window_id: int = 1) -> WalkForwardWindow:
    return WalkForwardWindow(
        window_id,
        pd.Timestamp("2020-01-01"),
        pd.Timestamp("2022-12-31"),
        pd.Timestamp("2023-01-01"),
        pd.Timestamp("2023-12-31"),
    )


def price_frame(start: str = "2020-01-01", periods: int = 1461) -> pd.DataFrame:
    index = pd.date_range(start, periods=periods, freq="D")
    close = pd.Series(range(periods), index=index, dtype=float) + 100.0
    return pd.DataFrame(
        {
            "Open": close,
            "High": close + 2.0,
            "Low": close - 2.0,
            "Close": close + 1.0,
            "Volume": 2_000_000,
        },
        index=index,
    )


def integrated_signals(start: pd.Timestamp) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "SignalDate": [start],
            "Ticker": ["AAA"],
            "Price": [100.0],
            "Score": [85.0],
            "Signal": ["BUY"],
            "TradePlan": ["??ACTIONABLE"],
            "RiskReward": [2.0],
            "MarketRegime": ["BULL"],
            "RegimeScore": [15.0],
            "RSComposite": [12.0],
            "Breakout55": [True],
            "DistanceToHigh55": [1.0],
            "PositionShares": [10],
            "StopLoss": [95.0],
            "TakeProfit1": [107.5],
            "TakeProfit2": [110.0],
        }
    )


def test_config_rejects_non_positive_values() -> None:
    with pytest.raises(ValueError, match="train_years"):
        WalkForwardConfig(train_years=0)
    with pytest.raises(ValueError, match="test_years"):
        WalkForwardConfig(test_years=0)
    with pytest.raises(ValueError, match="step_years"):
        WalkForwardConfig(step_years=0)


def test_generate_windows_uses_three_year_train_and_one_year_test() -> None:
    windows = generate_windows("2020-01-01", "2025-12-31")
    assert len(windows) == 3
    assert windows[0].train_end == pd.Timestamp("2022-12-31")
    assert windows[0].test_start == pd.Timestamp("2023-01-01")
    assert windows[1].train_start == pd.Timestamp("2021-01-01")


def test_generate_windows_supports_expanding_training_period() -> None:
    windows = generate_windows("2020-01-01", "2025-12-31", expanding=True)
    assert windows[1].train_start == pd.Timestamp("2020-01-01")
    assert windows[1].train_end == pd.Timestamp("2023-12-31")


def test_generate_windows_returns_only_complete_test_periods() -> None:
    assert generate_windows("2020-01-01", "2023-06-30") == []


def test_generate_windows_rejects_invalid_date_order() -> None:
    with pytest.raises(ValueError, match="start_date"):
        generate_windows("2025-01-01", "2024-01-01")


def test_window_rejects_overlap() -> None:
    with pytest.raises(ValueError, match="chronological"):
        WalkForwardWindow(
            1,
            pd.Timestamp("2020-01-01"),
            pd.Timestamp("2022-12-31"),
            pd.Timestamp("2022-12-31"),
            pd.Timestamp("2023-12-31"),
        )


def test_run_walkforward_window_runs_train_then_test() -> None:
    calls: list[tuple[int, str]] = []
    result = run_walkforward_window(window(), make_evaluator(calls))
    assert calls == [(1, "train"), (1, "test")]
    assert result.test.metrics["TotalReturn"] == pytest.approx(0.10)


def test_run_walkforward_rejects_duplicate_window_ids() -> None:
    with pytest.raises(ValueError, match="unique"):
        run_walkforward([window(), window()], make_evaluator([]))


def test_build_summary_uses_out_of_sample_metrics() -> None:
    results = run_walkforward(
        generate_windows("2020-01-01", "2024-12-31"), make_evaluator([])
    )
    summary = build_walkforward_summary(results)
    assert summary.window_count == 2
    assert summary.consistency_score == pytest.approx(1.0)
    assert summary.average_test_return == pytest.approx(0.15)
    assert summary.average_test_alpha == pytest.approx(0.03)


def test_summary_rejects_empty_results() -> None:
    with pytest.raises(ValueError, match="At least one"):
        build_walkforward_summary([])


def test_results_and_factor_frames() -> None:
    result = run_walkforward_window(window(), make_evaluator([]))
    assert results_to_frame([result]).loc[0, "test_TotalReturn"] == pytest.approx(0.10)
    factor_frame = factor_results_to_frame([result])
    assert factor_frame["sample"].tolist() == ["train", "test"]


def test_build_report_contains_required_sheets() -> None:
    report = build_walkforward_report([run_walkforward_window(window(), make_evaluator([]))])
    assert set(report) == {"Summary", "Windows", "Benchmark", "Factor Validation"}


def test_export_report_to_csv_and_excel(tmp_path: Path) -> None:
    result = run_walkforward_window(window(), make_evaluator([]))
    report = build_walkforward_report([result])
    folder = export_walkforward_report(report, tmp_path / "report")
    assert (folder / "summary.csv").exists()
    pytest.importorskip("openpyxl")
    workbook = export_walkforward_report(report, tmp_path / "report.xlsx")
    assert workbook.exists()


def test_real_engine_integration_calls_all_engines(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    signals = integrated_signals(pd.Timestamp("2020-01-02"))

    class FakePortfolio:
        def equity_curve_series(self) -> pd.Series:
            return pd.Series(
                [10_000.0, 10_100.0, 10_200.0],
                index=pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-04"]),
            )

        def trade_log_frame(self) -> pd.DataFrame:
            return pd.DataFrame(
                {
                    "signal_date": [pd.Timestamp("2020-01-02")],
                    "symbol": ["AAA"],
                    "net_return": [2.0],
                }
            )

    monkeypatch.setattr(
        walkforward_module,
        "replay_universe",
        lambda *args, **kwargs: calls.append("replay") or signals,
    )
    monkeypatch.setattr(
        walkforward_module,
        "simulate_portfolio",
        lambda *args, **kwargs: calls.append("portfolio") or FakePortfolio(),
    )
    monkeypatch.setattr(
        walkforward_module,
        "build_metrics",
        lambda *args, **kwargs: calls.append("backtest")
        or {"TotalReturn": 2.0, "SharpeRatio": 1.0},
    )
    monkeypatch.setattr(
        walkforward_module,
        "build_benchmark_metrics",
        lambda *args, **kwargs: calls.append("benchmark")
        or BenchmarkResult(
            2,
            pd.Timestamp("2020-01-02"),
            pd.Timestamp("2020-01-04"),
            2.0,
            1.0,
            1.0,
            1.1,
            0.1,
            0.5,
        ),
    )
    factor_table = pd.DataFrame(
        {
            "factor_name": ["RSComposite_Positive"],
            "sample_size": [1],
            "total_return": [0.02],
            "sharpe_ratio": [1.0],
            "alpha": [0.01],
        }
    )
    monkeypatch.setattr(
        walkforward_module,
        "build_factor_validation_report",
        lambda *args, **kwargs: calls.append("factor")
        or {"Individual Factors": factor_table},
    )

    history = price_frame(periods=10)
    result = evaluate_real_engines(
        window(),
        "train",
        universe_data={"AAA": history},
        benchmark_history=history,
    )
    assert calls == ["replay", "portfolio", "benchmark", "backtest", "factor"]
    assert result.trade_count == 1
    assert result.metrics["TotalReturn"] == 2.0
    assert result.benchmark_metrics["alpha"] == 1.0
    assert result.factor_metrics["RSComposite_Positive_sample_size"] == 1.0


def test_real_engine_integration_rejects_current_replay_interface(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    incomplete = integrated_signals(pd.Timestamp("2020-01-02")).drop(
        columns=["PositionShares", "StopLoss", "TakeProfit1", "TakeProfit2"]
    )
    monkeypatch.setattr(walkforward_module, "replay_universe", lambda *args, **kwargs: incomplete)
    history = price_frame(periods=10)
    with pytest.raises(ValueError, match="portfolio fields are missing"):
        evaluate_real_engines(
            window(),
            "train",
            universe_data={"AAA": history},
            benchmark_history=history,
        )


def test_real_engine_empty_replay_returns_empty_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        walkforward_module, "replay_universe", lambda *args, **kwargs: pd.DataFrame()
    )
    result = evaluate_real_engines(
        window(),
        "test",
        universe_data={},
        benchmark_history=price_frame(periods=10),
    )
    assert result.signals.empty
    assert result.metrics == {}


def test_run_walkforward_strategy_uses_real_evaluator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[int, str]] = []

    def fake_evaluate(window: WalkForwardWindow, sample: str, **kwargs) -> EvaluationResult:
        calls.append((window.window_id, sample))
        return EvaluationResult({"TotalReturn": 1.0})

    monkeypatch.setattr(walkforward_module, "evaluate_real_engines", fake_evaluate)
    results = run_walkforward_strategy(
        [window()],
        universe_data={},
        benchmark_history=price_frame(periods=10),
        portfolio_config=PortfolioConfig(),
    )
    assert calls == [(1, "train"), (1, "test")]
    assert len(results) == 1


def test_invalid_sample_is_rejected() -> None:
    with pytest.raises(ValueError, match="sample"):
        evaluate_real_engines(
            window(),
            "validation",
            universe_data={},
            benchmark_history=price_frame(periods=10),
        )
