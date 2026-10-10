"""Integrated walk-forward validation for US Stock Scanner v3.0.0.

Phase 1 provides deterministic rolling/expanding windows, summaries and report
export. Phase 2 adds a concrete orchestration path through replay, portfolio,
backtest, benchmark and factor-validation engines.

The module does not change production filters, scoring, TradePlan or ranking.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import pandas as pd
from dateutil.relativedelta import relativedelta

from scanner.backtest import build_metrics
from scanner.benchmark import BenchmarkConfig, build_benchmark_metrics
from scanner.factor_validation import DEFAULT_FACTORS, build_factor_validation_report
from scanner.portfolio import PortfolioConfig, simulate_portfolio
from scanner.replay import MarketRegimeProvider, replay_universe

WindowRunner = Callable[["WalkForwardWindow", str], "EvaluationResult"]

PORTFOLIO_SIGNAL_COLUMNS = {
    "SignalDate",
    "Ticker",
    "Price",
    "Score",
    "Signal",
    "TradePlan",
    "RiskReward",
    "MarketRegime",
    "RegimeScore",
    "RSComposite",
    "Breakout55",
    "DistanceToHigh55",
    "PositionShares",
    "StopLoss",
    "TakeProfit1",
    "TakeProfit2",
}
FACTOR_COLUMNS = {
    "SignalDate",
    "MarketRegime",
    "RegimeScore",
    "RSComposite",
    "Breakout55",
    "DistanceToHigh55",
}


@dataclass(frozen=True)
class WalkForwardConfig:
    """Configuration for rolling or expanding walk-forward windows."""

    train_years: int = 3
    test_years: int = 1
    step_years: int = 1
    expanding: bool = False

    def __post_init__(self) -> None:
        if self.train_years <= 0:
            raise ValueError("train_years must be positive")
        if self.test_years <= 0:
            raise ValueError("test_years must be positive")
        if self.step_years <= 0:
            raise ValueError("step_years must be positive")


@dataclass(frozen=True)
class WalkForwardWindow:
    """One chronological train/test split."""

    window_id: int
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp

    def __post_init__(self) -> None:
        dates = (self.train_start, self.train_end, self.test_start, self.test_end)
        if any(pd.isna(value) for value in dates):
            raise ValueError("Window dates must be valid")
        if self.window_id <= 0:
            raise ValueError("window_id must be positive")
        if not self.train_start <= self.train_end < self.test_start <= self.test_end:
            raise ValueError("Window dates must be chronological and non-overlapping")

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_id": self.window_id,
            "train_start": self.train_start.date().isoformat(),
            "train_end": self.train_end.date().isoformat(),
            "test_start": self.test_start.date().isoformat(),
            "test_end": self.test_end.date().isoformat(),
        }


@dataclass(frozen=True)
class EvaluationResult:
    """Metrics and artifacts returned by one train or test evaluation."""

    metrics: Mapping[str, float]
    trade_count: int = 0
    benchmark_metrics: Mapping[str, float] = field(default_factory=dict)
    factor_metrics: Mapping[str, float] = field(default_factory=dict)
    signals: pd.DataFrame = field(default_factory=pd.DataFrame, compare=False)
    equity_curve: pd.Series = field(
        default_factory=lambda: pd.Series(dtype=float), compare=False
    )
    trade_log: pd.DataFrame = field(default_factory=pd.DataFrame, compare=False)
    factor_report: Mapping[str, pd.DataFrame] = field(
        default_factory=dict, compare=False
    )

    def __post_init__(self) -> None:
        if self.trade_count < 0:
            raise ValueError("trade_count cannot be negative")


@dataclass(frozen=True)
class WalkForwardResult:
    """Integrated train/test result for one walk-forward window."""

    window: WalkForwardWindow
    train: EvaluationResult
    test: EvaluationResult

    @property
    def window_id(self) -> int:
        return self.window.window_id

    def to_dict(self) -> dict[str, Any]:
        row = self.window.to_dict()
        row.update({"train_trades": self.train.trade_count, "test_trades": self.test.trade_count})
        row.update(_prefixed_metrics("train", self.train.metrics))
        row.update(_prefixed_metrics("test", self.test.metrics))
        row.update(_prefixed_metrics("train_benchmark", self.train.benchmark_metrics))
        row.update(_prefixed_metrics("test_benchmark", self.test.benchmark_metrics))
        return row


@dataclass(frozen=True)
class WalkForwardSummary:
    """Cross-window out-of-sample summary."""

    window_count: int
    profitable_windows: int
    consistency_score: float
    average_test_return: float
    average_test_sharpe: float
    average_test_alpha: float
    best_test_return: float
    worst_test_return: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _timestamp(value: Any) -> pd.Timestamp:
    result = pd.Timestamp(value)
    if pd.isna(result):
        raise ValueError("Date must be valid")
    if result.tzinfo is not None:
        result = result.tz_convert(None)
    return result.normalize()


def generate_windows(
    start_date: Any,
    end_date: Any,
    train_years: int = 3,
    test_years: int = 1,
    step_years: int = 1,
    expanding: bool = False,
) -> list[WalkForwardWindow]:
    """Generate deterministic chronological train/test windows."""
    config = WalkForwardConfig(train_years, test_years, step_years, expanding)
    start = _timestamp(start_date)
    end = _timestamp(end_date)
    if start >= end:
        raise ValueError("start_date must be earlier than end_date")

    windows: list[WalkForwardWindow] = []
    anchor = start
    window_id = 1
    while True:
        train_start = start if config.expanding else anchor
        train_end = anchor + relativedelta(years=config.train_years) - pd.Timedelta(days=1)
        test_start = train_end + pd.Timedelta(days=1)
        test_end = test_start + relativedelta(years=config.test_years) - pd.Timedelta(days=1)
        if test_end > end:
            break
        windows.append(
            WalkForwardWindow(window_id, train_start, train_end, test_start, test_end)
        )
        anchor += relativedelta(years=config.step_years)
        window_id += 1
    return windows


def run_walkforward_window(
    window: WalkForwardWindow, evaluator: WindowRunner
) -> WalkForwardResult:
    """Run injected evaluation logic for one train/test window."""
    train = evaluator(window, "train")
    test = evaluator(window, "test")
    if not isinstance(train, EvaluationResult) or not isinstance(test, EvaluationResult):
        raise TypeError("evaluator must return EvaluationResult")
    return WalkForwardResult(window=window, train=train, test=test)


def run_walkforward(
    windows: Sequence[WalkForwardWindow], evaluator: WindowRunner
) -> list[WalkForwardResult]:
    """Run all windows in deterministic window-id order."""
    ordered = sorted(windows, key=lambda item: item.window_id)
    identifiers = [window.window_id for window in ordered]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("window_id values must be unique")
    return [run_walkforward_window(window, evaluator) for window in ordered]


def _period(window: WalkForwardWindow, sample: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    if sample == "train":
        return window.train_start, window.train_end
    if sample == "test":
        return window.test_start, window.test_end
    raise ValueError("sample must be 'train' or 'test'")


def _slice_prices(
    universe_data: Mapping[str, pd.DataFrame], start: pd.Timestamp, end: pd.Timestamp
) -> dict[str, pd.DataFrame]:
    sliced: dict[str, pd.DataFrame] = {}
    for symbol, frame in universe_data.items():
        if frame is None or frame.empty:
            continue
        clean = frame.copy()
        clean.index = pd.to_datetime(clean.index).tz_localize(None).normalize()
        selected = clean.loc[(clean.index >= start) & (clean.index <= end)].copy()
        if not selected.empty:
            sliced[str(symbol).upper()] = selected
    return sliced


def _benchmark_values(
    benchmark_history: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> pd.Series:
    if "Close" not in benchmark_history.columns:
        raise ValueError("benchmark_history requires a Close column")
    frame = benchmark_history.copy()
    frame.index = pd.to_datetime(frame.index).tz_localize(None).normalize()
    values = pd.to_numeric(frame["Close"], errors="coerce")
    return values.loc[(values.index >= start) & (values.index <= end)].dropna()


def _validate_portfolio_signal_columns(signals: pd.DataFrame) -> None:
    missing = sorted(PORTFOLIO_SIGNAL_COLUMNS.difference(signals.columns))
    if missing:
        raise ValueError(
            "Replay output cannot be simulated because portfolio fields are missing: "
            f"{missing}. Extend HistoricalSignal/SIGNAL_COLUMNS to preserve the risk fields "
            "returned by calculate_risk()."
        )


def _trade_returns(trade_log: pd.DataFrame) -> pd.Series:
    if trade_log.empty or "net_return" not in trade_log.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(trade_log["net_return"], errors="coerce").dropna().astype(float)


def _factor_observations(signals: pd.DataFrame, trade_log: pd.DataFrame) -> pd.DataFrame:
    if signals.empty or trade_log.empty:
        return pd.DataFrame(columns=[*sorted(FACTOR_COLUMNS), "Return"])
    returns = trade_log[["signal_date", "symbol", "net_return"]].copy()
    returns.columns = ["SignalDate", "Ticker", "Return"]
    returns["SignalDate"] = pd.to_datetime(returns["SignalDate"])
    returns["Ticker"] = returns["Ticker"].astype(str).str.upper()
    returns["Return"] = pd.to_numeric(returns["Return"], errors="coerce") / 100.0

    factors = signals.copy()
    factors["SignalDate"] = pd.to_datetime(factors["SignalDate"])
    factors["Ticker"] = factors["Ticker"].astype(str).str.upper()
    merged = factors.merge(returns, on=["SignalDate", "Ticker"], how="inner")
    return merged[[*sorted(FACTOR_COLUMNS), "Return"]]


def _flatten_factor_report(report: Mapping[str, pd.DataFrame]) -> dict[str, float]:
    metrics: dict[str, float] = {}
    individual = report.get("Individual Factors")
    if individual is None or individual.empty:
        return metrics
    for row in individual.to_dict(orient="records"):
        factor_name = str(row["factor_name"])
        metrics[f"{factor_name}_sample_size"] = float(row["sample_size"])
        metrics[f"{factor_name}_total_return"] = float(row["total_return"])
        metrics[f"{factor_name}_sharpe_ratio"] = float(row["sharpe_ratio"])
        metrics[f"{factor_name}_alpha"] = float(row["alpha"])
    return metrics


def evaluate_real_engines(
    window: WalkForwardWindow,
    sample: str,
    *,
    universe_data: Mapping[str, pd.DataFrame],
    benchmark_history: pd.DataFrame,
    portfolio_config: PortfolioConfig | None = None,
    benchmark_config: BenchmarkConfig | None = None,
    market_regime: str = "BULL",
    market_regime_provider: MarketRegimeProvider | None = None,
) -> EvaluationResult:
    """Run replay, portfolio, backtest, benchmark and factor engines for a period."""
    start, end = _period(window, sample)
    signals = replay_universe(
        universe_data,
        start,
        end,
        benchmark_history=benchmark_history,
        market_regime=market_regime,
        market_regime_provider=market_regime_provider,
    )
    if signals.empty:
        return EvaluationResult(metrics={}, signals=signals)

    _validate_portfolio_signal_columns(signals)
    prices = _slice_prices(universe_data, start, end)
    portfolio = simulate_portfolio(
        signals.to_dict(orient="records"), prices, portfolio_config
    )
    equity_curve = portfolio.equity_curve_series()
    trade_log = portfolio.trade_log_frame()
    if equity_curve.empty:
        return EvaluationResult(
            metrics={},
            trade_count=len(trade_log),
            signals=signals,
            equity_curve=equity_curve,
            trade_log=trade_log,
        )

    benchmark_values = _benchmark_values(benchmark_history, start, end)
    benchmark_result = build_benchmark_metrics(
        equity_curve, benchmark_values, benchmark_config
    )
    benchmark_metrics = {
        key: float(value)
        for key, value in benchmark_result.to_dict().items()
        if isinstance(value, (int, float))
    }
    metrics = build_metrics(
        equity_curve,
        _trade_returns(trade_log),
        benchmark_return=benchmark_result.benchmark_return,
    )

    factor_report: Mapping[str, pd.DataFrame] = {}
    factor_metrics: dict[str, float] = {}
    observations = _factor_observations(signals, trade_log)
    if not observations.empty:
        aligned_benchmark = benchmark_values.pct_change().dropna()
        factor_dates = pd.DatetimeIndex(observations["SignalDate"])
        factor_benchmark = aligned_benchmark.reindex(factor_dates)
        if not factor_benchmark.isna().any():
            factor_benchmark.index = factor_dates
            factor_report = build_factor_validation_report(
                observations,
                DEFAULT_FACTORS,
                factor_benchmark,
            )
            factor_metrics = _flatten_factor_report(factor_report)

    return EvaluationResult(
        metrics=metrics,
        trade_count=len(trade_log),
        benchmark_metrics=benchmark_metrics,
        factor_metrics=factor_metrics,
        signals=signals,
        equity_curve=equity_curve,
        trade_log=trade_log,
        factor_report=factor_report,
    )


def run_walkforward_strategy(
    windows: Sequence[WalkForwardWindow],
    *,
    universe_data: Mapping[str, pd.DataFrame],
    benchmark_history: pd.DataFrame,
    portfolio_config: PortfolioConfig | None = None,
    benchmark_config: BenchmarkConfig | None = None,
    market_regime: str = "BULL",
    market_regime_provider: MarketRegimeProvider | None = None,
) -> list[WalkForwardResult]:
    """Run the concrete Phase 2 engine integration across all windows."""

    def evaluator(window: WalkForwardWindow, sample: str) -> EvaluationResult:
        return evaluate_real_engines(
            window,
            sample,
            universe_data=universe_data,
            benchmark_history=benchmark_history,
            portfolio_config=portfolio_config,
            benchmark_config=benchmark_config,
            market_regime=market_regime,
            market_regime_provider=market_regime_provider,
        )

    return run_walkforward(windows, evaluator)


def _metric(metrics: Mapping[str, float], *names: str) -> float:
    for name in names:
        if name in metrics:
            return float(metrics[name])
    return 0.0


def build_walkforward_summary(results: Sequence[WalkForwardResult]) -> WalkForwardSummary:
    """Aggregate out-of-sample results across all complete windows."""
    if not results:
        raise ValueError("At least one walk-forward result is required")
    returns = [_metric(result.test.metrics, "total_return", "TotalReturn") for result in results]
    sharpes = [_metric(result.test.metrics, "sharpe_ratio", "SharpeRatio") for result in results]
    alphas = [
        _metric(result.test.benchmark_metrics or result.test.metrics, "alpha", "Alpha")
        for result in results
    ]
    profitable = sum(value > 0 for value in returns)
    count = len(results)
    return WalkForwardSummary(
        window_count=count,
        profitable_windows=profitable,
        consistency_score=profitable / count,
        average_test_return=sum(returns) / count,
        average_test_sharpe=sum(sharpes) / count,
        average_test_alpha=sum(alphas) / count,
        best_test_return=max(returns),
        worst_test_return=min(returns),
    )


def _prefixed_metrics(prefix: str, metrics: Mapping[str, float]) -> dict[str, float]:
    return {f"{prefix}_{key}": float(value) for key, value in metrics.items()}


def results_to_frame(results: Iterable[WalkForwardResult]) -> pd.DataFrame:
    return pd.DataFrame([result.to_dict() for result in results])


def factor_results_to_frame(results: Iterable[WalkForwardResult]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for result in results:
        for sample_name, evaluation in (("train", result.train), ("test", result.test)):
            for factor_name, value in evaluation.factor_metrics.items():
                rows.append(
                    {
                        "window_id": result.window_id,
                        "sample": sample_name,
                        "factor": factor_name,
                        "value": float(value),
                    }
                )
    return pd.DataFrame(rows, columns=["window_id", "sample", "factor", "value"])


def build_walkforward_report(
    results: Sequence[WalkForwardResult],
) -> dict[str, pd.DataFrame]:
    summary = build_walkforward_summary(results)
    windows = results_to_frame(results)
    benchmark_columns = [
        column
        for column in windows.columns
        if column.startswith("train_benchmark_")
        or column.startswith("test_benchmark_")
    ]
    benchmark = windows[["window_id", *benchmark_columns]].copy()
    return {
        "Summary": pd.DataFrame([summary.to_dict()]),
        "Windows": windows,
        "Benchmark": benchmark,
        "Factor Validation": factor_results_to_frame(results),
    }


def export_walkforward_report(
    report: Mapping[str, pd.DataFrame], output_path: str | Path
) -> Path:
    destination = Path(output_path)
    if destination.suffix.lower() == ".xlsx":
        destination.parent.mkdir(parents=True, exist_ok=True)
        with pd.ExcelWriter(destination, engine="openpyxl") as writer:
            for sheet_name, frame in report.items():
                frame.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        return destination
    if destination.suffix:
        raise ValueError("output_path must be an .xlsx file or a directory")
    destination.mkdir(parents=True, exist_ok=True)
    for name, frame in report.items():
        frame.to_csv(destination / f"{name.lower().replace(' ', '_')}.csv", index=False)
    return destination
