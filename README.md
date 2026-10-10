# US Stock Scanner v3.0.0

US Stock Scanner is a modular stock-screening, portfolio-research and validation platform. Version **v3.0.0 Integrated Walk-Forward Validation** connects point-in-time replay, native replay-to-portfolio signals, deterministic portfolio simulation, backtest metrics, SPY benchmark analytics and observational factor validation across sequential in-sample and out-of-sample windows.

## Current Validation Status

- Ruff: PASS
- MyPy: PASS
- Unit tests: 291 PASS
- Total coverage: 92.71%
- `scanner/walkforward.py`: 95%
- `scanner/replay.py`: 90%

## Core Principles

The research platform extends the stable production scanner without changing its validated trading rules.

The following production behaviour remains preserved:

- Production filters and filter order
- Score Engine behaviour
- TradePlan logic
- Candidate ranking
- Completed-session Volume Engine
- Relative Strength calculations
- Three-state Market Regime Engine
- ATR risk management and position sizing
- Five-sheet diagnostic workbook
- Diagnostic email reporting
- Bear-market alert behaviour

`RSComposite`, `Breakout55` and `DistanceToHigh55` remain observational. Walk-forward validation does not automatically promote a research factor into production filters, scoring, TradePlan or ranking.

## Architecture

### Production Scanner

```text
Market Data
    ↓
Indicator Engine
    ↓
Production Filters
    ↓
Score Engine
    ↓
Risk Engine
    ↓
Candidate Ranking
    ↓
Excel and Email Reporting
```

### Integrated Validation Platform

```text
Sequential Train/Test Windows
    ↓
Point-in-Time Replay
    ↓
HistoricalSignal
    ↓
Portfolio Simulation and Trade Log
    ↓
Backtest Metrics
    ├── SPY Benchmark Analytics
    └── Observational Factor Validation
    ↓
Walk-Forward Summary and Reports
```

## v3.0.0 Integrated Walk-Forward Validation

### Window Engine

`scanner/walkforward.py` supports:

- Rolling train/test windows
- Expanding training windows
- Configurable training, testing and step lengths
- Complete-test-period enforcement
- Chronological non-overlapping train/test boundaries
- Deterministic window ordering

Default configuration:

```text
Training period: 3 years
Testing period:  1 year
Rolling step:    1 year
```

Main data classes:

- `WalkForwardConfig`
- `WalkForwardWindow`
- `EvaluationResult`
- `WalkForwardResult`
- `WalkForwardSummary`

Main APIs:

- `generate_windows()`
- `run_walkforward_window()`
- `run_walkforward()`
- `evaluate_real_engines()`
- `run_walkforward_strategy()`
- `build_walkforward_summary()`
- `build_walkforward_report()`
- `export_walkforward_report()`

### Native Replay-to-Portfolio Contract

Historical replay now preserves the risk fields required by the portfolio simulator:

- `PositionShares`
- `StopLoss`
- `TakeProfit1`
- `TakeProfit2`

The complete replay signal also retains score, TradePlan, RiskReward, market regime, Relative Strength and breakout diagnostics. This allows `replay_universe()` output to be consumed directly by `simulate_portfolio()` without synthetic risk values.

### Integrated Evaluation Flow

For each training or testing period, `evaluate_real_engines()` coordinates:

```text
replay_universe()
    ↓
simulate_portfolio()
    ↓
build_benchmark_metrics()
    ↓
build_metrics()
    ↓
build_factor_validation_report()
```

The resulting `EvaluationResult` can contain:

- Historical signals
- Trade count
- Trade log
- Equity curve
- Backtest metrics
- Benchmark metrics
- Factor metrics
- Factor report tables

### Walk-Forward Summary

Cross-window out-of-sample summary fields include:

- Window count
- Profitable window count
- Consistency score
- Average test return
- Average test Sharpe ratio
- Average test Alpha
- Best test return
- Worst test return

The consistency score is the proportion of test windows with a positive total return.

### Walk-Forward Reporting

Walk-forward reports support Excel or CSV output with:

1. Summary
2. Windows
3. Benchmark
4. Factor Validation

## Production Filters

Production filters run in this order.

### 1. Liquidity

- Price must be at least $20.
- Average volume must be at least 1,000,000 shares.

### 2. Trend

- Price must be at or above MA20.
- MA20 must be at or above MA50.

### 3. Momentum

- RSI must be between 40 and 80.
- Completed-session VolumeRatio must be at least 0.8.
- MACD must not be materially below its signal line.

### 4. Relative Strength

- 63-session RelativeStrength must be at least -5.

## Indicator Engine

Technical and research outputs include:

- Price, MA20, MA50 and MA200
- RSI14
- MACD and signal line
- Bollinger middle and upper bands
- ADX, PlusDI and MinusDI
- Completed-session volume metrics
- RS21, RS63, RS126 and RS252
- RSComposite
- Breakout55
- DistanceToHigh55

`RelativeStrength` remains equal to `RS63` for production compatibility.

```text
RSComposite = 0.15 × RS21
            + 0.50 × RS63
            + 0.25 × RS126
            + 0.10 × RS252
```

At least 253 price observations are required for complete 252-session Relative Strength calculations.

## Completed-Session Volume Engine

- Before 16:15 New York time, a current-day daily bar is treated as incomplete and the previous completed session is used.
- After 16:15 New York time, or when the latest bar is historical, the latest bar is used.
- Average volume uses the 20 sessions before the selected completed session.

## Market Regime Engine

```text
BULL    = RegimeScore 15
NEUTRAL = RegimeScore 7
BEAR    = RegimeScore 0
```

`MarketScore` remains a compatibility alias of `RegimeScore`.

## Score Engine

The production score combines:

- TrendScore
- MomentumScore
- StrengthScore based on RS63
- VolumeScore
- RegimeScore
- ADXScore
- RiskPenalty

Final scores are constrained to 0 through 100.

```text
90-100  STRONG BUY
80-89   BUY
70-79   WATCH
60-69   MONITOR
Below 60 NO TRADE
```

## Risk Engine

Risk outputs include:

- ATR14
- StopLoss
- TakeProfit1
- TakeProfit2
- RiskPerShare
- RewardPerShare
- RiskReward
- PositionShares
- CapitalRequired
- PlannedRiskAmount
- TradePlan

```text
ACTIONABLE  Score ≥ 80 and RiskReward ≥ 2.0
WATCH       Score ≥ 70 and RiskReward ≥ 1.5
SKIP        All other cases, or zero position size
```

## Candidate Ranking

Production candidates remain ranked by:

```text
TradePlan → Score → RiskReward
```

## Historical Replay

The replay layer uses only observations available on or before each signal date and executes:

```text
Point-in-Time History
    ↓
calculate_indicators()
    ↓
run_filters()
    ↓
calculate_score()
    ↓
calculate_risk()
    ↓
HistoricalSignal
```

It supports benchmark replay, future-row isolation, deterministic replay and native portfolio risk fields.

## Portfolio Simulation

The portfolio simulator provides:

- Next-session entry processing
- Cash and position accounting
- Stop, target, time and end-of-data exits
- Position sizing
- Transaction costs and slippage
- Equity-curve generation
- Structured trade-log export
- Deterministic same-day allocation by score, RiskReward and symbol

## Performance and Benchmark Analytics

Backtest metrics include:

- Win rate
- Average gain and loss
- Profit factor
- Expectancy
- Total return
- CAGR
- Sharpe ratio
- Sortino ratio
- Maximum drawdown
- Benchmark return
- Alpha

Benchmark analytics add:

- Portfolio and benchmark date alignment
- Beta
- Tracking error
- Information ratio

## Factor Validation

The validation layer evaluates:

- RegimeScore
- RSComposite
- Breakout55
- DistanceToHigh55

Capabilities include individual-factor analysis, factor-on versus factor-off comparisons, logical-AND combinations, regime analysis, benchmark-aware metrics and Excel/CSV export.

## Reporting and Diagnostics

Structured scanner outcomes include:

- Passed
- Filtered
- Data Failure
- Indicator Failure
- Processing Error

The production diagnostic workbook retains:

1. Top20
2. Scan Summary
3. First Rejections
4. All Failed Conditions
5. Market Breadth

## Project Structure

```text
scanner/
├── __init__.py
├── backtest.py
├── benchmark.py
├── download.py
├── factor_validation.py
├── filter.py
├── indicator.py
├── portfolio.py
├── replay.py
├── risk.py
├── scanner.py
├── score.py
└── walkforward.py

tests/
├── test_backtest.py
├── test_benchmark.py
├── test_breakout.py
├── test_download.py
├── test_factor_validation.py
├── test_filters.py
├── test_indicator.py
├── test_main.py
├── test_market_context.py
├── test_market_regime.py
├── test_portfolio.py
├── test_regime_reporting.py
├── test_relative_strength.py
├── test_replay.py
├── test_risk.py
├── test_scanner.py
├── test_score.py
├── test_volume.py
└── test_walkforward.py
```

## Installation

```bash
python -m pip install -r requirements.txt
```

## Environment Variables

```text
ACCOUNT_SIZE=10000
RISK_PER_TRADE=0.01
ATR_STOP_MULTIPLIER=1.5
TP1_R_MULTIPLIER=1.5
TP2_R_MULTIPLIER=2.0

EMAIL_USER
EMAIL_PASSWORD
EMAIL_TO
```

## Run

```bash
python scanner.py
```

## Validation Commands

```bash
ruff check .
python -m mypy scanner
python -m pytest tests -v
```

## Documentation Responsibilities

- `README.md`: current system architecture, behaviour and operation
- `CHANGELOG.md`: version history and verified release results
- `UPGRADE_PLAN_V3.md`: completed incremental roadmap and production gates
- `Project.txt`: compact context for future Copilot conversations

## Disclaimer

This project is research software and does not constitute financial advice. Market data may contain errors or revisions. Validate outputs independently before making any investment decision.
