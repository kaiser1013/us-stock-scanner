"""
Aligned portfolio-versus-benchmark analytics for v2.11.0.

This module is isolated from the live scanner.

It aligns dated portfolio and benchmark observations,
calculates periodic returns,
and produces reproducible:

- Beta
- Tracking Error
- Information Ratio
- Alpha
- Benchmark comparison metrics
"""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
from typing import Sequence

import numpy as np
import pandas as pd

TRADING_PERIODS_PER_YEAR = 252

PORTFOLIO_COLUMN = "Portfolio"
BENCHMARK_COLUMN = "Benchmark"

PORTFOLIO_RETURN_COLUMN = "PortfolioReturn"
BENCHMARK_RETURN_COLUMN = "BenchmarkReturn"
ACTIVE_RETURN_COLUMN = "ActiveReturn"


@dataclass(frozen=True, slots=True)
class BenchmarkConfig:
    periods_per_year: int = TRADING_PERIODS_PER_YEAR
    minimum_observations: int = 2
    drop_missing: bool = True

    def __post_init__(self) -> None:
        if self.periods_per_year <= 0:
            raise ValueError(
                "periods_per_year must be positive"
            )

        if self.minimum_observations < 2:
            raise ValueError(
                "minimum_observations must be at least 2"
            )


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    observations: int

    start_date: pd.Timestamp
    end_date: pd.Timestamp

    portfolio_return: float
    benchmark_return: float

    alpha: float
    beta: float

    tracking_error: float
    information_ratio: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame([self.to_dict()])

    def export(
        self,
        path: str | Path,
    ) -> Path:
        output = Path(path)

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        frame = self.to_frame()

        suffix = output.suffix.lower()

        if suffix == ".csv":
            frame.to_csv(
                output,
                index=False,
            )

        elif suffix == ".xlsx":
            frame.to_excel(
                output,
                index=False,
                engine="openpyxl",
            )

        else:
            raise ValueError(
                "benchmark result path must end in .csv or .xlsx"
            )

        return output


def _as_series(
    values: (
        pd.Series
        | Mapping[object, float]
        | Sequence[float]
    ),
    *,
    name: str,
) -> pd.Series:
    """
    Normalise arbitrary inputs into a clean datetime-indexed series.
    """

    if isinstance(values, pd.Series):
        series = values.copy()

    elif isinstance(values, Mapping):
        series = pd.Series(
            values,
            dtype=float,
        )

    else:
        series = pd.Series(
            values,
            dtype=float,
        )

    if series.empty:
        raise ValueError(
            f"{name} cannot be empty"
        )

    series = pd.to_numeric(
        series,
        errors="coerce",
    ).astype(float)

    try:
        index = pd.to_datetime(series.index)

    except (TypeError, ValueError) as error:
        raise ValueError(
            f"{name} requires a date-like index"
        ) from error

    normalized_index = (
        pd.DatetimeIndex(index)
        .tz_localize(None)
        .normalize()
    )

    series.index = normalized_index

    series = (
        series[~series.index.duplicated(keep="last")]
        .sort_index()
    )

    series.name = name

    return series


def align_value_series(
    portfolio_values: (
        pd.Series
        | Mapping[object, float]
    ),
    benchmark_values: (
        pd.Series
        | Mapping[object, float]
    ),
    *,
    drop_missing: bool = True,
) -> pd.DataFrame:
    """
    Align price/equity/value history by calendar date.
    """

    portfolio = _as_series(
        portfolio_values,
        name=PORTFOLIO_COLUMN,
    )

    benchmark = _as_series(
        benchmark_values,
        name=BENCHMARK_COLUMN,
    )

    how = "inner" if drop_missing else "outer"

    aligned = pd.concat(
        [
            portfolio,
            benchmark,
        ],
        axis=1,
        join=how,
    ).sort_index()

    if drop_missing:
        aligned = aligned.dropna()

    if aligned.empty:
        raise ValueError(
            "portfolio and benchmark have no aligned observations"
        )

    return aligned.astype(float)


def calculate_return_series(
    aligned_values: pd.DataFrame,
) -> pd.DataFrame:
    """
    Convert aligned value history
    into aligned return history.
    """

    required = {
        PORTFOLIO_COLUMN,
        BENCHMARK_COLUMN,
    }

    missing = required.difference(
        aligned_values.columns
    )

    if missing:
        raise ValueError(
            f"aligned values are missing columns: "
            f"{sorted(missing)}"
        )

    if len(aligned_values) < 2:
        raise ValueError(
            "at least two aligned value observations are required"
        )

    if (
        aligned_values[
            [PORTFOLIO_COLUMN, BENCHMARK_COLUMN]
        ] <= 0
    ).any().any():
        raise ValueError(
            "portfolio and benchmark values must be positive"
        )

    returns = (
        aligned_values[
            [
                PORTFOLIO_COLUMN,
                BENCHMARK_COLUMN,
            ]
        ]
        .pct_change()
        .dropna()
    )

    returns.columns = [
        PORTFOLIO_RETURN_COLUMN,
        BENCHMARK_RETURN_COLUMN,
    ]

    returns[ACTIVE_RETURN_COLUMN] = (
        returns[PORTFOLIO_RETURN_COLUMN]
        - returns[BENCHMARK_RETURN_COLUMN]
    )

    if returns.empty:
        raise ValueError(
            "aligned values did not produce return observations"
        )

    return returns.astype(float)

def align_return_series(
    portfolio_returns: (
        pd.Series
        | Mapping[object, float]
    ),
    benchmark_returns: (
        pd.Series
        | Mapping[object, float]
    ),
    *,
    drop_missing: bool = True,
) -> pd.DataFrame:
    """
    Align pre-calculated return series.
    """

    portfolio = _as_series(
        portfolio_returns,
        name=PORTFOLIO_RETURN_COLUMN,
    )

    benchmark = _as_series(
        benchmark_returns,
        name=BENCHMARK_RETURN_COLUMN,
    )

    how = "inner" if drop_missing else "outer"

    aligned = pd.concat(
        [
            portfolio,
            benchmark,
        ],
        axis=1,
        join=how,
    ).sort_index()

    if drop_missing:
        aligned = aligned.dropna()

    if aligned.empty:
        raise ValueError(
            "portfolio and benchmark have no aligned returns"
        )

    aligned[ACTIVE_RETURN_COLUMN] = (
        aligned[PORTFOLIO_RETURN_COLUMN]
        - aligned[BENCHMARK_RETURN_COLUMN]
    )

    return aligned.astype(float)


def _validate_returns(
    returns: pd.DataFrame,
    minimum_observations: int = 2,
) -> None:
    required = {
        PORTFOLIO_RETURN_COLUMN,
        BENCHMARK_RETURN_COLUMN,
    }

    missing = required.difference(
        returns.columns
    )

    if missing:
        raise ValueError(
            f"returns are missing columns: "
            f"{sorted(missing)}"
        )

    clean = returns[
        [
            PORTFOLIO_RETURN_COLUMN,
            BENCHMARK_RETURN_COLUMN,
        ]
    ].dropna()

    if len(clean) < minimum_observations:
        raise ValueError(
            f"at least {minimum_observations} "
            f"aligned return observations are required"
        )

    if not np.isfinite(
        clean.to_numpy(dtype=float)
    ).all():
        raise ValueError(
            "returns must contain only finite values"
        )


def calculate_beta(
    returns: pd.DataFrame,
) -> float:
    """
    Beta =
    Covariance(portfolio, benchmark)
    /
    Variance(benchmark)
    """

    _validate_returns(returns)

    portfolio = returns[
        PORTFOLIO_RETURN_COLUMN
    ].astype(float)

    benchmark = returns[
        BENCHMARK_RETURN_COLUMN
    ].astype(float)

    benchmark_variance = float(
        benchmark.var(ddof=1)
    )

    if np.isclose(
        benchmark_variance,
        0.0,
    ):
        raise ValueError(
            "benchmark return variance must be positive"
        )

    covariance = float(
        portfolio.cov(benchmark)
    )

    return covariance / benchmark_variance


def calculate_tracking_error(
    returns: pd.DataFrame,
    periods_per_year: int = TRADING_PERIODS_PER_YEAR,
) -> float:
    """
    Annualised tracking error.
    """

    if periods_per_year <= 0:
        raise ValueError(
            "periods_per_year must be positive"
        )

    _validate_returns(returns)

    active_returns = (
        returns[PORTFOLIO_RETURN_COLUMN].astype(float)
        - returns[BENCHMARK_RETURN_COLUMN].astype(float)
    )

    tracking_error = (
        active_returns.std(ddof=1)
        * np.sqrt(periods_per_year)
    )

    return float(tracking_error)


def calculate_information_ratio(
    returns: pd.DataFrame,
    periods_per_year: int = TRADING_PERIODS_PER_YEAR,
) -> float:
    """
    Annualised Information Ratio.

    Mean Active Return
    ------------------
    Tracking Error
    """

    tracking_error = calculate_tracking_error(
        returns,
        periods_per_year,
    )

    active_returns = (
        returns[PORTFOLIO_RETURN_COLUMN].astype(float)
        - returns[BENCHMARK_RETURN_COLUMN].astype(float)
    )

    active_return_annualised = float(
        active_returns.mean()
        * periods_per_year
    )

    if np.isclose(
        tracking_error,
        0.0,
    ):
        if np.isclose(
            active_return_annualised,
            0.0,
        ):
            return 0.0

        raise ValueError(
            "information ratio is undefined when tracking error is zero"
        )

    return (
        active_return_annualised
        /
        tracking_error
    )


def calculate_total_return(
    values: (
        pd.Series
        | Mapping[object, float]
    ),
) -> float:
    """
    Percent total return.
    """

    series = (
        _as_series(
            values,
            name="Values",
        )
        .dropna()
    )

    if len(series) < 2:
        raise ValueError(
            "at least two value observations are required"
        )

    first_value = float(series.iloc[0])
    last_value = float(series.iloc[-1])

    if first_value <= 0 or last_value <=0:
        raise ValueError(
            "values must be positive"
        )

    return (
        (last_value / first_value)
        - 1.0
    ) * 100.0


def build_benchmark_metrics(
    portfolio_values: (
        pd.Series
        | Mapping[object, float]
    ),
    benchmark_values: (
        pd.Series
        | Mapping[object, float]
    ),
    config: BenchmarkConfig | None = None,
) -> BenchmarkResult:
    """
    Main v2.11 benchmark analytics entrypoint.
    """

    settings = config or BenchmarkConfig()

    aligned_values = align_value_series(
        portfolio_values,
        benchmark_values,
        drop_missing=settings.drop_missing,
    )

    returns = calculate_return_series(
        aligned_values
    )

    _validate_returns(
        returns,
        settings.minimum_observations,
    )

    portfolio_return = calculate_total_return(
        aligned_values[PORTFOLIO_COLUMN]
    )

    benchmark_return = calculate_total_return(
        aligned_values[BENCHMARK_COLUMN]
    )

    alpha = (
        portfolio_return
        - benchmark_return
    )

    beta = calculate_beta(
        returns
    )

    tracking_error = (
        calculate_tracking_error(
            returns,
            settings.periods_per_year,
        )
    )

    information_ratio = (
        calculate_information_ratio(
            returns,
            settings.periods_per_year,
        )
    )

    return BenchmarkResult(
        observations=len(returns),
        
        start_date=pd.Timestamp(
            aligned_values.index[0]
        ),
        
        end_date=pd.Timestamp(
            aligned_values.index[-1]
        ),
        
        portfolio_return=portfolio_return,
        benchmark_return=benchmark_return,
        
        alpha=alpha,
        beta=beta,
        
        tracking_error=tracking_error,
        information_ratio=information_ratio,
    )
    
