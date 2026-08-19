# CHANGELOG

## v2.3 Modular Stable

### Added
- Split original scanner into 5 files:
    - "scanner py"
    - "download.py"
    - "indicator-py"
    - "filter.py"
    - "score.py"
- Added clearer production flow between download, indicator, filter and score logic.
- Updated email subject and Excel filename to use v2.3.
- Added README roadmap for v2.4 stop loss / take profit and v3.0 advanced trading system.

### Preserved
- S&P500 download logic.
- Test ticker fallback.
- Safe download retry logic.
- Bear market protection.
- Liquidity, trend, momentum and relative strength filters.
- Score engine and signal classification.
- Excel export and email delivery.

## v2.4 Planned
- Add ATR based stop loss.
- Add take profit targets.
- Add reward/risk calculation.
- Add suggested trade plan columns.

## v3.0 Planned
- Advanced market regime.
- Sector rotation.
- Position sizing.
- Breakout and pocket pivot detection.
- Portfolio allocation.
