## US Stock Scanner

### Current Version
v2.3 Modular Stable

### Release Goal
建立可每日自動運行的 S&P500 Swing Trading Scanner，並由單一 `scanner.py` 拆分成清晰模組，方便 debug、維護及下一階段加入止賺止蝕。

## v2.3 Modular Architecture

### File Structure

```text
scanner.py      Main orchestration, Excel export, Email delivery
download.py     Download engine, S&P500 universe, market regime context
indicator.py    Technical indicators and raw metric calculation
filter.py       Liquidity, trend, momentum, relative strength filters
score.py        Score engine and signal classification
```

### Core Flow

```text
GitHub Actions
↓
scanner.py
↓
download.py: load S&P500 and market context
↓
indicator.py: calculate MA, RSI, MACD, Bollinger, Relative Strength, ADX
↓
filter.py: apply liquidity, trend, momentum and relative strength filters
↓
score.py: calculate score and signal
↓
scanner.py: Top20 ranking, Excel export and email delivery
```

## Existing Production Logic Preserved

### Market Universe
- S&P500 自動下載
- Test Mode 支援自訂股票列表
- GitHub Actions 自動執行

### Market Filter
- SPY / S&P500 Market Regime
- Index price > MA200 → Bull
- Index price < MA200 → Bear
- Bear Market：停止選股並發送 Bear Market Alert Email

### Filters
- Liquidity: Price > $20 and 20D average volume > 1M
- Trend: Price > MA20 and MA20 > MA50
- Momentum: RSI between 40 and 80, Volume Ratio > 0.8, MACD confirmation
- Relative Strength: 63 trading days return versus S&P500, Relative Strength > -5%

### Indicators
- MA20 / MA50 / MA200
- RSI(14)
- MACD and signal line
- Bollinger Bands
- Relative Strength
- ADX(14), +DI, -DI

### Score Engine

|Factor	| Max Score |
|---|---:|
| Trend | 30 |
| Momentum	| 20 |
| Relative Strength	| 15 |
| Volume	| 20 |
| Market	| 15 |
| ADX	| 6 |
| Risk Penalty	| -10 |

Final score is capped between 0 and 100.

### Signal Classification

| Score | Signal |
|---:|---|
| 90+	| 🔥 Strong Buy |
| 80+	| 🟢 Buy |
| 70+	| 🟡 Watch |
| 60+	| ⚪ Monitor |
| <60	| No Trade |

## v2.4 Planned: Take Profit and Stop Loss

### Goal
將 Scanner 由「選股排名」升級至「交易計劃建議」，但仍然保持 scanner 不直接落盤、不自動交易。

### Planned Additions
- ATR based stop loss
- Risk reward target
- Suggested stop loss price
- Suggested take profit 1 and take profit 2
- Risk per share
- Reward/risk ratio
- Optional trailing stop logic

### Suggested New File in v2.4

```text
risk.py         ATR, stop loss, take profit, reward/risk calculation
```

### Suggested Output Columns

```text
ATR14
StopLoss
TakeProfit1
TakeProfit2
RiskPerShare
RewardRiskRatio
TradePlan
```

## v3.0 Plan: Advanced Swing Trading Decision System

### Direction
v3.0 目標係由 Daily Stock Scanner 發展成更完整的 Swing Trading Decision System，重點唔單止係分數，而係市場環境、sector strength、risk management 同 portfolio exposure 一齊考慮。

### Planned Modules

```text
market.py       Enhanced market regime, index breadth, volatility filter
risk.py         ATR risk, stop loss, take profit, position sizing
pattern.py      Breakout, pocket pivot and base detection
sector.py       Sector rotation and sector relative strength
portfolio.py    Portfolio allocation and exposure control
report.py       Enhanced Excel and email report
config.py       Central configuration
```

### v3.0 Feature Roadmap
- ATR Risk Management
- Position Sizing
- Breakout Detection
- Pocket Pivot
- Volume Profile / POC
- TradingView Signal Alignment
- Sector Rotation
- Portfolio Allocation
- Enhanced Market Regime
- Improved Relative Strength Ranking
- Watchlist tracking
- Trade journal output

## Version Milestones

| Version	| Status	| Major Achievement |
|---|---|---|
| v1.x	| Legacy	| Basic stock scan and email function |
| v2.0	| Stable	| S&P500 scanner and score engine |
| v2.1	| Stable	| Production ready, Yahoo compatibility, safe download |
| v2.3	| Current	| Modular architecture with 5 Python files |
| v2.4	| Planned	| Stop loss and take profit trade plan |
| v3.0	| Planned	| Advanced swing trading decision system |

## Branch Recommendation
- `main` / `stable`: latest stable production version
- `dev`: next version development
- `v2.3-modular`: modular release branch
- `v2.4-risk`: take profit and stop loss development branch
