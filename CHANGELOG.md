## CHANGELOG

### v3.0.0 Integrated Walk-Forward Validation

#### Added
- `scanner/walkforward.py`
- `tests/test_walkforward.py`
- Rolling and expanding window generation
- Integrated train/test evaluation
- Walk-forward summaries
- Excel and CSV report export

#### Added Data Classes
- `WalkForwardConfig`
- `WalkForwardWindow`
- `EvaluationResult`
- `WalkForwardResult`
- `WalkForwardSummary`

#### Added Functions
- `generate_windows()`
- `run_walkforward_window()`
- `run_walkforward()`
- `evaluate_real_engines()`
- `run_walkforward_strategy()`
- `build_walkforward_summary()`
- `results_to_frame()`
- `factor_results_to_frame()`
- `build_walkforward_report()`
- `export_walkforward_report()`

#### Integrated Engines
- Point-in-time signal replay
- Deterministic portfolio simulation
- Structured trade-log processing
- Backtest metrics
- SPY benchmark analytics
- Observational factor validation

#### Replay-to-Portfolio Native Contract
Expanded `HistoricalSignal` and replay output with:
- `PositionShares`
- `StopLoss`
- `TakeProfit1`
- `TakeProfit2`

Replay now carries the production Risk Engine values required by `PortfolioSignal` and `simulate_portfolio()` without synthetic risk values.

#### Walk-Forward Capabilities
- Configurable training, testing and rolling-step lengths
- Rolling windows
- Expanding training windows
- Complete-test-period enforcement
- Chronological train/test separation
- Deterministic window ordering
- Per-window training and testing metrics
- Out-of-sample consistency score
- Average, best and worst test-return summaries
- Average test Sharpe ratio and Alpha
- Summary, Windows, Benchmark and Factor Validation report tables

#### Preserved
- Production filters and filter order
- Score Engine behaviour
- TradePlan logic
- Candidate ranking by TradePlan, Score and RiskReward
- Completed-session Volume Engine
- RelativeStrength = RS63 compatibility
- Three-state Market Regime Engine
- ATR risk calculations and position sizing
- Observational status of RSComposite, Breakout55 and DistanceToHigh55
- Production Excel and email reporting

#### Validation Results
- Ruff PASS
- MyPy PASS
- Unit Tests: 291 PASS
- Total Coverage: 92.71%
- `scanner/walkforward.py`: 95%
- `scanner/replay.py`: 90%

#### Release Status
Complete

# CHANGELOG

## v2.12.0 Factor Validation

### Added

- scanner/factor_validation.py
- tests/test_factor_validation.py

### Added Data Classes

- FactorDefinition
- FactorResult

### Added Functions

- validate_factor
- compare_factor_groups
- validate_factor_combinations
- validate_by_regime
- build_factor_validation_report
- export_factor_validation_report

### Added Capabilities

- Individual factor evaluation
- Factor-on vs factor-off comparison
- Factor combination analysis
- Market-regime analysis
- Benchmark-aware factor evaluation
- Sample-size reporting
- Evaluation-period reporting
- Excel factor-report export
- CSV factor-report export

### Validated Factors

- RegimeScore
- RSComposite
- Breakout55
- DistanceToHigh55

### Preserved

- Production filters
- Production filter order
- Score Engine behaviour
- TradePlan logic
- Candidate ranking
- Market Regime Engine
- Replay Engine
- Portfolio Simulation
- Benchmark Analytics
- Risk Engine

### Validation Results

- Ruff PASS
- MyPy PASS
- Unit Tests: 271 PASS
- Coverage: 92.36%
- scanner/factor_validation.py: 92%

### Release Status

Complete

## v2.11.0 Benchmark and Risk Analytics

### Added

- scanner/benchmark.py
- tests/test_benchmark.py

### Added Data Classes

- BenchmarkConfig
- BenchmarkResult

### Added Functions

- align_value_series
- align_return_series
- calculate_return_series
- calculate_beta
- calculate_tracking_error
- calculate_information_ratio
- calculate_total_return
- build_benchmark_metrics

### Validation Results

- Ruff PASS
- MyPy PASS
- Unit Tests: 258 PASS
- Coverage: 92.36%
- scanner/benchmark.py: 92%

## v2.10.0 Portfolio Simulation and Trade Log

### Added
- scanner/portfolio.py
- tests/test_portfolio.py

### Added data classes:
- PortfolioConfig
- PortfolioSignal
- Position
- ClosedTrade
- PortfolioState
- PortfolioResult

### Added functions:
- normalise_signal
- open_position
- close_position
- mark_to_market
- simulate_portfolio
- export_trade_log

### Validation Results
- Ruff PASS
- MyPy PASS
- Unit Tests: 232 PASS
- Coverage: 92.43%
- scanner/portfolio.py: 90%

## v2.9.0 Point-in-Time Signal Replay

### Added

- Added scanner/replay.py.
- Added tests/test_replay.py.
- Added HistoricalSignal.
- Added point_in_time_history().
- Added generate_signal().
- Added replay_symbol().
- Added replay_universe().
- Added point-in-time benchmark return calculation.
- Added historical signal generation.
- Added deterministic replay support.
- Added market-regime provider support.
- Added production-engine integration support.

### Production Engine Integration

Replay now executes the production pipeline using only data available on or before the signal date:

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

The replay framework now reuses existing production:

- Filters
- Score Engine
- TradePlan logic
- Relative Strength
- Market Regime
- Breakout diagnostics
- ATR Risk Engine

### Added Tests

Added replay-foundation tests:

- Point-in-time history
- Deterministic replay
- HistoricalSignal validation
- Replay symbol
- Replay universe
- Required signal fields
- Future row isolation

Added production-integration tests:

- Indicator integration
- Filter integration
- Score integration
- Risk integration
- Benchmark return generation
- Benchmark future-row isolation
- Market-regime provider
- Invalid market regime handling
- Production pipeline failures
- Empty replay output validation

### Validation Results

- Ruff: PASS
- MyPy: PASS
- Unit Tests: 215 PASS
- Coverage: 93.45%
- scanner/replay.py: 90%

### Preserved

- Production filters
- Production filter order
- Candidate ranking
- Completed-session Volume Engine
- Relative Strength calculations
- Market Regime Engine
- Breakout diagnostics
- ATR Risk Engine
- Excel reporting
- Email reporting

### Completed Objectives

- Historical signal generation
- Point-in-time data isolation
- Look-ahead-bias prevention
- Deterministic replay
- Production-engine integration

## v2.8.0 Backtest Metrics Foundation

### Added

- Added `scanner/backtest.py`.
- Added `tests/test_backtest.py`.
- Added the `Trade` data class for representing completed trades.
- Added the `BacktestResult` data class for representing consolidated backtest results.
- Added individual trade-return calculation.
- Added maximum-drawdown calculation.
- Added CAGR calculation.
- Added annualised Sharpe ratio calculation.
- Added annualised Sortino ratio calculation.
- Added profit-factor calculation.
- Added trade-expectancy calculation.
- Added total-return calculation.
- Added benchmark-return comparison.
- Added Alpha calculation.
- Added consolidated backtest metrics generation through `build_metrics`.

### Performance Metrics

The initial Backtest Metrics Foundation supports:

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

### Added Tests

- Added positive trade-return validation.
- Added negative trade-return validation.
- Added floating-point trade-return comparison using `pytest.approx`.
- Added maximum-drawdown validation.
- Added profit-factor validation.
- Added expectancy validation.
- Added required-metrics validation.
- Added Alpha calculation validation.

### Changed

- Updated the unit-test baseline from 179 tests to 186 tests.
- Added an isolated performance-analytics module without changing the existing stock-scanner execution flow.
- Established v2.8.0 as the first incremental implementation step towards v3.0.0 Walk-Forward Validation.
- Continued sequential numeric versioning without release-candidate suffixes.

### Preserved

- Preserved all v2.7.0 Breakout Engine behaviour.
- Preserved all v2.6.x Market Regime Engine behaviour.
- Preserved production filters and filter order.
- Preserved Score Engine behaviour.
- Preserved TradePlan logic.
- Preserved candidate ranking by TradePlan, Score and RiskReward.
- Preserved completed-session Volume Engine behaviour.
- Preserved Relative Strength calculations.
- Preserved RSComposite calculations.
- Preserved MarketRegime and RegimeScore behaviour.
- Preserved Breakout55 and DistanceToHigh55 diagnostics.
- Preserved ATR risk management and position sizing.
- Preserved Excel reporting.
- Preserved email reporting.
- Preserved the observational status of RSComposite, Breakout55 and DistanceToHigh55.

### Scope

v2.8.0 provides reusable performance calculations for trade returns and equity curves.

It does not yet provide a complete portfolio backtesting or walk-forward validation engine.

The following capabilities remain planned for later numeric releases:

- Point-in-time signal generation
- Historical scanner replay
- Look-ahead-bias protection
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

### Validation Results

- Unit Tests: 186 PASS
- Backtest Tests: 7 PASS
- Existing regression tests: PASS
- Ruff: Final verification required
- MyPy: Final verification required

### Release Status

Backtest Metrics Foundation Complete

This release establishes the performance-metrics layer required by the future portfolio simulation and walk-forward validation engine.

It does not change live scanner filters, scores, ranking, TradePlan decisions or position-sizing behaviour.

## v2.7.0 Breakout Engine

### Added
- Added Breakout55 diagnostics.
- Added DistanceToHigh55 diagnostics.
- Added Breakout55 to indicator output.
- Added DistanceToHigh55 to indicator output.
- Added Breakout diagnostics to scanner candidate output.
- Added Breakout diagnostics to Excel Top20 reporting.
- Added Breakout diagnostics to email reporting.
- Added comprehensive breakout-engine validation tests.

### Added Tests
- Breakout55 above-prior-high validation.
- Breakout55 below-prior-high validation.
- Breakout55 equal-prior-high validation.
- DistanceToHigh55 positive validation.
- DistanceToHigh55 negative validation.
- Percentage-formula validation.
- Latest-bar exclusion validation.
- Custom-lookback validation.
- Invalid-input validation.
- Ranking-preservation validation.
- Output-column preservation validation.
- Breakout-output column vallidation.
- Ranking-column preservation validation.
- Breakout diagnostic reporting validation.

### Preserved
- Preserved all v2.6.1 Market Regime logic.
- Preserved all production filters.
- Preserved Score Engine behaviour.
- Preserved ranking order.
- Preserved Volume Engine.
- Preserved Relative Strength calculations.
- Preserved ATR risk management.
- Preserved Excel reporting.
- Preserved email reporting.

### Validation Results
- Ruff: PASS
- MyPy: PASS
- Unit Tests: 179 PASS

### Release Status
Production Ready

## v2.6.1 Market Regime Test Expansion

### Added
- Added dedicated Bull market-regime tests.
- Added dedicated Neutral market-regime tests.
- Added dedicated Bear market-regime tests.
- Added RegimeScore validation tests.
- Added Market Regime summary-report validation.
- Added Market Regime email-report validation.
- Added boundary-condition validation around the 3% neutral band.
- Added main() orchestration tests covering:
  - BEAR early-exit path
  - BULL scan path
  - NEUTRAL scan path
  - Local test-mode path
- Added regression tests for candidate ranking, report generation and email generation.

### Changed
- Expanded scanner.py regression protection from 68% coverage to 99%.
- Expanded total project coverage from 83.12% to 94.61%.
- Increased automated validation around MarketRegime and RegimeScore reporting.

### Preserved
- Preserved all v2.6.0 market-regime logic.
- Preserved the 3% neutral band around SPY MA200.
- Preserved RegimeScore values:
  - BULL = 15
  - NEUTRAL = 7
  - BEAR = 0
- Preserved production filters.
- Preserved ranking by TradePlan, Score and RiskReward.
- Preserved Volume Engine behaviour.
- Preserved Relative Strength calculations.
- Preserved Excel and email reporting.

### Validation Results
- Ruff: PASS
- MyPy: PASS
- Unit Tests: 157 PASS
- scanner.py Coverage: 99%
- Total Coverage: 94.61%

### Release Status
Production Ready

## v2.6.0 Three-State Market Regime Engine

### Added
- Added BULL, NEUTRAL and BEAR market-regime classification.
- Added a configurable 3% neutral band around the S&P 500 MA200.
- Added RegimeScore values of 15 for BULL, 7 for NEUTRAL and 0 for BEAR.
- Added MarketRegime and RegimeScore to candidate results.
- Added regime information to console, Excel summary and diagnostic email output.
- Added reusable regime classification and score constants to the market-data module.

### Changed
- Updated scanner version, Excel filename and email subjects to v2.6.0.
- Updated the Score Engine to use RegimeScore as the market component.
- Retained MarketScore as a backwards-compatible alias of RegimeScore.
- Changed bear protection to exit only when the three-state regime is BEAR.
- Allowed NEUTRAL scans to continue with a reduced seven-point regime contribution.

### Preserved
- Preserved all production filters and filter order.
- Preserved candidate ranking by TradePlan, Score and RiskReward.
- Preserved the completed-session Volume Engine.
- Preserved multi-timeframe Relative Strength and RSComposite calculations.
- Preserved ATR risk management and position sizing.
- Preserved the five-sheet diagnostic workbook.
- Preserved the market_bull and MarketScore compatibility fields.

### Validation Baseline
- Ruff passes.
- MyPy passes.
- 134 unit tests pass.
- Total coverage above 80%.

### Release Status

Production ready

Validation Results:
- Ruff: PASS
- MyPy: PASS
- Unit Tests: 134 PASS
- Coverage: 81.51%

## v2.5.3 Indicator Hardening Release

### Added
- Added comprehensive indicator-engine unit tests.
- Added completed-session Volume Engine validation.
- Added RSI validation tests.
- Added MACD validation tests.
- Added Bollinger Band validation tests.
- Added ADX validation tests.
- Added Relative Strength benchmark-comparison tests.
- Added timezone and market-session tests.
- Added indicator failure-path regression tests.

### Changed
- Increased minimum CI coverage requirement from 70% to 80%.
- Expanded automated regression protection around technical-indicator calculations.

### Validation
- Ruff must pass.
- MyPy must pass.
- All unit tests must pass.
- Scanner package coverage must remain above 80%.

### Metrics
- Total Tests: 134
- Coverage: 83.30%

## v2.5.2 Test Coverage Expansion

#### Added
- Added comprehensive unit tests for the download module.
- Added tests for safe download validation, retry outcomes and invalid market data.
- Added tests for S&P 500 symbol loading and fallback behaviour.
- Added tests for multi-horizon market-context calculation.
- Added comprehensive unit tests for scanner orchestration and structured outcomes.
- Added tests for Passed, Filtered, Data Failure, Indicator Failure and Processing Error outcomes.
- Added tests for market-breadth statistics.
- Added tests for candidate ranking.
- Added tests for diagnostic report-frame generation.
- Added tests for five-sheet Excel export.
- Added tests for diagnostic email-body generation.
- Added mocked SMTP and bear-market email tests.
- Increased the minimum CI coverage gate from 30% to 70%.

#### Changed
- Updated scanner version, report filename and email subject to v2.5.2.
- Combined unit-test and coverage execution into one CI step.
- Expanded automated regression validation around download and scanner orchestration.
- Corrected documentation references from v2.5.0 to the current maintenance release where appropriate.

#### Fixed
- Corrected spelling and wording issues in the v2.5.1 changelog.
- Prevented external downloads and email delivery during unit testing through dependency mocking.
- Fixed report-frame generation so both empty and non-empty Top20 results return all five report DataFrames.

#### Preserved
- Preserved all v2.5.0 multi-timeframe Relative Strength calculations.
- Preserved RelativeStrength as an alias of RS63.
- Preserved the v2.4.1 production filters and filter order.
- Preserved the v2.4.1 Score Engine formula and thresholds.
- Preserved the completed-session Volume Engine.
- Preserved ATR risk management and position sizing.
- Preserved candidate ranking by TradePlan, Score and RiskReward.
- Preserved all five diagnostic Excel worksheets.
- Preserved production email and bear-market alert behaviour.

#### Validation
- Ruff lint validation must pass.
- MyPy type checking must pass.
- All unit tests must pass.
- Total scanner-package coverage must remain at or above 50%.
- Tests must not require live market data, network access or SMTP credentials.

#### Purpose
- Increase regression protection for data acquisition and scanner orchestration.
- Validate diagnostic outputs without running a live market scan.
- Establish a stronger testing baseline before the v2.6.0 Market Regime Engine.

## v2.5.1 Stability + CI Release

### Added

- Added GitHub CI pipeline.
- Added Ruff lint validation.
- Added MyPy type checking.
- Added pytest coverage reporting.
- Added minimum 30% coverage gate.
- Added pyproject.toml development configuration.

### Changed

- Introduced an initial 30% coverage gate.
- Updated scanner version to v2.5.1.
- Standardized automated quality validation for every pull request.

### Preserved

- Preserved all v2.5.0 Relative Strength functionality.
- Preserved Volume Engine behaviour.
- Preserved Risk Engine calculations.
- Preserved diagnostic reporting.
- Preserved ranking logic.

### Purpose

- Establish CI baseline before increasing test coverage in future releases.
- Improve software quality and deployment confidence.
- Prevent regressions before production releases.

## v2.5.0 Multi-Timeframe Relative Strength

### Added

- Added benchmark returns for 21, 63, 126 and 252 sessions.
- Added stock-versus-benchmark Relative Strength fields:
  - RS21
  - RS63
  - RS126
  - RS252
- Added `RSComposite` using 15% RS21, 50% RS63, 25% RS126 and 10% RS252.
- Added the five v2.5 RS fields to candidate results, console output, Excel and email.
- Added `Non-negative RSComposite` to Market Breadth.
- Added helper functions for period-return and multi-horizon Relative Strength calculation.
- Added a v2.5 validation checklist to README.
- Added `UPGRADE_PLAN_V3.md` with the incremental roadmap to v3.0.

### Changed

- Updated scanner version, email subject and Excel filename to v2.5.0.
- Increased default price-history download from one year to two years.
- Increased minimum indicator history to 253 observations for RS252.
- Expanded market context with `spy_returns`, while preserving the existing `spy_return` 63-session key.
- Updated module documentation to distinguish new research factors from unchanged production logic.

### Preserved

- Preserved all v2.4.1 structured diagnostic outcomes.
- Preserved the five-sheet diagnostic workbook.
- Preserved first-rejection and all-failed-condition reporting.
- Preserved completed-session Volume Engine behaviour and 16:15 New York cutoff.
- Preserved all production filters and their order.
- Preserved the v2.4.1 Score Engine formula and signal thresholds.
- Preserved ranking by TradePlan, Score and RiskReward.
- Preserved ATR stops, targets and position sizing.
- Preserved email attachment and bear-market alert behaviour.

### Compatibility

- `RelativeStrength` remains equal to `RS63`.
- Existing filtering and scoring therefore continue to use the same 63-session Relative Strength concept.
- RSComposite is informational in v2.5.0 and does not change filter, score or ranking outcomes.

### Validation Notes

- Stocks with fewer than 253 observations are reported through the existing Indicator Failure path.
- Compare v2.5.0 against v2.4.1 using the same market snapshot before setting v2.5.0 as the production baseline.

## v2.4.1 Diagnostic Reporting

### Added

- Added structured scan outcomes for Passed, Filtered, Data Failure, Indicator Failure and Processing Error.
- Added first-rejection statistics for the production filter funnel.
- Added all-failed-condition statistics by evaluating every applicable filter.
- Added market-breadth counts for MA, RSI, volume and relative strength conditions.
- Added a five-sheet Excel diagnostic workbook:
  - Top20
  - Scan Summary
  - First Rejections
  - All Failed Conditions
  - Market Breadth
- Added Excel filtering, frozen headers and automatic column widths.
- Added a diagnostic email body with summary, rejection and breadth sections.
- Added an Excel attachment even when zero stocks pass.
- Added console Scan Summary and Top First-Fail Reasons.

### Changed

- Updated scanner version, email subject and Excel filename to v2.4.1.
- Changed scanner outcomes from a simple result-or-None pattern to a structured diagnostic result.
- Preserved the v2.4 candidate ranking order: TradePlan, Score and RiskReward.
- Kept the v2.4 completed-session Volume Engine and Risk Engine logic unchanged.

### Purpose

- Makes `No stocks passed the technical filters` an auditable scanner result.
- Helps distinguish a weak market from overly restrictive filters, incomplete data or processing errors.

## v2.4 Final

### Added

- Added ATR-based risk management, stop loss, take-profit targets and position sizing.
- Added the automatic completed-session Volume Engine.
- Added risk and volume fields to Excel and email output.
- Added TradePlan ranking.

### Fixed

- Fixed partial intraday volume distorting VolumeRatio.
- Fixed capital-required calculation.
- Fixed ranking parameter consistency and Signal spelling.

## v2.3 Modular Stable

### Added

- Split the scanner into download, indicator, filter, score and scanner modules.

## v3.0 Planned

- Enhanced market regime and historical breadth.
- Sector rotation and sector-relative strength.
- Breakout and pocket-pivot detection.
- Portfolio allocation and exposure control.
- Trade journal, outcome tracking and backtesting.
