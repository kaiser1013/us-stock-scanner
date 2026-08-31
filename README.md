# US Stock Scanner v2.4.1

## Overview

v2.4.1 is the diagnostics and reporting update built on v2.4 Final. It keeps the same modular scanner, completed-session Volume Engine and ATR Risk Engine, while making each run auditable even when zero stocks pass the technical filters.

## File Structure

```text
scanner.py      Scan flow, diagnostics, reporting, ranking and email
download.py     yfinance download, S&P500 universe and market regime
indicator.py    Technical indicators and automatic Volume Engine
filter.py       Filter rules and full filter evaluation
score.py        Score Engine and signal classification
risk.py         ATR stops, targets and position sizing
```

## v2.4.1 Diagnostic Flow

```text
Download stock
↓
Calculate indicators
↓
Record market-breadth conditions
↓
Evaluate every filter condition
↓
Record first rejection reason and all failed conditions
↓
Score and calculate risk for passed stocks
↓
Create Excel and email report even when Passed = 0
```

## Excel Workbook

Every run creates an Excel workbook with five sheets:

1. `Top20`
   - Ranked candidates and full technical/risk fields.
   - When no stock passes, the sheet is still created with column headers.

2. `Scan Summary`
   - Version and generation time.
   - Market status, SPY and SPY MA200.
   - Stocks scanned, passed and filtered.
   - Data failures, indicator failures and processing errors.
   - Pass rate.

3. `First Rejections`
   - Counts the first production filter that excluded each stock.
   - Useful for understanding the actual scanner funnel.

4. `All Failed Conditions`
   - Evaluates every applicable filter for each indicator-ready stock.
   - Useful for diagnosing filters that may be too restrictive.

5. `Market Breadth`
   - Price above MA20, MA50 and MA200.
   - MA20 above MA50.
   - RSI above 50.
   - VolumeRatio at least 0.8 and 1.0.
   - Non-negative relative strength.

Sheets include frozen headers, filters and practical column widths.

## Email Report

The email always includes:

- Market status and SPY context.
- Stocks scanned and indicator-ready.
- Passed, filtered and error counts.
- Top first-fail reasons.
- Market breadth counts.
- Top candidates when available.
- The diagnostics Excel workbook as an attachment.

A zero-candidate run is therefore a valid result rather than an empty report.

## Automatic Volume Engine

The existing v2.4 Volume Engine remains unchanged:

- Before 16:15 New York time, today's daily bar is treated as incomplete and the previous completed session is used.
- After 16:15 New York time, or when the latest bar belongs to an earlier date, the latest completed session is used.
- Average volume uses the 20 sessions before the selected session.

## Production Filters

- Price at least $20.
- Average volume at least 1,000,000 shares.
- Price above MA20.
- MA20 above MA50.
- RSI between 40 and 80.
- Completed-session VolumeRatio at least 0.8.
- MACD not materially below signal.
- RelativeStrength at least -5.

## Risk Environment Variables

```text
ACCOUNT_SIZE=10000
RISK_PER_TRADE=0.01
ATR_STOP_MULTIPLIER=1.5
TP1_R_MULTIPLE=1.5
TP2_R_MULTIPLE=2.0
```

## Required Email Environment Variables

```text
EMAIL_USER
EMAIL_PASSWORD
EMAIL_TO
```

## Validation Checklist

A healthy run should show:

- `Stocks Scanned` close to the loaded universe size.
- A reasonable number of `Indicator-ready stocks`.
- `Processing Errors` equal to zero or a clearly explainable small number.
- Rejection counts that add context to the candidate count.
- Market Breadth values that are not all zero.
- An Excel attachment even when no candidates pass.

## v3 Development Direction

v2.4.1 creates the diagnostic foundation for:

- Funnel and threshold analytics.
- Historical pass-rate tracking.
- Time-adjusted intraday relative volume.
- Market regime and breadth scoring.
- Sector rotation.
- Breakout and pocket-pivot detection.
- Trade-journal outcome tracking.
- Backtesting and parameter validation.
