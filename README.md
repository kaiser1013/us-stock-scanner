# US Stock Scanner v2.8.0

v2.8.0 introduces the Backtest Metrics Foundation.

The release adds reusable performance calculations for completed trades and equity curves without changing the live scanner's production filters, scoring, TradePlan logic, candidate ranking, risk management, Excel reporting or email reporting.

The Backtest Metrics Foundation is an incremental step towards the future integrated Walk-Forward Validation Engine. It is not yet a complete portfolio backtesting engine.

## Release Summary

v2.8.0 adds:

- `scanner/backtest.py`
- `tests/test_backtest.py`
- `Trade` data class
- `BacktestResult` data class
- Trade-return calculation
- Maximum-drawdown calculation
- CAGR
- Sharpe ratio
- Sortino ratio
- Profit factor
- Expectancy
- Total return
- Benchmark-return comparison
- Alpha
- Consolidated metrics generation through `build_metrics`

## Current Validation

Latest verified validation:

- Unit Tests: 186 PASS
- Backtest Tests: 7 PASS
- Existing regression tests: PASS
- Ruff: Final verification required
- MyPy: Final verification required

Do not record Ruff or MyPy as passing for v2.8.0 until fresh successful command output is available.

## Backtest Metrics Foundation

The initial performance-analytics layer supports:

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

### Backtest Data Classes

`Trade`

Represents a completed trade with:

- Entry date
- Exit date
- Symbol
- Entry price
- Exit price
- Return percentage

`BacktestResult`

Represents a consolidated backtest result with:

- Trades
- Equity curve
- Performance metrics

### Backtest Functions

`calculate_trade_return`

Calculates the percentage return between an entry price and an exit price.

`calculate_max_drawdown`

Calculates the largest percentage decline from a running equity peak.

`calculate_cagr`

Calculates compound annual growth using a 252-session trading-year assumption.

`calculate_sharpe_ratio`

Calculates an annualised Sharpe ratio from periodic returns.

`calculate_sortino_ratio`

Calculates an annualised Sortino ratio using negative returns as downside observations.

`calculate_profit_factor`

Calculates gross gains divided by absolute gross losses.

`calculate_expectancy`

Calculates expected return per trade from win rate, average gain and average loss.

`build_metrics`

Builds the standard backtest metrics dictionary from an equity curve, trade returns and an optional benchmark return.

## Current Backtest Scope

v2.8.0 provides reusable calculations for trade returns and equity curves.

It does not yet include:

- Point-in-time signal generation
- Historical scanner replay
- Explicit look-ahead-bias protection
- Portfolio position simulation
- Portfolio cash accounting
- Entry and exit execution
- Transaction-cost modelling
- Slippage modelling
- Trade-log export
- SPY return-series alignment
- Beta
- Information ratio
- Factor-combination validation
- Complete walk-forward validation

## Backtest Tests

`tests/test_backtest.py` validates:

- Positive trade returns
- Negative trade returns
- Floating-point comparisons using `pytest.approx`
- Maximum drawdown
- Profit factor
- Expectancy
- Required metrics
- Alpha

## Continuous Integration

Every push and pull request automatically executes the configured quality checks:

- Ruff lint validation
- MyPy type checking
- Pytest unit tests
- Scanner-package coverage validation

Quality gates:

- Lint must pass
- Type checking must pass
- All tests must pass
- Configured coverage validation must pass
- Existing production behaviour must remain stable

## Versioning Policy

The project uses sequential numeric versions.

Release-candidate suffixes such as `rc1` and `rc2` are not used.

Current working progression:

- v2.8.0 Backtest Metrics Foundation
- v2.9.0 Point-in-Time Signal Replay
- v2.10.0 Portfolio Simulation and Trade Log
- v2.11.0 Benchmark and Risk Analytics
- v2.12.0 Factor Validation
- v3.0.0 Integrated Walk-Forward Validation

Intermediate release names and scope may be adjusted when implementation requirements change.

## Preserved Production Behaviour

v2.8.0 preserves:

- Structured scanner outcomes
- Production filters and filter order
- Score Engine behaviour
- TradePlan logic
- Candidate ranking
- Completed-session Volume Engine
- Multi-timeframe Relative Strength
- Three-state Market Regime Engine
- Breakout diagnostics
- ATR risk management
- Position sizing
- Five-sheet Excel reporting
- Diagnostic email reporting
- Bear-market alert behaviour

## Candidate Ranking

The production ranking order remains:

1. TradePlan
2. Score
3. RiskReward

The Backtest Metrics Foundation does not change candidate ranking.

## Production Filters

The production filter rules remain:

- Price at least $20
- Average volume at least 1,000,000 shares
- Price above MA20
- MA20 above MA50
- RSI between 40 and 80
- Completed-session VolumeRatio at least 0.8
- MACD not materially below signal
- 63-session RelativeStrength at least -5

## Multi-Timeframe Relative Strength

The scanner calculates:

```text
RS21  = Stock 21-session return  - benchmark 21-session return
RS63  = Stock 63-session return  - benchmark 63-session return
RS126 = Stock 126-session return - benchmark 126-session return
RS252 = Stock 252-session return - benchmark 252-session return
```

`RelativeStrength` remains an alias of `RS63`, preserving existing filter and score behaviour.

### RSComposite

```text
RSComposite = 0.15 * RS21
            + 0.50 * RS63
            + 0.25 * RS126
            + 0.10 * RS252
```

RSComposite is included in console, Excel, email and market-breadth diagnostics.

It remains observational and does not change production filters, score, TradePlan or ranking.

### Data History Requirement

The default price-history download is two years.

At least 253 observations are required to calculate a complete 252-session return.

Stocks without sufficient history use the existing `Indicator Failure` outcome with the reason:

```text
Indicators unavailable or insufficient history
```

## Three-State Market Regime Engine

The scanner classifies the market as:

- BULL
- NEUTRAL
- BEAR

RegimeScore values:

- BULL = 15
- NEUTRAL = 7
- BEAR = 0

`MarketScore` remains a backwards-compatible alias of `RegimeScore`.

Bear protection exits the scan only when the market regime is BEAR.

NEUTRAL scans continue with a reduced seven-point RegimeScore contribution.

## Breakout Diagnostics

The Breakout Engine provides:

- Breakout55
- DistanceToHigh55

### Breakout55

```text
Latest close >= Highest high of the prior completed 55 sessions
```

### DistanceToHigh55

```text
(Current Price / Prior 55-session High - 1) * 100
```

The latest session high is excluded from the reference window.

Breakout diagnostics are exported to:

- Console output
- Candidate results
- Top20
- Excel reporting
- Diagnostic email reporting

Breakout diagnostics remain observational and do not participate in:

- Production filters
- Score calculation
- TradePlan logic
- Candidate ranking

## Observational Factors

The following factors remain observational:

- RSComposite
- Breakout55
- DistanceToHigh55

They must not affect production filters, score, TradePlan or ranking until historical and walk-forward validation demonstrates a statistically significant improvement.

## Completed-Session Volume Engine

The completed-session rules remain:

- Before 16:15 New York time, the current daily bar is treated as incomplete and the previous completed session is used.
- After 16:15 New York time, or when the latest bar is from an earlier date, the latest bar is used.
- Average volume uses the 20 sessions before the selected session.

## Score Engine

The Score Engine retains:

- TrendScore
- MomentumScore
- StrengthScore based on 63-session RelativeStrength
- VolumeScore
- RegimeScore
- MarketScore as a backwards-compatible alias
- ADXScore
- RiskPenalty

Multi-timeframe Relative Strength and the Backtest Metrics Foundation do not alter the production Score Engine.

## Diagnostics

Structured scanner outcomes:

- Passed
- Filtered
- Data Failure
- Indicator Failure
- Processing Error

The filter engine records:

- First rejection reason
- Every failed condition
- Market breadth

## Excel Workbook

Every successful scan produces the same five diagnostic worksheets:

1. `Top20`
2. `Scan Summary`
3. `First Rejections`
4. `All Failed Conditions`
5. `Market Breadth`

The Top20 results include multi-timeframe Relative Strength and breakout diagnostic fields.

## File Structure

```text
scanner/
âââ backtest.py
âââ download.py
âââ filter.py
âââ indicator.py
âââ risk.py
âââ scanner.py
âââ score.py

tests/
âââ test_backtest.py
âââ test_breakout.py
âââ test_download.py
âââ test_filters.py
âââ test_indicator.py
âââ test_main.py
âââ test_market_context.py
âââ test_market_regime.py
âââ test_regime_reporting.py
âââ test_relative_strength.py
âââ test_risk.py
âââ test_scanner.py
âââ test_score.py
âââ test_volume.py

.github/workflows/
âââ ci.yml
âââ stock_scan.yml

CHANGELOG.md
Project.txt
README.md
UPGRADE_PLAN_V3.md
pyproject.toml
requirements.txt
```

### Main Modules

`scanner/backtest.py`

Backtest data structures and reusable performance calculations.

`scanner/scanner.py`

Scan flow, diagnostics, reporting, ranking and email.

`scanner/download.py`

yfinance download, S&P 500 universe and market context.

`scanner/indicator.py`

Technical indicators, completed-session Volume Engine, multi-timeframe Relative Strength and breakout diagnostics.

`scanner/filter.py`

Production filter rules.

`scanner/score.py`

Production scoring formula.

`scanner/risk.py`

ATR stops, targets and position sizing.

## Environment Variables

### Risk

```text
ACCOUNT_SIZE=10000
RISK_PER_TRADE=0.01
ATR_STOP_MULTIPLIER=1.5
TP1_R_MULTIPLE=1.5
TP2_R_MULTIPLE=2.0
```

### Email

```text
EMAIL_USER
EMAIL_PASSWORD
EMAIL_TO
```

## Installation

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
python scanner.py
```

## Validation Commands

```bash
ruff check .
python -m mypy scanner
python -m pytest tests/ -v
```

Use the commands configured by the repository if its `pyproject.toml` or CI workflow specifies a different MyPy target.

## Next Planned Release

v2.9.0 Point-in-Time Signal Replay

Primary objective:

Build the historical point-in-time signal layer before portfolio simulation.

Planned scope:

- Evaluate scanner conditions using historical point-in-time data
- Generate dated historical signals
- Prevent future data from influencing historical signals
- Reuse existing production filters
- Reuse existing Score Engine logic
- Reuse existing TradePlan logic
- Record regime and diagnostic-factor data
- Add deterministic historical replay tests

The detailed interface remains a design task for v2.9.0 and is not part of v2.8.0.

## Roadmap

### v2.10.0 Portfolio Simulation and Trade Log

- Convert historical signals into simulated positions
- Track portfolio cash
- Track open and closed positions
- Apply entry and exit rules
- Apply position sizing
- Generate an equity curve
- Model transaction costs and slippage
- Export a structured trade log
- Connect simulation results to `build_metrics`

### v2.11.0 Benchmark and Risk Analytics

- Align portfolio returns with SPY returns
- Add Beta
- Add information ratio
- Validate benchmark alignment
- Export portfolio-versus-benchmark results

### v2.12.0 Factor Validation

- Validate RegimeScore
- Validate RSComposite
- Validate Breakout55
- Validate DistanceToHigh55
- Compare factor combinations
- Export factor-performance reports

### v3.0.0 Integrated Walk-Forward Validation

- Integrate point-in-time signals
- Integrate historical validation
- Integrate portfolio simulation
- Integrate trade-log export
- Integrate SPY benchmark comparison
- Integrate performance analytics
- Integrate factor validation
- Compare in-sample and out-of-sample results
- Produce reproducible performance reports

## Production Gates

Every release must maintain:

- Data Failures at zero or an explainably low level
- Processing Errors at zero
- Indicator Failures below 1%, unless a documented history requirement explains the increase
- All five diagnostic Excel worksheets
- Email report and attachment generation
- Completed-session Volume Engine behaviour
- Reproducible score and ranking for unchanged logic
- Ruff validation
- MyPy validation
- Full unit-test pass

If an enhancement reduces stability, it must remain disabled until validated.

## Current Release

v2.8.0 Backtest Metrics Foundation

Status:

- Backtest Metrics Foundation Complete
- 186 unit tests verified as passing
- Ruff final verification required
- MyPy final verification required

## Disclaimer

This project is research software and does not constitute financial advice.

Market data may contain errors or revisions. Validate outputs independently before making any investment decision.
