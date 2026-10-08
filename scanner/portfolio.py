"""Deterministic portfolio simulation and structured trade-log support.

The module is intentionally isolated from the live scanner.  It consumes dated
historical signal objects or mappings and daily OHLC price frames, applies
explicit execution assumptions, reconciles cash, and produces records that can
be passed to the existing backtest metrics layer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime
from math import isfinite
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd

ACTIONABLE = "✅ ACTIONABLE"
EXIT_STOP_LOSS = "STOP LOSS"
EXIT_TAKE_PROFIT = "TAKE PROFIT"
EXIT_TIME = "TIME EXIT"
EXIT_END_OF_DATA = "END OF DATA"


@dataclass(frozen=True, slots=True)
class PortfolioConfig:
    initial_cash: float = 10_000.0
    transaction_cost: float = 0.0
    slippage_bps: float = 0.0
    max_positions: int = 10
    max_holding_sessions: int = 20
    actionable_trade_plan: str = ACTIONABLE
    entry_price_field: str = "Open"

    def __post_init__(self) -> None:
        if self.initial_cash <= 0:
            raise ValueError("initial_cash must be positive")
        if self.transaction_cost < 0:
            raise ValueError("transaction_cost cannot be negative")
        if self.slippage_bps < 0:
            raise ValueError("slippage_bps cannot be negative")
        if self.max_positions <= 0:
            raise ValueError("max_positions must be positive")
        if self.max_holding_sessions <= 0:
            raise ValueError("max_holding_sessions must be positive")
        if self.entry_price_field not in {"Open", "Close"}:
            raise ValueError("entry_price_field must be 'Open' or 'Close'")


@dataclass(frozen=True, slots=True)
class PortfolioSignal:
    signal_date: date
    symbol: str
    price: float
    score: float
    signal: str
    trade_plan: str
    position_shares: int
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    risk_reward: float = 0.0
    market_regime: str = ""
    regime_score: float = 0.0
    rs_composite: float = 0.0
    breakout55: bool = False
    distance_to_high55: float = 0.0

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("symbol cannot be empty")
        if self.price <= 0:
            raise ValueError("price must be positive")
        if self.position_shares < 0:
            raise ValueError("position_shares cannot be negative")
        if self.stop_loss <= 0:
            raise ValueError("stop_loss must be positive")
        if self.take_profit_2 <= 0:
            raise ValueError("take_profit_2 must be positive")


@dataclass(slots=True)
class Position:
    symbol: str
    signal_date: date
    entry_date: date
    entry_price: float
    shares: int
    entry_cost: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    score: float
    signal: str
    trade_plan: str
    risk_reward: float
    market_regime: str
    regime_score: float
    rs_composite: float
    breakout55: bool
    distance_to_high55: float
    holding_sessions: int = 0

    @property
    def market_value_at_entry(self) -> float:
        return self.entry_price * self.shares


@dataclass(frozen=True, slots=True)
class ClosedTrade:
    symbol: str
    signal_date: date
    entry_date: date
    exit_date: date
    entry_price: float
    exit_price: float
    position_size: int
    gross_return: float
    gross_pnl: float
    transaction_costs: float
    net_return: float
    net_pnl: float
    exit_reason: str
    market_regime: str
    score: float
    rs_composite: float
    breakout55: bool
    distance_to_high55: float


@dataclass(frozen=True, slots=True)
class PortfolioState:
    state_date: date
    cash: float
    invested_value: float
    equity: float
    open_positions: int
    closed_trades: int


@dataclass(slots=True)
class PortfolioResult:
    initial_cash: float
    ending_cash: float
    open_positions: list[Position] = field(default_factory=list)
    trade_log: list[ClosedTrade] = field(default_factory=list)
    equity_curve: list[PortfolioState] = field(default_factory=list)

    @property
    def ending_equity(self) -> float:
        if self.equity_curve:
            return self.equity_curve[-1].equity
        return self.ending_cash

    def trade_log_frame(self) -> pd.DataFrame:
        return pd.DataFrame([asdict(trade) for trade in self.trade_log])

    def equity_curve_series(self) -> pd.Series:
        if not self.equity_curve:
            return pd.Series(dtype=float, name="Equity")
        return pd.Series(
            [state.equity for state in self.equity_curve],
            index=pd.to_datetime([state.state_date for state in self.equity_curve]),
            name="Equity",
            dtype=float,
        )

    def export_trade_log(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        frame = self.trade_log_frame()
        suffix = output.suffix.lower()
        if suffix == ".csv":
            frame.to_csv(output, index=False)
        elif suffix == ".xlsx":
            frame.to_excel(output, index=False, engine="openpyxl")
        else:
            raise ValueError("trade log path must end in .csv or .xlsx")
        return output


def _value(source: Mapping[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in source:
            return source[name]
    return default


def _as_mapping(signal: Any) -> Mapping[str, Any]:
    if isinstance(signal, Mapping):
        return signal
        
    if is_dataclass(signal):
        if isinstance(signal, type):
            raise TypeError(
                "Dataclass class provided instead of dataclass instance"
            )
        return asdict(signal)
        
    if hasattr(signal, "__dict__"):
        return vars(signal)
        
    raise TypeError(
        "signal must be a mapping or object with named attributes"
    )


def _as_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return pd.Timestamp(value).date()


def normalise_signal(signal: Any) -> PortfolioSignal:
    """Convert replay output, scanner-style mappings, or PortfolioSignal."""
    if isinstance(signal, PortfolioSignal):
        return signal
    raw = _as_mapping(signal)
    signal_date = _value(raw, "signal_date", "SignalDate")
    symbol = _value(raw, "symbol", "ticker", "Symbol", "Ticker")
    if signal_date is None or symbol is None:
        raise ValueError("signal requires a signal date and symbol/ticker")
    return PortfolioSignal(
        signal_date=_as_date(signal_date),
        symbol=str(symbol).upper(),
        price=float(_value(raw, "price", "Price")),
        score=float(_value(raw, "score", "Score", default=0.0)),
        signal=str(_value(raw, "signal", "Signal", default="")),
        trade_plan=str(_value(raw, "trade_plan", "TradePlan", default="")),
        position_shares=int(
            _value(raw, "position_shares", "PositionShares", default=0)
        ),
        stop_loss=float(_value(raw, "stop_loss", "StopLoss")),
        take_profit_1=float(
            _value(raw, "take_profit_1", "TakeProfit1", default=0.0)
        ),
        take_profit_2=float(_value(raw, "take_profit_2", "TakeProfit2")),
        risk_reward=float(_value(raw, "risk_reward", "RiskReward", default=0.0)),
        market_regime=str(
            _value(raw, "market_regime", "MarketRegime", default="")
        ),
        regime_score=float(_value(raw, "regime_score", "RegimeScore", default=0.0)),
        rs_composite=float(_value(raw, "rs_composite", "RSComposite", default=0.0)),
        breakout55=bool(_value(raw, "breakout55", "Breakout55", default=False)),
        distance_to_high55=float(
            _value(raw, "distance_to_high55", "DistanceToHigh55", default=0.0)
        ),
    )


def _normalise_prices(prices: Mapping[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    result: dict[str, pd.DataFrame] = {}
    required = {"Open", "High", "Low", "Close"}
    for symbol, frame in prices.items():
        if frame is None or frame.empty:
            continue
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{symbol} is missing price columns: {sorted(missing)}")
        clean = frame.copy()
        clean.index = pd.to_datetime(clean.index).normalize()
        clean = clean[~clean.index.duplicated(keep="last")].sort_index()
        result[str(symbol).upper()] = clean
    return result


def _execution_price(raw_price: float, slippage_bps: float, *, buying: bool) -> float:
    if raw_price <= 0 or not isfinite(raw_price):
        raise ValueError("execution price must be a positive finite number")
    adjustment = slippage_bps / 10_000.0
    return raw_price * (1.0 + adjustment if buying else 1.0 - adjustment)


def open_position(
    cash: float,
    signal: PortfolioSignal,
    entry_date: date,
    raw_entry_price: float,
    config: PortfolioConfig,
) -> tuple[Position | None, float]:
    """Open an affordable position and return the reconciled remaining cash."""
    if signal.trade_plan != config.actionable_trade_plan or signal.position_shares <= 0:
        return None, cash
    entry_price = _execution_price(raw_entry_price, config.slippage_bps, buying=True)
    affordable = int(max(0.0, cash - config.transaction_cost) / entry_price)
    shares = min(signal.position_shares, affordable)
    if shares <= 0:
        return None, cash
    debit = shares * entry_price + config.transaction_cost
    position = Position(
        symbol=signal.symbol,
        signal_date=signal.signal_date,
        entry_date=entry_date,
        entry_price=entry_price,
        shares=shares,
        entry_cost=config.transaction_cost,
        stop_loss=signal.stop_loss,
        take_profit_1=signal.take_profit_1,
        take_profit_2=signal.take_profit_2,
        score=signal.score,
        signal=signal.signal,
        trade_plan=signal.trade_plan,
        risk_reward=signal.risk_reward,
        market_regime=signal.market_regime,
        regime_score=signal.regime_score,
        rs_composite=signal.rs_composite,
        breakout55=signal.breakout55,
        distance_to_high55=signal.distance_to_high55,
    )
    return position, cash - debit


def close_position(
    position: Position,
    exit_date: date,
    raw_exit_price: float,
    reason: str,
    config: PortfolioConfig,
) -> tuple[ClosedTrade, float]:
    """Close a position and return the trade plus cash proceeds."""
    exit_price = _execution_price(raw_exit_price, config.slippage_bps, buying=False)
    gross_pnl = (exit_price - position.entry_price) * position.shares
    total_costs = position.entry_cost + config.transaction_cost
    net_pnl = gross_pnl - total_costs
    invested = position.entry_price * position.shares
    gross_return = gross_pnl / invested * 100.0
    net_return = net_pnl / invested * 100.0
    trade = ClosedTrade(
        symbol=position.symbol,
        signal_date=position.signal_date,
        entry_date=position.entry_date,
        exit_date=exit_date,
        entry_price=position.entry_price,
        exit_price=exit_price,
        position_size=position.shares,
        gross_return=gross_return,
        gross_pnl=gross_pnl,
        transaction_costs=total_costs,
        net_return=net_return,
        net_pnl=net_pnl,
        exit_reason=reason,
        market_regime=position.market_regime,
        score=position.score,
        rs_composite=position.rs_composite,
        breakout55=position.breakout55,
        distance_to_high55=position.distance_to_high55,
    )
    proceeds = exit_price * position.shares - config.transaction_cost
    return trade, proceeds


def mark_to_market(
    cash: float,
    positions: Mapping[str, Position] | Sequence[Position],
    prices: Mapping[str, float],
) -> tuple[float, float]:
    iterable = positions.values() if isinstance(positions, Mapping) else positions
    invested = 0.0
    for position in iterable:
        price = float(prices.get(position.symbol, position.entry_price))
        invested += position.shares * price
    return invested, cash + invested


def _next_session(frame: pd.DataFrame, signal_date: date) -> pd.Timestamp | None:
    future = frame.index[frame.index > pd.Timestamp(signal_date)]
    return future[0] if len(future) else None


def _exit_for_bar(
    position: Position,
    row: pd.Series,
    config: PortfolioConfig,
) -> tuple[float, str] | None:
    # Conservative daily-bar convention: if stop and target are both touched,
    # the stop is executed first because intraday ordering is unavailable.
    low = float(row["Low"])
    high = float(row["High"])
    close = float(row["Close"])
    if low <= position.stop_loss:
        return position.stop_loss, EXIT_STOP_LOSS
    if high >= position.take_profit_2:
        return position.take_profit_2, EXIT_TAKE_PROFIT
    if position.holding_sessions >= config.max_holding_sessions:
        return close, EXIT_TIME
    return None


def simulate_portfolio(
    signals: Iterable[Any],
    prices: Mapping[str, pd.DataFrame],
    config: PortfolioConfig | None = None,
    *,
    liquidate_at_end: bool = True,
) -> PortfolioResult:
    """Run a deterministic next-session-entry portfolio simulation.

    Signals are eligible at the next available session after SignalDate, which
    prevents same-bar execution.  Existing positions are processed before new
    entries each day.  Signals on the same day are ordered by score descending,
    then risk/reward descending, then symbol for deterministic cash allocation.
    """
    settings = config or PortfolioConfig()
    market = _normalise_prices(prices)
    normalised = [normalise_signal(item) for item in signals]
    eligible: list[tuple[pd.Timestamp, PortfolioSignal]] = []
    for signal in normalised:
        frame = market.get(signal.symbol)
        if frame is None or signal.trade_plan != settings.actionable_trade_plan:
            continue
        entry_session = _next_session(frame, signal.signal_date)
        if entry_session is not None:
            eligible.append((entry_session, signal))

    signals_by_date: dict[pd.Timestamp, list[PortfolioSignal]] = {}
    for session, signal in eligible:
        signals_by_date.setdefault(session, []).append(signal)
    for daily_signals in signals_by_date.values():
        daily_signals.sort(key=lambda s: (-s.score, -s.risk_reward, s.symbol))

    all_dates = sorted(
        set(signals_by_date).union(
            *(set(frame.index) for frame in market.values()) if market else [set()]
        )
    )
    if not all_dates:
        return PortfolioResult(settings.initial_cash, settings.initial_cash)

    cash = settings.initial_cash
    positions: dict[str, Position] = {}
    trades: list[ClosedTrade] = []
    curve: list[PortfolioState] = []
    last_prices: dict[str, float] = {}

    for session in all_dates:
        current_date = session.date()
        for symbol, position in list(positions.items()):
            frame = market[symbol]
            if session not in frame.index:
                continue
            row = frame.loc[session]
            position.holding_sessions += 1
            last_prices[symbol] = float(row["Close"])
            exit_decision = _exit_for_bar(position, row, settings)
            if exit_decision is not None:
                raw_exit, reason = exit_decision
                trade, proceeds = close_position(
                    position, current_date, raw_exit, reason, settings
                )
                cash += proceeds
                trades.append(trade)
                del positions[symbol]

        for signal in signals_by_date.get(session, []):
            if signal.symbol in positions or len(positions) >= settings.max_positions:
                continue
            row = market[signal.symbol].loc[session]
            raw_entry = float(row[settings.entry_price_field])
            new_position, cash = open_position(
                cash, signal, current_date, raw_entry, settings
            )
            if new_position is not None:
                positions[new_position.symbol] = new_position
                last_prices[new_position.symbol] = float(row["Close"])

        invested, equity = mark_to_market(cash, positions, last_prices)
        curve.append(
            PortfolioState(
                state_date=current_date,
                cash=cash,
                invested_value=invested,
                equity=equity,
                open_positions=len(positions),
                closed_trades=len(trades),
            )
        )

    if liquidate_at_end and positions:
        final_session = all_dates[-1]
        final_date = final_session.date()
        for symbol, position in list(positions.items()):
            frame = market[symbol]
            available = frame.index[frame.index <= final_session]
            if not len(available):
                continue
            raw_exit = float(frame.loc[available[-1], "Close"])
            trade, proceeds = close_position(
                position, final_date, raw_exit, EXIT_END_OF_DATA, settings
            )
            cash += proceeds
            trades.append(trade)
            del positions[symbol]
        curve.append(
            PortfolioState(
                state_date=final_date,
                cash=cash,
                invested_value=0.0,
                equity=cash,
                open_positions=0,
                closed_trades=len(trades),
            )
        )

    return PortfolioResult(
        initial_cash=settings.initial_cash,
        ending_cash=cash,
        open_positions=list(positions.values()),
        trade_log=trades,
        equity_curve=curve,
    )
