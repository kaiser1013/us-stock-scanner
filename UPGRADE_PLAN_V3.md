# US Stock Scanner v3.0 Incremental Upgrade Plan

## Guiding Principle

v2.4.1 is the proven production foundation.

Every later release must add functionality without removing or unintentionally changing stable:

- Diagnostics
- Reporting
- Production filters
- Filter order
- Score Engine behaviour
- TradePlan logic
- Candidate ranking
- Completed-session Volume Engine
- Relative Strength calculations
- Market Regime behaviour
- Risk Engine behaviour
- Excel output
- Email behaviour

```text
v2.4.1 Production Engine
+ Alpha Layer
+ Validation Layer
= v3.0.0
```

New factors must remain observational until historical and walk-forward validation demonstrates a measurable improvement.

## Versioning Strategy

Development uses sequential numeric releases.

Release-candidate suffixes such as `rc1` and `rc2` are not used.

Current working progression:

```text
v2.7.0  Breakout Engine
v2.8.0  Backtest Metrics Foundation
v2.9.0  Point-in-Time Signal Replay
v2.10.0 Portfolio Simulation and Trade Log
v2.11.0 Benchmark and Risk Analytics
v2.12.0 Factor Validation
v3.0.0  Integrated Walk-Forward Validation
```

Intermediate release names and scope may be adjusted when implementation requirements change, but numeric continuity should be preserved.

## Phase 1: v2.5.0 Multi-Timeframe Relative Strength

Status: Complete

Implemented:

- Added RS21.
- Added RS63.
- Added RS126.
- Added RS252.
- Added RSComposite.
- Preserved `RelativeStrength = RS63`.
- Preserved production filters.
- Preserved Score Engine behaviour.
- Preserved candidate ranking.
- Kept new Relative Strength fields observational.

## Phase 1.1: v2.5.1 Stability and CI

Status: Complete

Implemented:

- Added the GitHub CI pipeline.
- Added Ruff lint validation.
- Added MyPy type checking.
- Added pytest coverage reporting.
- Added project development configuration.
- Preserved production trading logic.

## Phase 1.2: v2.5.2 Test Coverage Expansion

Status: Complete

Implemented:

- Expanded download-module tests.
- Expanded scanner-orchestration tests.
- Added structured-outcome tests.
- Added report-generation tests.
- Added Excel-export tests.
- Added mocked email tests.
- Increased regression protection without changing production trading logic.

## Phase 1.3: v2.5.3 Indicator Hardening

Status: Complete

Implemented:

- Added indicator-engine tests.
- Added completed-session Volume Engine validation.
- Added RSI tests.
- Added MACD tests.
- Added Bollinger Band tests.
- Added ADX tests.
- Added Relative Strength benchmark tests.
- Added timezone and market-session tests.
- Added indicator failure-path regression tests.

## Phase 2: v2.6.0 Three-State Market Regime Engine

Status: Complete

Implemented:

- Expanded Bull/Bear classification into BULL, NEUTRAL and BEAR.
- Added explicit and auditable regime conditions.
- Added RegimeScore.
- Preserved production filters.
- Preserved candidate ranking.
- Preserved Relative Strength logic.
- Preserved completed-session Volume Engine behaviour.

RegimeScore values:

- BULL = 15
- NEUTRAL = 7
- BEAR = 0

## Phase 2.1: v2.6.1 Market Regime Test Expansion

Status: Complete

Implemented:

- Added dedicated BULL tests.
- Added dedicated NEUTRAL tests.
- Added dedicated BEAR tests.
- Validated RegimeScore behaviour.
- Validated scanner output containing MarketRegime.
- Validated summary reporting.
- Validated Excel and email regime reporting.
- Expanded scanner regression protection.

No trading-logic changes were introduced.

## Phase 3: v2.7.0 Breakout Engine

Status: Complete

Implemented:

- Added Breakout55.
- Added DistanceToHigh55.
- Added breakout diagnostics to candidate output.
- Added breakout diagnostics to Top20 output.
- Added breakout diagnostics to email reporting.
- Added breakout diagnostics to Excel reporting.
- Added dedicated Breakout Engine validation tests.

Preserved:

- Production filters
- Score Engine
- Market Regime Engine
- TradePlan logic
- Candidate ranking

Breakout diagnostics remain observational and do not participate in production ranking.

## Phase 4: v2.8.0 Backtest Metrics Foundation

Status: Complete

Implemented:

- Added `scanner/backtest.py`.
- Added `tests/test_backtest.py`.
- Added the `Trade` data class.
- Added the `BacktestResult` data class.
- Added trade-return calculation.
- Added maximum-drawdown calculation.
- Added CAGR calculation.
- Added Sharpe ratio calculation.
- Added Sortino ratio calculation.
- Added profit-factor calculation.
- Added expectancy calculation.
- Added total-return calculation.
- Added benchmark-return comparison.
- Added Alpha calculation.
- Added consolidated metrics generation through `build_metrics`.

Verified validation:

- Unit Tests: 186 PASS
- Backtest Tests: 7 PASS
- Existing regression tests: PASS

Final verification still required before recording a complete v2.8.0 engineering baseline:

- Ruff
- MyPy

Current limitations:

- No point-in-time scanner replay.
- No explicit look-ahead-bias protection layer.
- No portfolio position accounting.
- No portfolio cash accounting.
- No entry and exit execution engine.
- No transaction-cost model.
- No slippage model.
- No trade-log export.
- No aligned SPY return series.
- No Beta.
- No information ratio.
- No complete walk-forward validation.

## Phase 4.1: v2.9.0 Point-in-Time Signal Replay

Status: Complete

Primary objective:

Build the historical signal-generation layer before portfolio simulation.

Planned scope:

- Evaluate scanner conditions using historical point-in-time data.
- Generate dated historical signals.
- Prevent future observations from influencing historical signals.
- Reuse existing production filters without changing thresholds.
- Reuse existing Score Engine logic.
- Reuse existing TradePlan logic.
- Record market-regime values with each signal.
- Record Relative Strength and breakout diagnostics with each signal.
- Add deterministic historical replay tests.
- Keep live scanner execution unchanged.

Proposed signal fields for design and validation:

- SignalDate
- Ticker
- Price
- Score
- Signal
- TradePlan
- RiskReward
- MarketRegime
- RegimeScore
- RS21
- RS63
- RS126
- RS252
- RSComposite
- Breakout55
- DistanceToHigh55

The proposed field list is not yet an implemented interface.

Acceptance criteria:

- A historical signal must use only information available on or before its signal date.
- The same input snapshot must produce the same output.
- Historical replay must not modify the live scanner's production logic.
- Existing regression tests must continue to pass.
- New point-in-time tests must pass.
- Ruff must pass.
- MyPy must pass.
- The complete pytest suite must pass.

Verified Validation

- Ruff PASS
- MyPy PASS
- 215 Tests PASS
- Coverage 93.45%

Implemented

- HistoricalSignal
- point_in_time_history()
- generate_signal()
- replay_symbol()
- replay_universe()

Production Integration

- calculate_indicators()
- run_filters()
- calculate_score()
- calculate_risk()

Validated

- Historical signal generation
- Point-in-time replay
- Benchmark replay
- Deterministic replay
- Future-row isolation
- Production-engine integration

## Phase 4.2: v2.10.0 Portfolio Simulation and Trade Log

Status: Complete

Primary objective:

Convert dated historical signals into a reproducible portfolio simulation.

Planned scope:

- Convert historical signals into simulated positions.
- Track available cash.
- Track open positions.
- Track closed positions.
- Apply defined entry rules.
- Apply defined exit rules.
- Apply position-sizing rules.
- Generate a dated equity curve.
- Add configurable transaction costs.
- Add configurable slippage.
- Export a structured trade log.
- Connect completed trades and the equity curve to `build_metrics`.

Proposed trade-log fields:

- Symbol
- Signal date
- Entry date
- Exit date
- Entry price
- Exit price
- Position size
- Gross return
- Transaction costs
- Net return
- Exit reason
- Market regime
- Score
- RSComposite
- Breakout55
- DistanceToHigh55

The proposed trade-log fields are not yet an implemented interface.

Acceptance criteria:

- Portfolio cash must reconcile after every simulated transaction.
- Positions must not use unavailable future prices.
- The same inputs and configuration must produce the same trade log and equity curve.
- Transaction costs and slippage must be explicit and configurable.
- The complete regression suite must pass.

Verified Validation

- Ruff PASS
- MyPy PASS
- 232 Tests PASS
- Coverage 92.43%

## Phase 4.3: v2.11.0 Benchmark and Risk Analytics

Status: Planned

Primary objective:

Add aligned portfolio-versus-benchmark analytics.

Planned scope:

- Align portfolio returns with SPY returns.
- Add Beta.
- Add information ratio.
- Add tracking-error calculation if required by the information-ratio implementation.
- Validate benchmark-date alignment.
- Define handling for missing benchmark observations.
- Add benchmark-comparison tests.
- Export portfolio-versus-benchmark results.

Acceptance criteria:

- Portfolio and benchmark observations must use aligned dates.
- Missing benchmark data must be handled explicitly.
- Beta and information ratio must be covered by unit tests.
- Benchmark calculations must be reproducible.

## Phase 4.4: v2.12.0 Factor Validation

Status: Planned

Primary objective:

Evaluate observational factors before any production promotion decision.

Factors to validate:

- RegimeScore
- RSComposite
- Breakout55
- DistanceToHigh55

Planned scope:

- Measure factor performance individually.
- Compare factor combinations.
- Compare performance across market regimes.
- Compare portfolio results with and without each factor.
- Export factor-performance reports.
- Document sample size and evaluation period.
- Keep factors observational unless promotion gates are satisfied.

Factor validation must not automatically change filters, score, TradePlan or ranking.

## Phase 5: v3.0.0 Integrated Walk-Forward Validation

Status: Planned Major Release

Primary objective:

Integrate the completed validation layers into a reproducible walk-forward framework.

Planned scope:

- Integrate point-in-time signals.
- Integrate historical signal validation.
- Integrate portfolio simulation.
- Integrate trade-log export.
- Integrate SPY benchmark comparison.
- Integrate performance analytics.
- Integrate factor validation.
- Evaluate sequential historical windows.
- Separate in-sample and out-of-sample evaluation.
- Produce reproducible performance reports.
- Document any validated production changes.

v3.0.0 is complete only when the historical signal engine, portfolio simulation, benchmark analytics and walk-forward evaluation operate together.

## Required Backtest Metrics

Implemented in v2.8.0:

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

Planned:

- Beta
- Information ratio

## Observational-Factor Policy

The following factors remain observational:

- RSComposite
- Breakout55
- DistanceToHigh55

They must not affect:

- Production filters
- Score Engine
- TradePlan
- Candidate ranking

A factor may only be considered for production use after historical validation, out-of-sample testing, benchmark comparison and walk-forward evaluation.

## Production Gates

Every release must maintain:

- Data Failures at zero or an explainably low level.
- Processing Errors at zero.
- Indicator Failures below 1%, unless a documented history requirement explains the increase.
- All five diagnostic Excel worksheets.
- Email report and attachment generation.
- Completed-session Volume Engine behaviour.
- Reproducible score and ranking for unchanged logic.
- Production ranking by TradePlan, Score and RiskReward unless a validated release explicitly changes it.

Required engineering checks:

- Ruff lint validation
- MyPy type checking
- Complete pytest execution
- Configured coverage validation

If an enhancement reduces stability or cannot pass the production gates, it must remain disabled.

## Promotion Rule

A research factor may affect production filters, score, TradePlan or ranking only after:

1. Point-in-time historical validation.
2. Explicit look-ahead-bias controls.
3. Out-of-sample testing.
4. Walk-forward validation.
5. Benchmark comparison.
6. Regression-test coverage.
7. Documented evidence that the change improves the intended performance measure without unacceptable deterioration elsewhere.

## Documentation Update Rule

Before marking a release complete:

1. Confirm the implemented scope.
2. Run Ruff.
3. Run MyPy.
4. Run the complete pytest suite.
5. Record only verified results.
6. Update `Project.txt`.
7. Update `README.md`.
8. Update `CHANGELOG.md`.
9. Update `UPGRADE_PLAN_V3.md`.
10. Keep version numbers and release status consistent across all four files.
