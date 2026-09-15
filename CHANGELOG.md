# CHANGELOG

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

### v2.5.2 Test Coverage Expansion

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
