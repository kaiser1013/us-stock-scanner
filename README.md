# US Stock Scanner v2.12.0

US Stock Scanner is a modular stock-screening and research platform. It combines the stable production scanner with point-in-time replay, portfolio simulation, benchmark analytics and observational factor validation.

The current release is **v2.12.0 Factor Validation**.

## Current Validation Status

- Ruff: PASS
- MyPy: PASS
- Unit tests: 271 PASS
- Total coverage: 92.36%
- `scanner/factor_validation.py`: 92%

## Core Principles

The project preserves the established production engine while adding separate research and validation layers.

The following behaviour remains unchanged unless a future validated release explicitly documents otherwise:

- Production filters and filter order
- Score Engine behaviour
- TradePlan logic
- Candidate ranking
- Completed-session Volume Engine
- Relative Strength calculations
- Three-state Market Regime Engine
- ATR risk management
- Position sizing
- Five-sheet diagnostic workbook
- Diagnostic email reporting
- Bear-market alert behaviour

New research factors remain observational until historical, out-of-sample and walk-forward validation demonstrates a measurable improvement.

## System Architecture

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

### Research and Validation Platform

```text
Point-in-Time Signal Replay
    ↓
Portfolio Simulation and Trade Log
    ↓
Benchmark and Risk Analytics
    ↓
Factor Validation
```

The production scanner and research platform share the established indicator, filter, score and risk engines. Research modules must not silently alter live scanner behaviour.

## Production Filters

Production filters run in the following order.

### 1. Liquidity

- Price must be at least $20.
- Average volume must be at least 1,000,000 shares.

### 2. Trend

- Price must be at or above MA20.
- MA20 must be at or above MA50.

### 3. Momentum

- RSI must be between 40 and 80.
- Completed-session VolumeRatio must be at least 0.8.
- MACD must not be materially below the signal line.

### 4. Relative Strength

- 63-session RelativeStrength must be at least -5.

The filter engine records the first rejection reason and can evaluate every failed condition for diagnostic reporting.

## Indicator Engine

The Indicator Engine calculates technical, volume, Relative Strength and breakout metrics.

### Technical Indicators

- Price
- MA20
- MA50
- MA200
- RSI14
- MACD
- MACD Signal Line
- Bollinger middle and upper bands
- ADX
- PlusDI
- MinusDI

### Completed-Session Volume Engine

- Before 16:15 New York time, a current-day daily bar is treated as incomplete and the previous completed session is used.
- After 16:15 New York time, or when the latest bar is from an earlier date, the latest bar is used.
- Average volume uses the 20 sessions before the selected completed session.

Volume outputs include:

- LastVolume
- AvgVolume
- VolumeSource
- VolumeRatio
- RelativeVolumeLatest
- RelativeVolumePrevious

### Multi-Timeframe Relative Strength

The scanner calculates stock return minus benchmark return over four horizons:

```text
RS21  = Stock 21-session return  - Benchmark 21-session return
RS63  = Stock 63-session return  - Benchmark 63-session return
RS126 = Stock 126-session return - Benchmark 126-session return
RS252 = Stock 252-session return - Benchmark 252-session return
```

`RelativeStrength` remains an alias of `RS63` for compatibility with the production filter and Score Engine.

`RSComposite` is calculated as:

```text
RSComposite = 0.15 × RS21
            + 0.50 × RS63
            + 0.25 × RS126
            + 0.10 × RS252
```

At least 253 price observations are required for a complete 252-session Relative Strength calculation.

### Breakout Diagnostics

`Breakout55` is true when the latest close is greater than or equal to the highest high of the prior completed 55 sessions.

```text
DistanceToHigh55 = (Current Price / Prior 55-session High - 1) × 100
```

The latest session high is excluded from the reference window.

`RSComposite`, `Breakout55` and `DistanceToHigh55` remain observational. They do not participate in production filters, score calculation, TradePlan logic or candidate ranking.

## Market Regime Engine

The scanner uses three market-regime states:

- BULL
- NEUTRAL
- BEAR

RegimeScore values are:

```text
BULL    = 15
NEUTRAL = 7
BEAR    = 0
```

`MarketScore` remains a backwards-compatible alias of `RegimeScore`.

Bear protection exits the scan only when the market regime is BEAR. NEUTRAL scans continue with the reduced RegimeScore contribution.

## Score Engine

The production Score Engine combines:

- TrendScore
- MomentumScore
- StrengthScore based on 63-session RelativeStrength
- VolumeScore
- RegimeScore
- ADXScore
- RiskPenalty

The final score is constrained to the range from 0 to 100.

Signal classification:

```text
90-100  STRONG BUY
80-89   BUY
70-79   WATCH
60-69   MONITOR
Below 60 NO TRADE
```

Observational factors do not change the production score formula.

## Risk Engine

The Risk Engine provides:

- ATR14
- ATR-based StopLoss
- TakeProfit1
- TakeProfit2
- RiskPerShare
- RewardPerShare
- RiskReward
- PositionShares
- CapitalRequired
- PlannedRiskAmount
- TradePlan

Position sizing is limited by both account risk and available capital.

TradePlan classification:

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

Research and factor-validation outputs do not change this ranking order.

## Historical Replay

The point-in-time replay layer generates dated historical signals using only information available on or before each signal date.

The replay pipeline reuses the production engines:

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

The replay layer supports deterministic signal generation, benchmark replay and future-row isolation.

## Portfolio Simulation

The portfolio simulator converts historical signals into reproducible simulated positions.

Capabilities include:

- Cash accounting
- Open and closed position tracking
- Next-session entry processing
- Stop, target and time exits
- Position sizing
- Transaction costs
- Slippage
- Equity-curve generation
- Structured trade-log export

## Backtest Metrics

Available performance metrics include:

- Win rate
- Average gain
- Average loss
- Profit factor
- Expectancy
- Total return
- CAGR
- Sharpe ratio
- Sortino ratio
- Maximum drawdown
- Benchmark return
- Alpha

## Benchmark and Risk Analytics

The benchmark layer provides aligned portfolio-versus-benchmark analytics, including:

- Value-series alignment
- Return-series alignment
- Portfolio and benchmark total returns
- Beta
- Tracking error
- Information ratio
- Benchmark result export

Missing or non-overlapping benchmark observations are handled explicitly by the benchmark analytics layer.

## Factor Validation

The v2.12.0 Factor Validation layer evaluates observational factors before any production-promotion decision.

Validated factors:

- RegimeScore
- RSComposite
- Breakout55
- DistanceToHigh55

Capabilities include:

- Individual factor evaluation
- Baseline, factor-on and factor-off comparison
- Logical-AND factor-combination analysis
- BULL, NEUTRAL and BEAR regime analysis
- Benchmark-aware performance measurement
- Sample-size and evaluation-period reporting
- Excel report export
- CSV report export

Factor results can include:

- Sample size
- Start and end dates
- Win rate
- Average and median return
- Total and annualised return
- Annualised volatility
- Sharpe ratio
- Sortino ratio
- Maximum drawdown
- Benchmark return
- Alpha
- Beta
- Tracking error
- Information ratio

Factor Validation remains a research layer. It does not automatically promote any factor into production filters, scoring, TradePlan or ranking.

## Reporting and Diagnostics

Structured scanner outcomes include:

- Passed
- Filtered
- Data Failure
- Indicator Failure
- Processing Error

The diagnostic Excel workbook contains five worksheets:

1. Top20
2. Scan Summary
3. First Rejections
4. All Failed Conditions
5. Market Breadth

The scanner also supports diagnostic email reporting and bear-market alerts.

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
└── score.py

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
├── test_scanner.pySSSa
├── test_score.py
└── test_volume.py

.github/workflows/
├── ci.yml
├── stock_scan.yml
└── tests.yml

CHANGELOG.md
Project.txt
README.md
UPGRADE_PLAN_V3.md
pyproject.toml
requirements.txt
```

## Main Modules

- `scanner/scanner.py`: scan orchestration, diagnostics, ranking, Excel reporting and email reporting
- `scanner/download.py`: market-data download, universe loading and market context
- `scanner/indicator.py`: technical indicators, completed-session volume, Relative Strength and breakout diagnostics
- `scanner/filter.py`: ordered production filter rules
- `scanner/score.py`: production scoring and signal classification
- `scanner/risk.py`: ATR risk controls, targets, position sizing and TradePlan
- `scanner/backtest.py`: reusable backtest metrics
- `scanner/replay.py`: point-in-time historical signal replay
- `scanner/portfolio.py`: deterministic portfolio simulation and trade log
- `scanner/benchmark.py`: benchmark alignment and risk analytics
- `scanner/factor_validation.py`: observational factor evaluation and report export

## Installation

```bash
python -m pip install -r requirements.txt
```

## Environment Variables

### Risk Configuration

```text
ACCOUNT_SIZE=10000
RISK_PER_TRADE=0.01
ATR_STOP_MULTIPLIER=1.5
TP1_R_MULTIPLIER=1.5
TP2_R_MULTIPLIER=2.0
```

### Email Configuration

```text
EMAIL_USER
EMAIL_PASSWORD
EMAIL_TO
```

## Run

Use the repository entry point configured for the scanner. The current project documentation records:

```bash
python scanner.py
```

## Validation Commands

```bash
ruff check .
python -m mypy scanner
python -m pytest tests/ -v
```

Use the commands configured by `pyproject.toml` or the CI workflows if they differ from the examples above.

## Documentation

- `README.md`: current system behaviour, architecture and operation
- `CHANGELOG.md`: version-by-version implementation and validation history
- `UPGRADE_PLAN_V3.md`: incremental roadmap, promotion rules and production gates
- `Project.txt`: compact project context for future Copilot conversations

## Disclaimer

This project is research software and does not constitute financial advice. Market data may contain errors or revisions. Validate outputs independently before making any investment decision.
