from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

import pandas as pd

from scanner.filter import run_filters
from scanner.indicator import (
    RS_LOOKBACKS,
    calculate_indicators,
    calculate_period_return,
)
from scanner.risk import calculate_risk
from scanner.score import calculate_score


MarketRegimeProvider = Callable[
    [pd.Timestamp],
    str,
]


@dataclass(slots=True)
class HistoricalSignal:
    signal_date: pd.Timestamp
    ticker: str
    price: float

    score: float
    signal: str

    trade_plan: str
    risk_reward: float

    market_regime: str
    regime_score: float

    rs21: float
    rs63: float
    rs126: float
    rs252: float
    rs_composite: float

    breakout55: bool
    distance_to_high55: float


SIGNAL_COLUMNS = [
    "SignalDate",
    "Ticker",
    "Price",
    "Score",
    "Signal",
    "TradePlan",
    "RiskReward",
    "MarketRegime",
    "RegimeScore",
    "RS21",
    "RS63",
    "RS126",
    "RS252",
    "RSComposite",
    "Breakout55",
    "DistanceToHigh55",
]


def _normalise_timestamp(
    value: pd.Timestamp | str,
) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)

    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_convert(
            "UTC"
        ).tz_localize(None)

    return timestamp


def _normalise_history(
    history: pd.DataFrame,
) -> pd.DataFrame:
    result = history.copy()

    result.index = pd.to_datetime(
        result.index,
        errors="coerce",
        utc=True,
    )

    result = result.loc[
        ~result.index.isna()
    ].copy()

    result.index = result.index.tz_convert(
        "UTC"
    ).tz_localize(None)

    return result.sort_index()


def _as_float(
    value: Any,
    default: float = 0.0,
) -> float:
    if value is None:
        return default

    try:
        result = float(value)
    except (TypeError, ValueError):
        return default

    if pd.isna(result):
        return default

    return result


def _as_string(
    value: Any,
    default: str = "",
) -> str:
    if value is None:
        return default

    if pd.isna(value):
        return default

    return str(value)


def _as_bool(
    value: Any,
    default: bool = False,
) -> bool:
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if pd.isna(value):
        return default

    return bool(value)


def point_in_time_history(
    history: pd.DataFrame,
    signal_date: pd.Timestamp,
) -> pd.DataFrame:
    """
    Return only observations available on or before signal_date.

    The input DataFrame is not modified.
    """

    normalised_history = _normalise_history(
        history
    )

    normalised_signal_date = _normalise_timestamp(
        signal_date
    )

    return normalised_history.loc[
        normalised_history.index
        <= normalised_signal_date
    ].copy()


def _latest_close(
    history: pd.DataFrame,
) -> float | None:
    if "Close" not in history.columns:
        return None

    close = pd.to_numeric(
        history["Close"],
        errors="coerce",
    ).dropna()

    if close.empty:
        return None

    return float(close.iloc[-1])


def calculate_point_in_time_benchmark_returns(
    benchmark_history: pd.DataFrame,
    signal_date: pd.Timestamp,
) -> dict[int, float] | None:
    """
    Calculate SPY returns using only benchmark data available
    on or before signal_date.
    """

    pit_benchmark = point_in_time_history(
        benchmark_history,
        signal_date,
    )

    if (
        pit_benchmark.empty
        or "Close" not in pit_benchmark.columns
    ):
        return None

    close = pd.to_numeric(
        pit_benchmark["Close"],
        errors="coerce",
    ).dropna()

    required_history = max(
        RS_LOOKBACKS
    ) + 1

    if len(close) < required_history:
        return None

    try:
        return {
            lookback: calculate_period_return(
                close,
                lookback,
            )
            for lookback in RS_LOOKBACKS
        }
    except ValueError:
        return None


def _resolve_market_regime(
    signal_date: pd.Timestamp,
    market_regime: str,
    market_regime_provider: (
        MarketRegimeProvider | None
    ),
) -> str:
    if market_regime_provider is not None:
        resolved_regime = (
            market_regime_provider(
                signal_date
            )
        )
    else:
        resolved_regime = market_regime

    normalised_regime = str(
        resolved_regime
    ).upper()

    valid_regimes = {
        "BULL",
        "NEUTRAL",
        "BEAR",
    }

    if normalised_regime not in valid_regimes:
        raise ValueError(
            "Unsupported market regime: "
            f"{resolved_regime}"
        )

    return normalised_regime


def evaluate_production_snapshot(
    *,
    ticker: str,
    history: pd.DataFrame,
    spy_returns: Mapping[int, float],
    market_regime: str,
) -> dict[str, Any] | None:
    """
    Run the existing production indicator, filter, score
    and risk engines against one point-in-time snapshot.

    Return None when indicators are unavailable, production
    filters fail, or risk calculation cannot produce a plan.
    """

    metrics = calculate_indicators(
        ticker,
        history,
        dict(spy_returns),
    )

    if metrics is None:
        return None

    passed, _reason = run_filters(
        ticker,
        metrics,
    )

    if not passed:
        return None

    normalised_regime = str(
        market_regime
    ).upper()

    score_result = calculate_score(
        metrics,
        market_bull=(
            normalised_regime == "BULL"
        ),
        market_regime=normalised_regime,
    )

    score = float(
        score_result["Score"]
    )

    try:
        risk_result = calculate_risk(
            history,
            metrics,
            score,
        )
    except ValueError:
        return None

    return {
        **metrics,
        **score_result,
        **risk_result,
    }


def _build_historical_signal(
    *,
    ticker: str,
    signal_date: pd.Timestamp,
    price: float,
    values: Mapping[str, Any],
) -> HistoricalSignal:
    return HistoricalSignal(
        signal_date=signal_date,
        ticker=ticker,
        price=_as_float(
            values.get(
                "Price",
                price,
            ),
            price,
        ),
        score=_as_float(
            values.get("Score")
        ),
        signal=_as_string(
            values.get("Signal")
        ),
        trade_plan=_as_string(
            values.get("TradePlan")
        ),
        risk_reward=_as_float(
            values.get("RiskReward")
        ),
        market_regime=_as_string(
            values.get("MarketRegime")
        ),
        regime_score=_as_float(
            values.get(
                "RegimeScore",
                values.get(
                    "MarketScore"
                ),
            )
        ),
        rs21=_as_float(
            values.get("RS21")
        ),
        rs63=_as_float(
            values.get(
                "RS63",
                values.get(
                    "RelativeStrength"
                ),
            )
        ),
        rs126=_as_float(
            values.get("RS126")
        ),
        rs252=_as_float(
            values.get("RS252")
        ),
        rs_composite=_as_float(
            values.get("RSComposite")
        ),
        breakout55=_as_bool(
            values.get("Breakout55")
        ),
        distance_to_high55=_as_float(
            values.get(
                "DistanceToHigh55"
            )
        ),
    )


def generate_signal(
    *,
    ticker: str,
    history: pd.DataFrame,
    signal_date: pd.Timestamp,
    benchmark_history: pd.DataFrame | None = None,
    market_regime: str = "BULL",
    market_regime_provider: (
        MarketRegimeProvider | None
    ) = None,
    score: float = 0.0,
    signal: str = "",
    trade_plan: str = "",
    risk_reward: float = 0.0,
    regime_score: float = 0.0,
    rs21: float = 0.0,
    rs63: float = 0.0,
    rs126: float = 0.0,
    rs252: float = 0.0,
    rs_composite: float = 0.0,
    breakout55: bool = False,
    distance_to_high55: float = 0.0,
) -> HistoricalSignal | None:
    """
    Generate a historical signal using information available
    on or before signal_date.

    When benchmark_history is supplied, the function executes
    the existing production indicator, filter, score and risk
    engines.

    When benchmark_history is omitted, the legacy manual-field
    mode is retained for backwards compatibility.
    """

    normalised_signal_date = _normalise_timestamp(
        signal_date
    )

    pit_history = point_in_time_history(
        history,
        normalised_signal_date,
    )

    if pit_history.empty:
        return None

    price = _latest_close(
        pit_history
    )

    if price is None:
        return None

    if benchmark_history is not None:
        spy_returns = (
            calculate_point_in_time_benchmark_returns(
                benchmark_history,
                normalised_signal_date,
            )
        )

        if spy_returns is None:
            return None

        resolved_regime = (
            _resolve_market_regime(
                normalised_signal_date,
                market_regime,
                market_regime_provider,
            )
        )

        production_values = (
            evaluate_production_snapshot(
                ticker=ticker,
                history=pit_history,
                spy_returns=spy_returns,
                market_regime=resolved_regime,
            )
        )

        if production_values is None:
            return None

        return _build_historical_signal(
            ticker=ticker,
            signal_date=normalised_signal_date,
            price=price,
            values=production_values,
        )

    manual_values: dict[str, Any] = {
        "Price": price,
        "Score": score,
        "Signal": signal,
        "TradePlan": trade_plan,
        "RiskReward": risk_reward,
        "MarketRegime": market_regime,
        "RegimeScore": regime_score,
        "RS21": rs21,
        "RS63": rs63,
        "RS126": rs126,
        "RS252": rs252,
        "RSComposite": rs_composite,
        "Breakout55": breakout55,
        "DistanceToHigh55": (
            distance_to_high55
        ),
    }

    return _build_historical_signal(
        ticker=ticker,
        signal_date=normalised_signal_date,
        price=price,
        values=manual_values,
    )


def replay_symbol(
    *,
    ticker: str,
    history: pd.DataFrame,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    benchmark_history: pd.DataFrame | None = None,
    market_regime: str = "BULL",
    market_regime_provider: (
        MarketRegimeProvider | None
    ) = None,
) -> list[HistoricalSignal]:
    """
    Replay one symbol over the inclusive date range.
    """

    normalised_history = _normalise_history(
        history
    )

    normalised_start_date = (
        _normalise_timestamp(
            start_date
        )
    )

    normalised_end_date = (
        _normalise_timestamp(
            end_date
        )
    )

    if normalised_start_date > normalised_end_date:
        return []

    mask = (
        (
            normalised_history.index
            >= normalised_start_date
        )
        & (
            normalised_history.index
            <= normalised_end_date
        )
    )

    replay_dates = normalised_history.loc[
        mask
    ].index

    signals: list[HistoricalSignal] = []

    for replay_date in replay_dates:
        historical_signal = generate_signal(
            ticker=ticker,
            history=normalised_history,
            signal_date=pd.Timestamp(
                replay_date
            ),
            benchmark_history=(
                benchmark_history
            ),
            market_regime=market_regime,
            market_regime_provider=(
                market_regime_provider
            ),
        )

        if historical_signal is not None:
            signals.append(
                historical_signal
            )

    return signals


def historical_signal_to_dict(
    historical_signal: HistoricalSignal,
) -> dict[str, Any]:
    return {
        "SignalDate": (
            historical_signal.signal_date
        ),
        "Ticker": historical_signal.ticker,
        "Price": historical_signal.price,
        "Score": historical_signal.score,
        "Signal": historical_signal.signal,
        "TradePlan": (
            historical_signal.trade_plan
        ),
        "RiskReward": (
            historical_signal.risk_reward
        ),
        "MarketRegime": (
            historical_signal.market_regime
        ),
        "RegimeScore": (
            historical_signal.regime_score
        ),
        "RS21": historical_signal.rs21,
        "RS63": historical_signal.rs63,
        "RS126": historical_signal.rs126,
        "RS252": historical_signal.rs252,
        "RSComposite": (
            historical_signal.rs_composite
        ),
        "Breakout55": (
            historical_signal.breakout55
        ),
        "DistanceToHigh55": (
            historical_signal
            .distance_to_high55
        ),
    }


def replay_universe(
    universe_data: Mapping[
        str,
        pd.DataFrame,
    ],
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    benchmark_history: pd.DataFrame | None = None,
    market_regime: str = "BULL",
    market_regime_provider: (
        MarketRegimeProvider | None
    ) = None,
) -> pd.DataFrame:
    """
    Replay every symbol and return a deterministic table.
    """

    rows: list[dict[str, Any]] = []

    for ticker in sorted(
        universe_data
    ):
        signals = replay_symbol(
            ticker=ticker,
            history=universe_data[ticker],
            start_date=start_date,
            end_date=end_date,
            benchmark_history=(
                benchmark_history
            ),
            market_regime=market_regime,
            market_regime_provider=(
                market_regime_provider
            ),
        )

        rows.extend(
            historical_signal_to_dict(
                historical_signal
            )
            for historical_signal in signals
        )

    if not rows:
        return pd.DataFrame(
            columns=SIGNAL_COLUMNS
        )

    result = pd.DataFrame(
        rows,
        columns=SIGNAL_COLUMNS,
    )

    return result.sort_values(
        by=[
            "SignalDate",
            "Ticker",
        ],
        kind="stable",
    ).reset_index(
        drop=True
    )
