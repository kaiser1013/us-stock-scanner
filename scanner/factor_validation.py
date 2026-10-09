"""Observational factor validation for US Stock Scanner v2.12.0.

This module evaluates RegimeScore, RSComposite, Breakout55 and
DistanceToHigh55 without changing production filters, scores, TradePlan or
candidate ranking.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

FactorPredicate = Callable[[pd.DataFrame], pd.Series]

REQUIRED_COLUMNS = {
    "SignalDate",
    "Return",
    "MarketRegime",
    "RegimeScore",
    "RSComposite",
    "Breakout55",
    "DistanceToHigh55",
}


@dataclass(frozen=True)
class FactorDefinition:
    """A named, observational factor rule."""

    name: str
    column: str
    operator: str = ">"
    threshold: Any = 0

    def mask(self, frame: pd.DataFrame) -> pd.Series:
        """Return a boolean selection mask for *frame*."""
        if self.column not in frame.columns:
            raise ValueError(f"Missing factor column: {self.column}")

        values = frame[self.column]
        operators: dict[str, Callable[[pd.Series, Any], pd.Series]] = {
            ">": lambda series, value: series > value,
            ">=": lambda series, value: series >= value,
            "<": lambda series, value: series < value,
            "<=": lambda series, value: series <= value,
            "==": lambda series, value: series == value,
            "!=": lambda series, value: series != value,
        }
        if self.operator not in operators:
            raise ValueError(f"Unsupported factor operator: {self.operator}")
        return operators[self.operator](values, self.threshold).fillna(False).astype(bool)


@dataclass(frozen=True)
class FactorResult:
    """Performance summary for one factor selection or factor combination."""

    factor_name: str
    group: str
    sample_size: int
    start_date: pd.Timestamp | None
    end_date: pd.Timestamp | None
    win_rate: float
    average_return: float
    median_return: float
    total_return: float
    annualised_return: float
    annualised_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    maximum_drawdown: float
    benchmark_return: float
    alpha: float
    beta: float
    tracking_error: float
    information_ratio: float

    def to_dict(self) -> dict[str, Any]:
        """Return a serialisable result dictionary."""
        result = asdict(self)
        result["start_date"] = self.start_date.date().isoformat() if self.start_date is not None else None
        result["end_date"] = self.end_date.date().isoformat() if self.end_date is not None else None
        return result


DEFAULT_FACTORS = (
    FactorDefinition("RegimeScore_BULL", "RegimeScore", "==", 15),
    FactorDefinition("RSComposite_Positive", "RSComposite", ">", 0.0),
    FactorDefinition("Breakout55", "Breakout55", "==", True),
    FactorDefinition("DistanceToHigh55_Positive", "DistanceToHigh55", ">", 0.0),
)


def _validate_frame(frame: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(REQUIRED_COLUMNS.difference(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if frame.empty:
        raise ValueError("Factor validation requires at least one observation")

    validated = frame.copy()
    validated["SignalDate"] = pd.to_datetime(validated["SignalDate"], errors="raise")
    validated["Return"] = pd.to_numeric(validated["Return"], errors="raise")
    if validated["Return"].isna().any():
        raise ValueError("Return contains missing values")
    if (validated["Return"] <= -1.0).any():
        raise ValueError("Return must be expressed as decimal returns greater than -1.0")

    validated["MarketRegime"] = validated["MarketRegime"].astype(str).str.upper()
    validated = validated.sort_values("SignalDate", kind="stable").reset_index(drop=True)
    return validated


def _aligned_benchmark_returns(
    selected: pd.DataFrame,
    benchmark_returns: pd.Series | None,
) -> pd.Series:
    if benchmark_returns is None:
        return pd.Series(0.0, index=selected.index, dtype=float)

    benchmark = benchmark_returns.copy()
    benchmark.index = pd.to_datetime(benchmark.index)
    benchmark = pd.to_numeric(benchmark, errors="raise").sort_index()
    dates = pd.DatetimeIndex(selected["SignalDate"])
    aligned = benchmark.reindex(dates)
    if aligned.isna().any():
        missing_dates = dates[aligned.isna()].strftime("%Y-%m-%d").tolist()
        raise ValueError(f"Missing benchmark returns for dates: {missing_dates}")
    return pd.Series(aligned.to_numpy(dtype=float), index=selected.index)


def _compound_return(returns: pd.Series) -> float:
    return float((1.0 + returns).prod() - 1.0)


def _annualised_return(returns: pd.Series, periods_per_year: int) -> float:
    if returns.empty:
        return 0.0
    growth = float((1.0 + returns).prod())
    return float(growth ** (periods_per_year / len(returns)) - 1.0)


def _annualised_volatility(returns: pd.Series, periods_per_year: int) -> float:
    if len(returns) < 2:
        return 0.0
    return float(returns.std(ddof=1) * np.sqrt(periods_per_year))


def _sharpe_ratio(returns: pd.Series, periods_per_year: int) -> float:
    volatility = returns.std(ddof=1) if len(returns) >= 2 else 0.0
    if not np.isfinite(volatility) or volatility == 0:
        return 0.0
    return float(returns.mean() / volatility * np.sqrt(periods_per_year))


def _sortino_ratio(returns: pd.Series, periods_per_year: int) -> float:
    downside = returns[returns < 0]
    downside_deviation = downside.std(ddof=1) if len(downside) >= 2 else 0.0
    if not np.isfinite(downside_deviation) or downside_deviation == 0:
        return 0.0
    return float(returns.mean() / downside_deviation * np.sqrt(periods_per_year))


def _maximum_drawdown(returns: pd.Series) -> float:
    equity = (1.0 + returns).cumprod()
    running_peak = equity.cummax()
    drawdown = equity / running_peak - 1.0
    return float(drawdown.min()) if not drawdown.empty else 0.0


def _beta(returns: pd.Series, benchmark: pd.Series) -> float:
    if len(returns) < 2:
        return 0.0
    variance = float(benchmark.var(ddof=1))
    if not np.isfinite(variance) or variance == 0:
        return 0.0
    covariance = float(np.cov(returns, benchmark, ddof=1)[0, 1])
    return covariance / variance


def _tracking_error(active_returns: pd.Series, periods_per_year: int) -> float:
    if len(active_returns) < 2:
        return 0.0
    return float(active_returns.std(ddof=1) * np.sqrt(periods_per_year))


def _information_ratio(active_returns: pd.Series, periods_per_year: int) -> float:
    tracking_error = _tracking_error(active_returns, periods_per_year)
    if tracking_error == 0:
        return 0.0
    annualised_active_return = float(active_returns.mean() * periods_per_year)
    return annualised_active_return / tracking_error


def _empty_result(factor_name: str, group: str) -> FactorResult:
    return FactorResult(
        factor_name=factor_name,
        group=group,
        sample_size=0,
        start_date=None,
        end_date=None,
        win_rate=0.0,
        average_return=0.0,
        median_return=0.0,
        total_return=0.0,
        annualised_return=0.0,
        annualised_volatility=0.0,
        sharpe_ratio=0.0,
        sortino_ratio=0.0,
        maximum_drawdown=0.0,
        benchmark_return=0.0,
        alpha=0.0,
        beta=0.0,
        tracking_error=0.0,
        information_ratio=0.0,
    )


def summarise_performance(
    frame: pd.DataFrame,
    factor_name: str,
    group: str = "selected",
    benchmark_returns: pd.Series | None = None,
    periods_per_year: int = 252,
) -> FactorResult:
    """Build a deterministic performance summary for selected observations."""
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    if frame.empty:
        return _empty_result(factor_name, group)

    selected = frame.sort_values("SignalDate", kind="stable").reset_index(drop=True)
    returns = selected["Return"].astype(float)
    benchmark = _aligned_benchmark_returns(selected, benchmark_returns)
    active_returns = returns - benchmark
    total_return = _compound_return(returns)
    benchmark_return = _compound_return(benchmark)

    return FactorResult(
        factor_name=factor_name,
        group=group,
        sample_size=len(selected),
        start_date=pd.Timestamp(selected["SignalDate"].iloc[0]),
        end_date=pd.Timestamp(selected["SignalDate"].iloc[-1]),
        win_rate=float((returns > 0).mean()),
        average_return=float(returns.mean()),
        median_return=float(returns.median()),
        total_return=total_return,
        annualised_return=_annualised_return(returns, periods_per_year),
        annualised_volatility=_annualised_volatility(returns, periods_per_year),
        sharpe_ratio=_sharpe_ratio(returns, periods_per_year),
        sortino_ratio=_sortino_ratio(returns, periods_per_year),
        maximum_drawdown=_maximum_drawdown(returns),
        benchmark_return=benchmark_return,
        alpha=total_return - benchmark_return,
        beta=_beta(returns, benchmark),
        tracking_error=_tracking_error(active_returns, periods_per_year),
        information_ratio=_information_ratio(active_returns, periods_per_year),
    )


def validate_factor(
    frame: pd.DataFrame,
    factor: FactorDefinition,
    benchmark_returns: pd.Series | None = None,
    periods_per_year: int = 252,
) -> FactorResult:
    """Validate the observations selected by one factor."""
    validated = _validate_frame(frame)
    selected = validated.loc[factor.mask(validated)]
    return summarise_performance(
        selected,
        factor.name,
        benchmark_returns=benchmark_returns,
        periods_per_year=periods_per_year,
    )


def compare_factor_groups(
    frame: pd.DataFrame,
    factor: FactorDefinition,
    benchmark_returns: pd.Series | None = None,
    periods_per_year: int = 252,
) -> pd.DataFrame:
    """Compare factor-on, factor-off and unfiltered baseline groups."""
    validated = _validate_frame(frame)
    mask = factor.mask(validated)
    results = [
        summarise_performance(validated, factor.name, "baseline", benchmark_returns, periods_per_year),
        summarise_performance(validated.loc[mask], factor.name, "factor_on", benchmark_returns, periods_per_year),
        summarise_performance(validated.loc[~mask], factor.name, "factor_off", benchmark_returns, periods_per_year),
    ]
    return results_to_frame(results)


def validate_factor_combinations(
    frame: pd.DataFrame,
    factors: Sequence[FactorDefinition],
    benchmark_returns: pd.Series | None = None,
    min_combination_size: int = 2,
    max_combination_size: int | None = None,
    periods_per_year: int = 252,
) -> pd.DataFrame:
    """Evaluate logical-AND combinations of observational factor rules."""
    validated = _validate_frame(frame)
    if not factors:
        raise ValueError("At least one factor is required")
    maximum = max_combination_size or len(factors)
    if min_combination_size <= 0 or maximum < min_combination_size:
        raise ValueError("Invalid factor-combination size")
    maximum = min(maximum, len(factors))

    results: list[FactorResult] = []
    for size in range(min_combination_size, maximum + 1):
        for factor_group in combinations(factors, size):
            mask = pd.Series(True, index=validated.index)
            for factor in factor_group:
                mask &= factor.mask(validated)
            name = " + ".join(factor.name for factor in factor_group)
            results.append(
                summarise_performance(
                    validated.loc[mask],
                    name,
                    "combination",
                    benchmark_returns,
                    periods_per_year,
                )
            )
    return results_to_frame(results)


def validate_by_regime(
    frame: pd.DataFrame,
    factor: FactorDefinition | None = None,
    benchmark_returns: pd.Series | None = None,
    periods_per_year: int = 252,
) -> pd.DataFrame:
    """Summarise baseline or factor-selected performance by market regime."""
    validated = _validate_frame(frame)
    if factor is not None:
        validated = validated.loc[factor.mask(validated)]
        factor_name = factor.name
    else:
        factor_name = "Baseline"

    results = [
        summarise_performance(
            validated.loc[validated["MarketRegime"] == regime],
            factor_name,
            regime,
            benchmark_returns,
            periods_per_year,
        )
        for regime in ("BULL", "NEUTRAL", "BEAR")
    ]
    return results_to_frame(results)


def build_factor_validation_report(
    frame: pd.DataFrame,
    factors: Sequence[FactorDefinition] = DEFAULT_FACTORS,
    benchmark_returns: pd.Series | None = None,
    periods_per_year: int = 252,
) -> dict[str, pd.DataFrame]:
    """Build individual, on/off, combination and regime report tables."""
    validated = _validate_frame(frame)
    individual = results_to_frame(
        [
            validate_factor(validated, factor, benchmark_returns, periods_per_year)
            for factor in factors
        ]
    )
    comparisons = pd.concat(
        [
            compare_factor_groups(validated, factor, benchmark_returns, periods_per_year)
            for factor in factors
        ],
        ignore_index=True,
    )
    combinations_frame = validate_factor_combinations(
        validated,
        factors,
        benchmark_returns,
        periods_per_year=periods_per_year,
    )
    regimes = pd.concat(
        [
            validate_by_regime(validated, None, benchmark_returns, periods_per_year),
            *[
                validate_by_regime(validated, factor, benchmark_returns, periods_per_year)
                for factor in factors
            ],
        ],
        ignore_index=True,
    )
    return {
        "Individual Factors": individual,
        "Factor Comparisons": comparisons,
        "Factor Combinations": combinations_frame,
        "Regime Analysis": regimes,
    }


def results_to_frame(results: Iterable[FactorResult]) -> pd.DataFrame:
    """Convert FactorResult objects to a stable report DataFrame."""
    return pd.DataFrame([result.to_dict() for result in results])


def export_factor_validation_report(
    report: Mapping[str, pd.DataFrame],
    output_path: str | Path,
) -> Path:
    """Export report tables to .xlsx or to one .csv file per table."""
    destination = Path(output_path)
    if destination.suffix.lower() == ".xlsx":
        destination.parent.mkdir(parents=True, exist_ok=True)
        with pd.ExcelWriter(destination, engine="openpyxl") as writer:
            for sheet_name, table in report.items():
                table.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        return destination

    if destination.suffix:
        raise ValueError("output_path must be an .xlsx file or a directory")

    destination.mkdir(parents=True, exist_ok=True)
    for name, table in report.items():
        filename = name.lower().replace(" ", "_") + ".csv"
        table.to_csv(destination / filename, index=False)
    return destination
