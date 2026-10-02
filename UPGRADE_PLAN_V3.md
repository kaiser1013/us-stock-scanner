# US Stock Scanner v3.0 Incremental Upgrade Plan

## Guiding Principle

v2.4.1 is the proven production foundation. v2.5.0 and later releases must add functionality without removing stable diagnostics, reporting, filtering, Volume Engine, Risk Engine or email behaviour.

```text
v2.4.1 Production Engine
+ Alpha Layer
+ Validation Layer
= v3.0
```

## Phase 1: v2.5.0 Multi-Timeframe Relative Strength

Status: implemented in this package.

- Add RS21, RS63, RS126 and RS252.
- Add RSComposite.
- Preserve `RelativeStrength = RS63`.
- Preserve the production score, filters and ranking.
- Observe new fields before using them in live ranking.

## Phase 2: v2.6.0 Market Regime Engine

Status: implemented in this package.

Completed:
- Expand Bull/Bear into Bull/Neutral/Bear.
- Add explicit and auditable regime conditions.
- Add RegimeScore.
- Preserved production filters.
- Preserved ranking logic.
- Preserved Relative Strength logic.

## phase 2.1: v2.6.1 Market Regime Test Expansion

Status: completed

Objective:
- Add dedicated Bull, Neutral and Bear regime tests.
- Validate RegimeScore Behaviour.
- Validate scanner outputs containing MarketRegime.
- Validate Excel and email regime reporting.
- Increase scanner.py coverage to 80%+.
- Increase total package coverage to 85%+.

No trading logic changes.
Engineering-quality release only.

## Phase 3: v2.7.0 Breakout Engine

Status: implemented in this package.

Completed:

- Added Breakout55.
- Added DistanceToHigh55.
- Added Breakout diagnostics to candidate output.
- Added Breakout diagnostics to Top20 output.
- Added Breakout diagnostics to email reporting.
- Added Breakout diagnostics to Excel reporting.
- Added dedicated Breakout Engine validation tests.

Preserved:

- Production filters
- Score Engine
- Regime Engine
- TradePlan logic
- Candidate ranking

Breakout diagnostics remain observational and do not participate in ranking.

## Phase 4: v3.0.0 Walk-Forward Validation

Status: next release

Objectives:

- Add backtest.py.
- Point-in-time signal generation.
- Historical signal validation.
- Portfolio simulation.
- SPY benchmark comparison.
- Trade log export.
- Performance analytics.

## Phase 4.1 Factor Validation

Objectives:

- Validate RegimeScore performance.
- Validate RSComposite performance.
- Validate Breakout55 performance.
- Validate DistanceToHigh55 performance.
- Compare factor combinations.
- Export factor-performance reports.

Purpose:

Keep diagnostics separate from production ranking until statistical validation is complete.

## Required Backtest Metrics

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
- SPY benchmark return
- Alpha
- Beta
- Information ratio

## Production Gates

Every release must maintain:

- Data Failures at zero or an explainably low level.
- Processing Errors at zero.
- Indicator Failures below 1%, unless a documented history requirement explains the increase.
- All five diagnostic Excel sheets.
- Email report and attachment generation.
- Completed-session volume behaviour.
- Reproducible score and ranking for unchanged logic.

If an enhancement reduces stability, it must remain disabled until validated.
