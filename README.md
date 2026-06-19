我建議你開始建立一個 **CHANGELOG + README.md** 習慣。對於日後 v3、v4，甚至回退 (rollback) 都非常有用。

以下係根據我哋呢幾個星期 development 嘅整理，可以直接放入 GitHub。

---

# US Stock Scanner

## v2.0 Stable

### Release Goal

建立可每日自動運行的 S&P500 Swing Trading Scanner。

---

## Core Features

### Market Universe

* S&P500 自動下載
* Test Mode 支援自訂股票列表
* GitHub Actions 自動執行

---

### Market Filter

SPY Market Regime：

```
SPY > MA200 → Bull
SPY < MA200 → Bear
```

Bear Market：

* 停止選股
* 發送 Bear Market Alert Email

---

### Liquidity Filter

```
Price > $20

20D Avg Volume > 1M
```

---

### Trend Filter

```
Price > MA20

MA20 > MA50
```

---

### Momentum Filter

Indicators：

* RSI(14)
* MACD
* Bollinger Bands

Rules：

```
RSI > 40

RSI < 80

Volume Ratio > 0.8

MACD Confirmation
```

---

### Relative Strength

Compare against SP500：

```
63 Trading Days Return

Relative Strength > -5%
```

---

### ADX Trend Strength

```
ADX(14)

+DI

-DI
```

---

### Score Engine

Components：

| Factor            | Max Score |
| ----------------- | --------: |
| Trend             |        30 |
| Momentum          |        20 |
| Relative Strength |        15 |
| Volume            |        20 |
| Market            |        15 |
| ADX               |         6 |
| Risk Penalty      |       -10 |

Final：

```
0~100
```

---

### Signal Classification

| Score | Signal        |
| ----- | ------------- |
| 90+   | 🔥 Strong Buy |
| 80+   | 🟢 Buy        |
| 70+   | 🟡 Watch      |
| 60+   | ⚪ Monitor     |
| <60   | No Trade      |

---

### Output

Top20 Ranking

Excel Export

Daily Email

Bear Market Alert

No Candidate Alert

---

# v2.1 Stable

## Release Goal

提高穩定性及適合作每日 Production 運行。

---

# Major Improvements

## 1. Yahoo Finance Compatibility

解決：

```
MultiIndex Columns
```

例如：

```
Close MMM

High MMM

Low MMM
```

自動轉換：

```
Close

High

Low
```

Compatible with 最新 yfinance。

---

## 2. Safe Download Engine

新增：

```
safe_download()
```

Features：

* Retry 3 次
* Download Error Handling
* Empty Data Protection
* NaN Protection

---

## 3. Data Validation

增加：

```
No Data

Missing Close

All Close NaN

Insufficient History

Indicator NaN
```

避免 Scanner Crash。

---

## 4. Technical Indicator Protection

增加：

MA：

```
MA20

MA50

MA200
```

Validation。

MACD：

```
MACD NaN Protection
```

ADX：

```
NaN Default Handling
```

---

## 5. Logging Upgrade

新增：

```
Processing

Attempt

Price

MA20

Avg Volume

Volume Ratio

Filter Reason

Score

Filtered Out
```

Example：

```
Processing MMM

MMM: attempt 1

MMM | Price=161

MA20=155

AvgVol=3.7M

VolRatio=0.5

MMM: Low volume

MMM filtered out
```

方便 Debug。

---

## 6. Production Email

三種模式：

### Bull Market

```
US Scanner v2.1 Top20
```

---

### Bear Market

```
🔴 Bear Market Alert US Scanner v2.1
```

---

### No Candidates

```
No Candidates US Scanner v2.1 Top20
```

---

## 7. GitHub Actions

Daily Automation

Manual Run：

```
workflow_dispatch
```

Support。

Recommended：

```
22:00 UTC

Mon-Fri
```

---

## 8. Bug Fixes

### Fixed

✅ MultiIndex Error

✅ Indicator NaN

✅ Missing Close

✅ Download Retry

✅ Yahoo Compatibility

✅ Build Email Error

✅ GitHub Workflow Stability

---

## Known Improvements

Minor Cleanup：

```
Duplicate result append
```

Remove：

```
if result is not None:
    results.append(result)
```

---

# Current Status

## Version

```
v2.1 Stable
```

---

## Daily Workflow

```
GitHub Actions

↓

Download SP500

↓

Market Check

↓

Bear Protection

↓

Technical Scan

↓

Score Engine

↓

Top20 Ranking

↓

Excel Export

↓

Email Delivery
```

---

# Future Roadmap

## v2.2

### Code Modularization

```
scanner.py

download.py

indicator.py
```

---

## v2.3

```
filter.py

score.py
```

---

## v3.0

### Advanced Trading System

Planned：

* ATR Risk Management
* Position Sizing
* Breakout Detection
* Pocket Pivot
* Volume Profile / POC
* TradingView Signal Alignment
* Sector Rotation
* Portfolio Allocation
* Enhanced Market Regime
* Improved Relative Strength Ranking

---

## 🏆 專案里程碑（建議加喺 README 最後）

| Version | Status  | Major Achievement                  |
| ------- | ------- | ---------------------------------- |
| v1.x    | Legacy  | 基本選股及 Email 功能                     |
| v2.0    | Stable  | 完整 S&P500 Scanner + Score Engine   |
| v2.1    | Stable  | Production Ready、Yahoo 相容、自動化穩定    |
| v2.2    | Planned | 模組化 (`download.py`、`indicator.py`) |
| v3.0    | Planned | 完整 Swing Trading Decision System   |

我另外建議 GitHub 採用一個簡單版本管理規則：

* **main / stable**：v2.1 Stable（每日自動運行）
* **dev**：v2.2 開發及模組化
* 每次完成一個版本，就更新 `README.md` 同新增 `CHANGELOG.md`，例如：

  * `v2.0 → Initial Production Scanner`
  * `v2.1 → Stability & Production Release`
  * `v2.2 → Modular Architecture`
  * `v3.0 → Advanced Trading System`

咁日後回顧、debug 同擴充功能都會容易得多。
