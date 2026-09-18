## US Stock Scanner v2.6.1

v2.6.1 is an engineering-quality release focused on expanding
automated validation for the v2.6.0 Market Regime Engine.

The release adds:

- Dedicated Bull regime tests.
- Dedicated Neutral regime tests.
- Dedicated Bear regime tests.
- RegimeScore validation tests.
- MarketRegime reporting validation.
- Email reporting validation.
- Summary-report validation.

No trading logic has changed.

Coverage Goals:
- scanner.py > 80%
- project coverage > 85%

### Continuous Integration

Every push and pull request automatically executes:

- Ruff lint validation
- MyPy type checking
- Pytest unit tests
- Scanner-package coverage validation

Quality gates:

- Lint must pass.
- Type checking must pass.
- All tests must pass.
- Total scanner-package coverage must remain at least 80%.

The unit tests use mocks for Yahoo Finance downloads, SMTP email delivery and scanner dependencies. CI therefore does not require live market data or email credentials.

### Engineering Metrics

Current quality metrics:

- Ruff: Passing
- MyPy: Passing
- Unit Tests: 157
- Coverage: 94.61%

Coverage by module:
- download.py: 100%
- filter.py: 100%
- indicator.py: 94%
- risk.py: 84%
- score.py: 81%
- scanner.py: 99%

### Overview

v2.6.0 adds a three-state Market Regime Engine to the tested v2.5.3 engineering baseline.

The v2.6.0 release adds:

- BULL, NEUTRAL and BEAR market regimes.
- A 3% neutral band around the S&P 500 200-session moving average.
- RegimeScore values of 15, 7 and 0 for BULL, NEUTRAL and BEAR.
- Regime fields in scoring, candidate output, Excel summaries, console output and email.
- Bear-market early exit only when the regime is BEAR.

v2.6.0 changes only the market component of scoring. Production filters, ranking, Volume Engine, Risk Engine and Relative Strength logic remain unchanged.

The release preserves:

- The modular scanner structure.
- The completed-session Volume Engine.
- The v2.4.1 production filters.
- The v2.4.1 Score Engine and score thresholds.
- ATR stops, targets and position sizing.
- Multi-timeframe Relative Strength fields.
- Structured scan outcomes and rejection diagnostics.
- Five-sheet Excel reporting.
- Diagnostic email reporting.
- Bear-market early-exit behaviour.

### File Structure

scanner/scanner.py
: Scan flow, diagnostics, reporting, ranking and email.

scanner/download.py
: yfinance download, S&P 500 universe and market context.

scanner/indicator.py
: Technical indicators, completed-session Volume Engine and multi-timeframe Relative Strength.

scanner/filter.py
: Existing v2.4.1 production filter rules.

scanner/score.py
: Existing v2.4.1 scoring formula.

scanner/risk.py
: ATR stops, targets and position sizing.

tests/test_download.py
: Download validation, retry outcomes, universe loading and market-context tests.

tests/test_scanner.py
: Scanner outcomes, ranking, reporting, Excel and email tests.

tests/
: Existing filter, score, risk, volume, Relative Strength and market-context tests.

.github/workflows/ci.yml
: Ruff, MyPy, pytest and coverage validation.

.github/workflows/stock_scan.yml
: Production stock-scan workflow.

pyproject.toml
: Ruff and MyPy configuration.

requirements.txt
: Runtime and test dependencies.

CHANGELOG.md
: Full project history through v2.6.0.

UPGRADE_PLAN_V3.md
: Incremental roadmap from v2.5 to v3.0.

## v2.5 Relative Strength Expansion

v2.4.1 calculated one 63-session Relative Strength value:

```text
RelativeStrength = Stock 63-session return - benchmark 63-session return
```

v2.5.0 retains that field unchanged and adds:

```text
RS21  = Stock 21-session return  - benchmark 21-session return
RS63  = Stock 63-session return  - benchmark 63-session return
RS126 = Stock 126-session return - benchmark 126-session return
RS252 = Stock 252-session return - benchmark 252-session return
```

`RelativeStrength` remains an alias of `RS63`, so the existing filter and score behaviour remain compatible.

## RSComposite

The release adds an informational composite:

```text
RSComposite = 0.15 * RS21
            + 0.50 * RS63
            + 0.25 * RS126
            + 0.10 * RS252
```

The composite is included in console, Excel, email and market-breadth diagnostics. It does not change production score, filter or ranking logic in v2.5.0. This separation allows the new Alpha factor to be observed before it is promoted into ranking logic.

## Data History Change

The default yfinance history increases from one year to two years. At least 253 observations are required to calculate a complete 252-session return.

Stocks without enough history continue to use the existing `Indicator Failure` structured outcome with reason:

```text
Indicators unavailable or insufficient history
```

## Production Filters

The v2.4.1 rules are unchanged:

- Price at least $20
- Average volume at least 1,000,000 shares
- Price above MA20
- MA20 above MA50
- RSI between 40 and 80
- Completed-session VolumeRatio at least 0.8
- MACD not materially below signal
- 63-session RelativeStrength at least -5

## Score Engine

v2.6.0 replace the binary Bull/Bear market bonus with a three-state RegimeScore:

- BULL = 15
- NEUTRAL = 7
- BEAR = 0

The v2.4.1 categories and thresholds are unchanged:

- TrendScore
- MomentumScore
- StrengthScore based on 63-session RelativeStrength
- VolumeScore
- RegimeScore
- MarketScore (backwards-compatible alias)
- ADXScore
- RiskPenalty

Multi-timeframe RS does not alter Score in v2.5.0.

## Candidate Ranking

The v2.4.1 order remains unchanged:

1. TradePlan
2. Score
3. RiskReward

RSComposite is output for observation but is not yet a ranking tie-breaker.

## Completed-Session Volume Engine

The v2.4.1 logic remains unchanged:

- Before 16:15 New York time, today's daily bar is treated as incomplete and the preceding completed session is used.
- After 16:15 New York time, or when the latest bar is from an earlier date, the latest bar is used.
- Average volume uses the 20 sessions before the selected session.

## Diagnostics

Structured outcomes remain:

- Passed
- Filtered
- Data Failure
- Indicator Failure
- Processing Error

The filter engine still records:

- First rejection reason
- Every failed condition
- Market breadth

v2.5 adds `Non-negative RSComposite` to market breadth while keeping every existing breadth measure.

## Excel Workbook

Every successful bull-market scan creates the same five worksheets:

1. `Top20`
2. `Scan Summary`
3. `First Rejections`
4. `All Failed Conditions`
5. `Market Breadth`

The `Top20` sheet now includes `RS21`, `RS63`, `RS126`, `RS252` and `RSComposite`.

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

## v2.5 Validation Checklist

Before treating v2.5.0 as the new production baseline, compare it with a recent v2.4.1 run:

- Stocks Scanned should remain close to the loaded universe size.
- Data Failures should remain zero or explainably low.
- Processing Errors should remain zero.
- Indicator Failures may increase for stocks with fewer than 253 observations.
- Passed/Filtered behaviour should match v2.4.1 for stocks with sufficient history.
- Score and TradePlan should match v2.4.1 for the same market data.
- Five Excel sheets must be generated.
- Every Top20 row must contain all five RS fields.
- `RelativeStrength` and `RS63` must be equal.
- Email must include the multi-timeframe RS fields.

### v2.5.2 CI Validation Checklist

Before releasing v2.5.2:

- Ruff must report `All checks passed`.
- MyPy must complete without errors.
- All existing and new unit tests must pass.
- Total scanner-package coverage must remain at least 50%.
- Download tests must not perform live network requests.
- Scanner tests must not send real email.
- Excel export tests must create all five expected worksheets.
- Structured outcome tests must cover Passed, Filtered, Data Failure, Indicator Failure and Processing Error.
- Candidate ranking must remain TradePlan, Score and RiskReward.
- RelativeStrength must remain equal to RS63.
- Production filter and Score Engine behaviour must remain unchanged.

### Current Release

v2.6.1 Market Regime Test Expansion

Completed:
- Bull / Neutral / Bear regime tests
- RegimeScore validation
- Email reporting validation
- Summary reporting validation
- scanner.py coverage > 80%
- total package coverage > 85%

## Disclaimer

This project is research software and does not constitute financial advice. Market data may contain errors or revisions. Validate outputs independently before making any investment decision.
