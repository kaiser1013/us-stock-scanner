# Daily Stock Scanner

自動選出每日最強 3 隻美股並透過 Email 發送結果。

## Features

- Daily stock scan
- Momentum scoring
- Volume analysis
- Top 3 ranking
- Email notification
- GitHub Actions automation

## Required Secrets

EMAIL_USER
EMAIL_PASSWORD
EMAIL_TO

## Run Locally

```bash
pip install -r requirements.txt
python scanner.py
```

## Roadmap

- S&P500 scanning
- RSI filter
- Breakout detection
- Telegram alerts
- Backtesting
