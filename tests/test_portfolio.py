from datetime import date

import pandas as pd
import pytest

from scanner.portfolio import (
    ACTIONABLE,
    EXIT_END_OF_DATA,
    EXIT_STOP_LOSS,
    EXIT_TAKE_PROFIT,
    EXIT_TIME,
    PortfolioConfig,
    PortfolioSignal,
    close_position,
    mark_to_market,
    normalise_signal,
    open_position,
    simulate_portfolio,
)


def price_frame(rows):
    return pd.DataFrame(
        rows,
        columns=["Date", "Open", "High", "Low", "Close"],
    ).set_index("Date")


def signal(**overrides):
    values = {
        "signal_date": date(2025, 1, 2),
        "symbol": "AAA",
        "price": 100.0,
        "score": 85.0,
        "signal": "🟢 BUY",
        "trade_plan": ACTIONABLE,
        "position_shares": 10,
        "stop_loss": 95.0,
        "take_profit_1": 107.5,
        "take_profit_2": 110.0,
        "risk_reward": 2.0,
        "market_regime": "BULL",
        "regime_score": 15.0,
        "rs_composite": 12.0,
        "breakout55": True,
        "distance_to_high55": 1.5,
    }
    values.update(overrides)
    return PortfolioSignal(**values)


def test_normalise_signal_accepts_scanner_style_mapping():
    result = normalise_signal(
        {
            "SignalDate": "2025-01-02",
            "Ticker": "aaa",
            "Price": 100,
            "Score": 85,
            "Signal": "BUY",
            "TradePlan": ACTIONABLE,
            "PositionShares": 10,
            "StopLoss": 95,
            "TakeProfit1": 107.5,
            "TakeProfit2": 110,
            "RiskReward": 2,
            "MarketRegime": "BULL",
            "RegimeScore": 15,
            "RSComposite": 12,
            "Breakout55": True,
            "DistanceToHigh55": 1.5,
        }
    )
    assert result.symbol == "AAA"
    assert result.signal_date == date(2025, 1, 2)
    assert result.position_shares == 10


def test_config_rejects_invalid_values():
    with pytest.raises(ValueError):
        PortfolioConfig(initial_cash=0)
    with pytest.raises(ValueError):
        PortfolioConfig(slippage_bps=-1)
    with pytest.raises(ValueError):
        PortfolioConfig(entry_price_field="High")


def test_open_position_reconciles_cash_cost_and_slippage():
    config = PortfolioConfig(
        initial_cash=2_000,
        transaction_cost=5,
        slippage_bps=10,
    )
    position, cash = open_position(
        2_000, signal(), date(2025, 1, 3), 100.0, config
    )
    assert position is not None
    assert position.entry_price == pytest.approx(100.10)
    assert cash == pytest.approx(994.0)


def test_open_position_reduces_shares_to_available_cash():
    config = PortfolioConfig(initial_cash=250, transaction_cost=0)
    position, cash = open_position(
        250, signal(position_shares=10), date(2025, 1, 3), 100, config
    )
    assert position is not None
    assert position.shares == 2
    assert cash == pytest.approx(50)


def test_non_actionable_signal_does_not_open():
    config = PortfolioConfig()
    position, cash = open_position(
        1_000,
        signal(trade_plan="👀 WATCH"),
        date(2025, 1, 3),
        100,
        config,
    )
    assert position is None
    assert cash == 1_000


def test_close_position_calculates_gross_and_net_results():
    config = PortfolioConfig(transaction_cost=2)
    position, _ = open_position(
        2_000, signal(), date(2025, 1, 3), 100, config
    )
    assert position is not None
    trade, proceeds = close_position(
        position, date(2025, 1, 6), 110, EXIT_TAKE_PROFIT, config
    )
    assert trade.gross_pnl == pytest.approx(100)
    assert trade.transaction_costs == pytest.approx(4)
    assert trade.net_pnl == pytest.approx(96)
    assert trade.net_return == pytest.approx(9.6)
    assert proceeds == pytest.approx(1_098)


def test_mark_to_market_combines_cash_and_positions():
    config = PortfolioConfig()
    position, cash = open_position(
        2_000, signal(), date(2025, 1, 3), 100, config
    )
    assert position is not None
    invested, equity = mark_to_market(cash, [position], {"AAA": 105})
    assert invested == pytest.approx(1_050)
    assert equity == pytest.approx(2_050)


def test_simulation_enters_only_on_next_session_and_hits_target():
    prices = {
        "AAA": price_frame(
            [
                ("2025-01-02", 100, 102, 99, 101),
                ("2025-01-03", 102, 111, 101, 109),
            ]
        )
    }
    result = simulate_portfolio([signal()], prices)
    trade = result.trade_log[0]
    assert trade.entry_date == date(2025, 1, 3)
    assert trade.entry_price == pytest.approx(102)
    assert trade.exit_reason == EXIT_END_OF_DATA


def test_target_is_evaluated_after_entry_day():
    prices = {
        "AAA": price_frame(
            [
                ("2025-01-02", 100, 101, 99, 100),
                ("2025-01-03", 100, 109, 99, 105),
                ("2025-01-06", 106, 111, 105, 110),
            ]
        )
    }
    result = simulate_portfolio([signal()], prices)
    trade = result.trade_log[0]
    assert trade.exit_date == date(2025, 1, 6)
    assert trade.exit_price == pytest.approx(110)
    assert trade.exit_reason == EXIT_TAKE_PROFIT


def test_stop_has_priority_when_stop_and_target_touch_same_bar():
    prices = {
        "AAA": price_frame(
            [
                ("2025-01-02", 100, 101, 99, 100),
                ("2025-01-03", 100, 105, 98, 101),
                ("2025-01-06", 100, 112, 94, 101),
            ]
        )
    }
    result = simulate_portfolio([signal()], prices)
    assert result.trade_log[0].exit_reason == EXIT_STOP_LOSS
    assert result.trade_log[0].exit_price == pytest.approx(95)


def test_time_exit_occurs_at_configured_session_count():
    prices = {
        "AAA": price_frame(
            [
                ("2025-01-02", 100, 101, 99, 100),
                ("2025-01-03", 100, 104, 98, 101),
                ("2025-01-06", 101, 104, 98, 102),
                ("2025-01-07", 102, 104, 98, 103),
            ]
        )
    }
    result = simulate_portfolio(
        [signal()], prices, PortfolioConfig(max_holding_sessions=2)
    )
    trade = result.trade_log[0]
    assert trade.exit_date == date(2025, 1, 7)
    assert trade.exit_reason == EXIT_TIME
    assert trade.exit_price == pytest.approx(103)


def test_cash_reconciles_after_round_trip_without_costs():
    prices = {
        "AAA": price_frame(
            [
                ("2025-01-02", 100, 101, 99, 100),
                ("2025-01-03", 100, 105, 98, 100),
                ("2025-01-06", 100, 111, 99, 110),
            ]
        )
    }
    result = simulate_portfolio([signal()], prices)
    assert result.ending_cash == pytest.approx(10_100)
    assert result.ending_equity == pytest.approx(10_100)
    assert result.open_positions == []


def test_same_day_signals_are_allocated_deterministically_by_score():
    prices = {
        "AAA": price_frame(
            [("2025-01-02", 100, 101, 99, 100), ("2025-01-03", 100, 101, 99, 100)]
        ),
        "BBB": price_frame(
            [("2025-01-02", 100, 101, 99, 100), ("2025-01-03", 100, 101, 99, 100)]
        ),
    }
    signals = [
        signal(symbol="AAA", score=80, position_shares=10),
        signal(symbol="BBB", score=90, position_shares=10),
    ]
    result = simulate_portfolio(
        signals,
        prices,
        PortfolioConfig(initial_cash=1_000, max_positions=1),
    )
    assert result.trade_log[0].symbol == "BBB"


def test_simulation_is_deterministic():
    prices = {
        "AAA": price_frame(
            [
                ("2025-01-02", 100, 101, 99, 100),
                ("2025-01-03", 100, 105, 98, 100),
                ("2025-01-06", 100, 111, 99, 110),
            ]
        )
    }
    first = simulate_portfolio([signal()], prices)
    second = simulate_portfolio([signal()], prices)
    assert first.trade_log == second.trade_log
    assert first.equity_curve == second.equity_curve


def test_empty_inputs_return_unchanged_cash():
    result = simulate_portfolio([], {})
    assert result.initial_cash == 10_000
    assert result.ending_cash == 10_000
    assert result.trade_log == []
    assert result.equity_curve == []


def test_trade_log_and_equity_helpers(tmp_path):
    prices = {
        "AAA": price_frame(
            [("2025-01-02", 100, 101, 99, 100), ("2025-01-03", 100, 101, 99, 100)]
        )
    }
    result = simulate_portfolio([signal()], prices)
    frame = result.trade_log_frame()
    series = result.equity_curve_series()
    output = result.export_trade_log(tmp_path / "trades.csv")
    assert list(frame["symbol"]) == ["AAA"]
    assert series.name == "Equity"
    assert output.exists()


def test_missing_ohlc_columns_are_rejected():
    prices = {"AAA": pd.DataFrame({"Close": [100]}, index=["2025-01-03"])}
    with pytest.raises(ValueError, match="missing price columns"):
        simulate_portfolio([signal()], prices)
