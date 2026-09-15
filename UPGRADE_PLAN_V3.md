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

- Expand Bull/Bear into Bull/Neutral/Bear.
- Add explicit, auditable regime conditions.
- Add RegimeScore without deleting existing score components.
- Keep production filters unchanged during initial observation.

## Phase 3: v2.7.0 Breakout Engine

- Add Breakout55.
- Add DistanceToHigh55.
- Output breakout diagnostics before promoting them into rankings.
- Preserve all existing score fields and reports.

## Phase 4: v3.0.0 Walk-Forward Validation

- Add an independent `backtest.py`.
- Use point-in-time signal calculation without future data.
- Compare Top N portfolios against SPY.
- Export trade records, summary metrics, periodic returns and drawdown.
- Keep daily production scanning independent from research execution.

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
