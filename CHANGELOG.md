# CHANGELOG

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
