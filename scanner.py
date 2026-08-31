import os
import smtplib
import time
from collections import Counter
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd

from download import (
    TICKERS,
    USE_SP500,
    get_market_context,
    get_sp500_tickers,
    safe_download
)
from filter import evaluate_filters, run_filters
from indicator import calculate_indicators
from risk import calculate_risk
from score import calculate_score

VERSION = "v2.4.1"

# =====================================
# 掃描模式
# =====================================

def analyse_stock(ticker, market_bull, spy_return):   
    """Return a structured scan outcome for candidates and diagnostics."""
    try:
        df = safe_download(ticker)
        if df is None or df.empty:
            return {
                "Ticker": ticker,
                "Status": "Data Failure",
                "Reason": "Download returned no usable data",
                "Metrics": None,
                "FilterEvaluations": [],
                "Result": None,
            }
                
        metrics = calculate_indicators(ticker, df, spy_return)
        if metrics is None:
            return {
                "Ticker": ticker,
                "Status": "Indicator Failure",
                "Reason": "Indicators unavailable or insufficient history",
                "Metrics": None,
                "FilterEvaluations": [],
                "Result": None,
            }
            
        filter_evaluations = evaluate_filters(metrics)
        passed, reason = run_filters(ticker, metrics)
        if not passed:
            return {
                "Ticker": ticker,
                "Status": "Filtered",
                "Reason": reason,
                "Metrics": metrics,
                "FilterEvaluations": filter_evaluations,
                "Result": None,
            }

        score_result = calculate_score(metrics, market_bull)
        risk_result = calculate_risk(df, metrics, score_result["Score"])
            
        result = {
            "Ticker": ticker,
            "TradePlan": risk_result["TradePlan"],
            "Signal": score_result["Signal"],
            "Score": score_result["Score"],
            "Price": round(metrics["Price"], 2),
            "ATR14": risk_result["ATR14"],
            "StopLoss": risk_result["StopLoss"],
            "TakeProfit1": risk_result["TakeProfit1"],
            "TakeProfit2": risk_result["TakeProfit2"],
            "RiskPerShare": risk_result["RiskPerShare"],
            "RewardPerShare": risk_result["RewardPerShare"],
            "RiskReward": risk_result["RiskReward"],
            "PositionShares": risk_result["PositionShares"],
            "CapitalRequired": risk_result["CapitalRequired"],
            "PlannedRiskAmount": risk_result["PlannedRiskAmount"],
            "LastVolume": metrics["LastVolume"],
            "AvgVolume": metrics["AvgVolume"],
            "VolumeSource": metrics["VolumeSource"],
            "VolumeRatio": metrics["VolumeRatio"],
            "RelativeVolumeLatest": metrics["RelativeVolumeLatest"],
            "RelativeVolumePrevious": metrics["RelativeVolumePrevious"],
            "RSI": round(metrics["RSI"], 2),
            "RelativeStrength": round(metrics["RelativeStrength"], 2),
            "ADX": round(metrics["ADX"], 2),
            "MA20": round(metrics["MA20"], 2),
            "MA50": round(metrics["MA50"], 2),
            "MA200": round(metrics["MA200"], 2),
            "MACD": round(metrics["MACD"], 2),
            "SignalLine": round(metrics["SignalLine"], 2),
            "TrendScore": score_result["TrendScore"],
            "MomentumScore": score_result["MomentumScore"],
            "StrengthScore": score_result["StrengthScore"],
            "VolumeScore": score_result["VolumeScore"],
            "MarketScore": score_result["MarketScore"],
            "ADXScore": score_result["ADXScore"],
            "RiskPenalty": score_result["RiskPenalty"],
        }
        
        return {
            "Ticker": ticker,
            "Status": "Passed",
            "Reason": "PASS",
            "Metrics": metrics,
            "FilterEvaluations": filter_evaluations,
            "Result": result,
        }

    except Exception as error:
        print(f"Error processing {ticker}: {error}")
        return {
            "Ticker": ticker,
            "Status": "Processing Error",
            "Reason": str(error),
            "Metrics": None,
            "FilterEvaluations": [],
            "Result": None,
        }
        
def update_breadth_stats(breadth, metrics):
    breadth["Indicator-ready stocks"] += 1
    if metrics["Price"] > metrics["MA20"]:
        breadth["Price above MA20"] += 1
    if metrics["Price"] > metrics["MA50"]:
        breadth["Price above MA50"] += 1
    if metrics["Price"] > metrics["MA200"]:
        breadth["Price above MA200"] += 1
    if metrics["MA20"] > metrics["MA50"]:
        breadth["MA20 above MA50"] += 1
    if metrics["RSI"] > 50:
        breadth["RSI above 50"] += 1
    if metrics["VolumeRatio"] >= 0.8:
        breadth["VolumeRatio at least 0.8"] += 1
    if metrics["VolumeRatio"] >= 1.0:
        breadth["VolumeRatio at least 1.0"] += 1
    if metrics["RelativeStrength"] >= 0:
        breadth["Non-negative relative strength"] += 1
        
def rank_results(results):
    if not results:
        return pd.DataFrame()
        
    df = pd.DataFrame(results)
    trade_order = {
        "✅ ACTIONABLE": 3,
        "👀 WATCH": 2,
        "❌ SKIP": 1,
    }
    df["TradeRank"] = df["TradePlan"].map(trade_order).fillna(0)
    df = df.sort_values(
        by=["TradeRank", "Score", "RiskReward"],
        ascending=[False, False, False],
    )
    return df.drop(columns=["TradeRank"])
    
def build_report_frames(
    top20,
    total_scanned,
    status_counts,
    rejection_counts,
    all_failure_counts,
    breadth_counts,
    market_bull,
    spy_price,
    spy_ma200,
):
    market_status = "BULL" if market_bull else "BEAR"
    passed_count = int(status_counts.get("Passed",0))
    pass_rate = passed_count / total_scanned if total_scanned else 0

    summary_rows = [
        ("Version", VERSION),
        ("Generated At", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ("Market Status", market_status),
        ("SPY", round(spy_price, 2)),
        ("SPY MA200", round(spy_ma200, 2)),
        ("Stocks Scanned", total_scanned),
        ("Stocks Passed", passed_count),
        ("Pass Rate", round(pass_rate, 4)),
        ("Stocks Filtered", int(status_counts.get("Filtered", 0))),
        ("Data Failures", int(status_counts.get("Data Failure", 0))),
        ("Indicator Failures", int(status_counts.get("Indicator Failure", 0))),
        ("Processing Errors", int(status_counts.get("Processing Error", 0))),
    ]
    summary_df = pd.DataFrame(summary_rows, columns=["Metric", "Value"])
    
    rejection_df = pd.DataFrame(
        rejection_counts.most_common(),
        columns=["First Rejection Reason", "Count"],
    )
    all_failures_df = pd.DataFrame(
        all_failure_counts.most_common(),
        columns=["All Failed Conditions", "Count"],
    )
    
    indicator_ready = breadth_counts.get("Indicator-ready stocks", 0)
    breadth_rows = []
    for metric, count in breadth_counts.items():
        percentage = count / indicator_ready if indicator_ready else 0
        breadth_rows.append((metric, count, round(percentage, 4)))
    breadth_df = pd.DataFrame(
        breadth_rows,
        columns=["Breadth Metric", "Count", "Percent of Indicator-ready"],
    )
    
    if top20.empty:
        top = pd.DataFrame(
            columns=[
                "Rank",
                "Ticker",
                "TradePlan",
                "Signal",
                "Score",
                "RiskReward",
            ]
        )
    
    return top20, summary_df, rejection_df, all_failures_df, breadth_df

# =====================================
# Excel
# =====================================

def export_excel(
    top20,
    summary_df,
    rejection_df,
    all_failures_df,
    breadth_df,
):
    today = datetime.today().strftime("%Y-%m-%d")
    filename = f"stock_scan_{today}_{VERSION}.xlsx"
    
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        top20.to_excel(writer, sheet_name="Top20", index=False)
        summary_df.to_excel(writer, sheet_name="Scan Summary", index=False)
        rejection_df.to_excel(writer, sheet_name="First Rejections", index=False)
        all_failures_df.to_excel(writer, sheet_name="All Failed Conditions", index=False)
        breadth_df.to_excel(writer, sheet_name="Market Breadth", index=False)
        
        for sheet_name, worksheet in writer.sheets.items():
            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions
            for column_cells in worksheet.columns:
                max_length = max(
                    len(str(cell.value)) if cell.value is not None else 0
                    for cell in column_cells
                )
                worksheet.column_dimensions[column_cells[0].column_letter].width = min(
                    max(max_length + 2, 12),
                    40,
                )
    
    return filename
    
def format_counter(counter, empty_text="None"):
    if not counter:
        return empty_text
    return "\n".join(f"- {reason}: {count}" for reason, count in counter.most_common())

# =====================================
# Email內容
# =====================================

def build_email_body(
    top20,
    total_scanned,
    status_counts,
    rejection_counts,
    breadth_counts,
    market_bull,
    spy_price,
    spy_ma200,
):
    market_status = "🟢 BULL" if market_bull else "🔴 BEAR"
    passed_count = int(status_counts.get("Passed", 0))
    filtered_count = int(status_counts.get("Filtered", 0))
    indicator_ready = int(breadth_counts.get("Indicator-ready stocks", 0))
    
    body = f"""
================================
US STOCK SCANNER {VERSION}
Market: {market_status}
SPY: {spy_price:.2f}
SPY MA200: {spy_ma200:.2f}
================================

SCAN SUMMARY
Stocks Scanned: {total_scanned}
Indicator-ready: {indicator_ready}
Stocks Passed: {passed_count}
Stocks Filtered: {filtered_count}
Data Failures: {status_counts.get('Data Failure', 0)}
Indicator Failures: {status_counts.get('Indicator Failure', 0)}
Processing Errors: {status_counts.get('Processing Error', 0)}

TOP FIRST-FAIL REASONS
{format_counter(rejection_counts)}

MARKET BREADTH
- Price above MA20: {breadth_counts.get('Price above MA20', 0)}
- Price above MA50: {breadth_counts.get('Price above MA50', 0)}
- Price above MA200: {breadth_counts.get('Price above MA200', 0)}
- MA20 above MA50: {breadth_counts.get('MA20 above MA50', 0)}
- RSI above 50: {breadth_counts.get('RSI above 50', 0)}
- VolumeRatio at least 0.8: {breadth_counts.get('VolumeRatio at least 0.8', 0)}
- VolumeRatio at least 1.0: {breadth_counts.get('VolumeRatio at least 1.0', 0)}
"""

    if top20. empty:
        body += "\nNo stocks passed the technical filters. See the attached diagnostics report. \n"
    else:
        body += "\nTOP CANDIDATES\n"
        for _, row in top20.iterrows():
            body += f"""
Rank: {row['Rank']}
Ticker: {row['Ticker']}
Trade Plan: {row['TradePlan']}
Signal: {row['Signal']}
Score: {row['Score']}
Price: {row['Price']}
Stop Loss: {row['StopLoss']}
Take Profit 1: {row['TakeProfit1']}
Take Profit 2: {row['TakeProfit1']}
Risk/Reward: {row['RiskReward']}
Position: {row['RiskReward']}
Volume Source: {row['VolumeSource']}
Volume Ratio: {row['VolumeRatio']}
-------------------
"""

    body += "\nGenerated by GitHub Actions"
    return body

# =====================================
# Send Email
# =====================================

def send_email(subject, body, attachment=None):
    email_user = os.environ["EMAIL_USER"]
    email_password = os.environ["EMAIL_PASSWORD"]
    email_to = os.environ["EMAIL_TO"]

    message = MIMEMultipart()
    message["From"] = email_user
    message["To"] = email_to
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))
    
    if attachment:
        with open(attachment, "rb") as file:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(file.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(attachment)}",)
        message.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(email_user, email_password)
        server.send_message(message)

    print("Email sent successfully")

# ==========================
# BEAR MARKET PROTECTION
# ==========================

def send_bear_market_email(spy_price, spy_ma200):
    body = f"""
MARKET STATUS
🔴 BEAR
SPY: {spy_price:.2f}
SPY MA200: {spy_ma200:.2f}
No swing trades today.
"""
    send_email(f"🔴 Bear Market Alert US Scanner {VERSION}", body)

# =====================================
# Main
# =====================================

def main():
    print(f"Scanning stocks with US Stock Scanner {VERSION}...")

    # ==========================
    # LOAD DATA
    # ==========================

    if USE_SP500:
        tickers = get_sp500_tickers()
        print(f"Loaded {len(tickers)} S&P500 stocks")
        market = get_market_context()
        spy_price = market["spy_price"]
        spy_ma200 = market["spy_ma200"]
        spy_return = market["spy_return"]
        market_bull = market["market_bull"]
        print(f"Market Bull: {market_bull}")
    else:
        print("TEST MODE ENABLED")
        tickers = TICKERS
        spy_price = 0.0
        spy_ma200 = 0.0
        spy_return = 0.0
        market_bull = True

    # ==========================
    # BEAR MARKET
    # ==========================
    
    if spy_price < spy_ma200:
        print("Bear market detected")
        send_bear_market_email(spy_price, spy_ma200)
        return
        
    results = []
    status_counts = Counter()
    rejection_counts = Counter()
    all_failure_counts = Counter()
    breadth_counts = Counter()
    
    # ==========================
    # SCAN LOOP
    # ==========================

    for ticker in tickers:
        print(f"Processing {ticker}")
        outcome = analyse_stock(ticker, market_bull, spy_return)
        status_counts[outcome["Status"]] += 1
        
        metrics = outcome["Metrics"]
        if metrics is not None:
            update_breadth_stats(breadth_counts, metrics)
            
        for evaluation in outcome["FilterEvaluations"]:
            if not evaluation["Passed"]:
                all_failure_counts[evaluation["Reason"]] += 1

        if outcome["Status"] == "Passed":
            result = outcome["Result"]
            print (f"{ticker} scored: {result['Score']:2f}")
            results.append(result)
            
        else:
            rejection_counts[outcome["Reason"]] += 1
            print(f"{ticker} excluded: {outcome['Reason']}")
            
        time.sleep(0.2)

    # ==========================
    # TOP 20
    # ==========================
    
    ranked = rank_results(results)
    top20 = ranked.head(20).copy() if not ranked.empty else pd.DataFrame()
    if not top20.empty:
        top20.insert(0, "Rank", range(1, len(top20) + 1))

    report_frames = build_report_frames(
        top20,
        len(tickers),
        status_counts,
        rejection_counts,
        all_failure_counts,
        breadth_counts,
        market_bull,
        spy_price,
        spy_ma200,
    )
    top20, summary_df, rejection_df, all_failures_df, breadth_df = report_frames

    print("\nSCAN SUMMARY:")
    print(summary_df.to_string(index=False))
    print("\nTOP FIRST-FAIL REASONS:")
    print(rejection_df.head(10).to_string(index=False))

    if not top20.empty:
        print("\nTOP 20 RESULTS:")
        print(
            top20[
                [
                    "Rank", 
                    "Ticker", 
                    "TradePlan",
                    "Signal",
                    "Score",
                    "RiskReward",
                    "VolumeSource",
                    "VolumeRatio", 
                ]
            ]
        )
    else:
        print(f"\nNo stocks passed the technical filters.")

    # ==========================
    # EXPORT
    # ==========================

    excel_file = export_excel(
        top20,
        summary_df,
        rejection_df,
        all_failures_df,
        breadth_df,
    )
    email_body = build_email_body(
        top20,
        len(tickers),
        status_counts,
        rejection_counts,
        breadth_counts,
        market_bull,
        spy_price,
        spy_ma200,
    )
    subject_prefix = "📈" if not top20.empty else "📊"
    send_email(f"{subject_prefix} US Scanner {VERSION} Daily Diagnostic Report", email_body, excel_file)

if __name__ == "__main__":
    main()
