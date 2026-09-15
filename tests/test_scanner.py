from collections import Counter

import pandas as pd

from scanner import scanner as scanner_module


def create_metrics(**overrides):
    metrics = {
        "Ticker": "TEST",
        "Price": 100.0,
        "LastVolume": 1_500_000,
        "AvgVolume": 1_200_000,
        "VolumeSource": "Latest completed session",
        "VolumeRatio": 1.25,
        "RelativeVolumeLatest": 1.25,
        "RelativeVolumePrevious": 1.10,
        "RSI": 60.0,
        "RelativeStrength": 10.0,
        "RS21": 5.0,
        "RS63": 10.0,
        "RS126": 8.0,
        "RS252": 6.0,
        "RSComposite": 8.45,
        "ADX": 30.0,
        "PlusDI": 35.0,
        "MinusDI": 15.0,
        "MA20": 95.0,
        "MA50": 90.0,
        "MA200": 80.0,
        "MACD": 2.0,
        "SignalLine": 1.0,
        "MiddleBB": 100.0,
        "UpperBB": 110.0,
    }
    metrics.update(overrides)
    return metrics


def create_score_result():
    return {
        "Score": 85.0,
        "Signal": "🟢 BUY",
        "TrendScore": 30,
        "MomentumScore": 20,
        "StrengthScore": 8,
        "VolumeScore": 10,
        "MarketScore": 15,
        "ADXScore": 6,
        "RiskPenalty": 0,
    }


def create_risk_result():
    return {
        "ATR14": 2.0,
        "StopLoss": 97.0,
        "TakeProfit1": 104.5,
        "TakeProfit2": 106.0,
        "RiskPerShare": 3.0,
        "RewardPerShare": 6.0,
        "RiskReward": 2.0,
        "PositionShares": 33,
        "CapitalRequired": 3300.0,
        "PlannedRiskAmount": 99.0,
        "TradePlan": "✅ ACTIONABLE",
    }


def create_price_df():
    return pd.DataFrame(
        {
            "High": [101.0, 102.0],
            "Low": [99.0, 100.0],
            "Close": [100.0, 101.0],
            "Volume": [1_000_000, 1_100_000],
        }
    )


def create_candidate(**overrides):
    candidate = {
        "Ticker": "TEST",
        "TradePlan": "✅ ACTIONABLE",
        "Signal": "🟢 BUY",
        "Score": 85.0,
        "Price": 100.0,
        "RiskReward": 2.0,
        "RS21": 5.0,
        "RS63": 10.0,
        "RS126": 8.0,
        "RS252": 6.0,
        "RSComposite": 8.45,
        "StopLoss": 97.0,
        "TakeProfit1": 104.5,
        "TakeProfit2": 106.0,
        "PositionShares": 33,
        "VolumeSource": "Latest completed session",
        "VolumeRatio": 1.25,
    }
    candidate.update(overrides)
    return candidate


def test_analyse_stock_returns_data_failure(monkeypatch):
    monkeypatch.setattr(
        scanner_module,
        "safe_download",
        lambda ticker: None,
    )

    result = scanner_module.analyse_stock(
        "TEST",
        True,
        {21: 0.0, 63: 0.0, 126: 0.0, 252: 0.0},
    )

    assert result["Ticker"] == "TEST"
    assert result["Status"] == "Data Failure"
    assert result["Result"] is None


def test_analyse_stock_returns_indicator_failure(monkeypatch):
    monkeypatch.setattr(
        scanner_module,
        "safe_download",
        lambda ticker: create_price_df(),
    )
    monkeypatch.setattr(
        scanner_module,
        "calculate_indicators",
        lambda *args, **kwargs: None,
    )

    result = scanner_module.analyse_stock(
        "TEST",
        True,
        {21: 0.0, 63: 0.0, 126: 0.0, 252: 0.0},
    )

    assert result["Status"] == "Indicator Failure"
    assert result["Metrics"] is None


def test_analyse_stock_returns_filtered_outcome(monkeypatch):
    metrics = create_metrics()

    monkeypatch.setattr(
        scanner_module,
        "safe_download",
        lambda ticker: create_price_df(),
    )
    monkeypatch.setattr(
        scanner_module,
        "calculate_indicators",
        lambda *args, **kwargs: metrics,
    )
    monkeypatch.setattr(
        scanner_module,
        "evaluate_filters",
        lambda current_metrics: [
            {
                "Rule": "liquidity_filter",
                "Passed": False,
                "Reason": "Volume filter",
            }
        ],
    )
    monkeypatch.setattr(
        scanner_module,
        "run_filters",
        lambda *args, **kwargs: (
            False,
            "Volume filter",
        ),
    )

    result = scanner_module.analyse_stock(
        "TEST",
        True,
        {21: 0.0, 63: 0.0, 126: 0.0, 252: 0.0},
    )

    assert result["Status"] == "Filtered"
    assert result["Reason"] == "Volume filter"
    assert result["Metrics"] == metrics
    assert result["Result"] is None


def test_analyse_stock_returns_passed_outcome(monkeypatch):
    metrics = create_metrics()

    monkeypatch.setattr(
        scanner_module,
        "safe_download",
        lambda ticker: create_price_df(),
    )
    monkeypatch.setattr(
        scanner_module,
        "calculate_indicators",
        lambda *args, **kwargs: metrics,
    )
    monkeypatch.setattr(
        scanner_module,
        "evaluate_filters",
        lambda current_metrics: [
            {
                "Rule": "liquidity_filter",
                "Passed": True,
                "Reason": "OK",
            }
        ],
    )
    monkeypatch.setattr(
        scanner_module,
        "run_filters",
        lambda *args, **kwargs: (
            True,
            "PASS",
        ),
    )
    monkeypatch.setattr(
        scanner_module,
        "calculate_score",
        lambda *args, **kwargs: create_score_result(),
    )
    monkeypatch.setattr(
        scanner_module,
        "calculate_risk",
        lambda *args, **kwargs: create_risk_result(),
    )

    result = scanner_module.analyse_stock(
        "TEST",
        True,
        {21: 0.0, 63: 0.0, 126: 0.0, 252: 0.0},
    )

    assert result["Status"] == "Passed"
    assert result["Reason"] == "PASS"
    assert result["Result"]["Ticker"] == "TEST"
    assert result["Result"]["Score"] == 85.0
    assert result["Result"]["TradePlan"] == "✅ ACTIONABLE"
    assert result["Result"]["RSComposite"] == 8.45


def test_analyse_stock_handles_processing_error(monkeypatch):
    def raise_error(ticker):
        raise RuntimeError("Unexpected processing failure")

    monkeypatch.setattr(
        scanner_module,
        "safe_download",
        raise_error,
    )

    result = scanner_module.analyse_stock(
        "TEST",
        True,
        {21: 0.0, 63: 0.0, 126: 0.0, 252: 0.0},
    )

    assert result["Status"] == "Processing Error"
    assert "Unexpected processing failure" in result["Reason"]


def test_update_breadth_stats_counts_qualifying_metrics():
    breadth = Counter()
    metrics = create_metrics()

    scanner_module.update_breadth_stats(
        breadth,
        metrics,
    )

    assert breadth["Indicator-ready stocks"] == 1
    assert breadth["Price above MA20"] == 1
    assert breadth["Price above MA50"] == 1
    assert breadth["Price above MA200"] == 1
    assert breadth["MA20 above MA50"] == 1
    assert breadth["RSI above 50"] == 1
    assert breadth["VolumeRatio at least 0.8"] == 1
    assert breadth["VolumeRatio at least 1.0"] == 1
    assert breadth["Non-negative relative strength"] == 1
    assert breadth["Non-negative RSComposite"] == 1


def test_update_breadth_stats_does_not_count_failed_conditions():
    breadth = Counter()
    metrics = create_metrics(
        Price=70.0,
        MA20=80.0,
        MA50=90.0,
        MA200=100.0,
        RSI=40.0,
        VolumeRatio=0.5,
        RelativeStrength=-1.0,
        RSComposite=-1.0,
    )

    scanner_module.update_breadth_stats(
        breadth,
        metrics,
    )

    assert breadth["Indicator-ready stocks"] == 1
    assert breadth["Price above MA20"] == 0
    assert breadth["RSI above 50"] == 0
    assert breadth["Non-negative RSComposite"] == 0


def test_rank_results_returns_empty_dataframe():
    result = scanner_module.rank_results([])

    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_rank_results_uses_trade_plan_score_and_risk_reward():
    results = [
        create_candidate(
            Ticker="WATCH",
            TradePlan="👀 WATCH",
            Score=95.0,
            RiskReward=3.0,
        ),
        create_candidate(
            Ticker="ACTION_LOW",
            TradePlan="✅ ACTIONABLE",
            Score=80.0,
            RiskReward=2.0,
        ),
        create_candidate(
            Ticker="ACTION_HIGH",
            TradePlan="✅ ACTIONABLE",
            Score=90.0,
            RiskReward=2.5,
        ),
    ]

    ranked = scanner_module.rank_results(results)

    assert ranked["Ticker"].tolist() == [
        "ACTION_HIGH",
        "ACTION_LOW",
        "WATCH",
    ]
    assert "TradeRank" not in ranked.columns


def test_build_report_frames_returns_five_frames():
    top20 = pd.DataFrame(
        [
            {
                "Rank": 1,
                **create_candidate(),
            }
        ]
    )
    status_counts = Counter(
        {
            "Passed": 1,
            "Filtered": 2,
        }
    )
    rejection_counts = Counter(
        {
            "Volume filter": 2,
        }
    )
    all_failure_counts = Counter(
        {
            "Volume filter": 2,
            "Price below MA20": 1,
        }
    )
    breadth_counts = Counter(
        {
            "Indicator-ready stocks": 3,
            "Price above MA20": 2,
        }
    )

    frames = scanner_module.build_report_frames(
        top20,
        3,
        status_counts,
        rejection_counts,
        all_failure_counts,
        breadth_counts,
        True,
        600.0,
        550.0,
    )

    assert len(frames) == 5

    returned_top20, summary, rejections, failures, breadth = frames

    assert returned_top20.equals(top20)
    assert "Version" in summary["Metric"].values
    assert "Volume filter" in rejections["First Rejection Reason"].values
    assert "Volume filter" in failures["All Failed Conditions"].values
    assert "Price above MA20" in breadth["Breadth Metric"].values


def test_build_report_frames_handles_empty_top20():
    frames = scanner_module.build_report_frames(
        pd.DataFrame(),
        0,
        Counter(),
        Counter(),
        Counter(),
        Counter(),
        True,
        600.0,
        550.0,
    )

    top20 = frames[0]

    assert isinstance(top20, pd.DataFrame)
    assert top20.empty


def test_export_excel_creates_five_worksheets(
    monkeypatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)

    top20 = pd.DataFrame(
        [
            {
                "Rank": 1,
                **create_candidate(),
            }
        ]
    )
    summary = pd.DataFrame(
        [("Version", scanner_module.VERSION)],
        columns=["Metric", "Value"],
    )
    rejections = pd.DataFrame(
        [("Volume filter", 1)],
        columns=["First Rejection Reason", "Count"],
    )
    failures = pd.DataFrame(
        [("Volume filter", 1)],
        columns=["All Failed Conditions", "Count"],
    )
    breadth = pd.DataFrame(
        [("Indicator-ready stocks", 1, 1.0)],
        columns=[
            "Breadth Metric",
            "Count",
            "Percent of Indicator-ready",
        ],
    )

    filename = scanner_module.export_excel(
        top20,
        summary,
        rejections,
        failures,
        breadth,
    )

    output = tmp_path / filename

    assert output.exists()

    workbook = pd.ExcelFile(output)

    assert workbook.sheet_names == [
        "Top20",
        "Scan Summary",
        "First Rejections",
        "All Failed Conditions",
        "Market Breadth",
    ]


def test_format_counter_returns_default_for_empty_counter():
    result = scanner_module.format_counter(Counter())

    assert result == "None"


def test_format_counter_formats_values():
    result = scanner_module.format_counter(
        Counter(
            {
                "Volume filter": 2,
                "Price filter": 1,
            }
        )
    )

    assert "- Volume filter: 2" in result
    assert "- Price filter: 1" in result


def test_build_email_body_handles_empty_results():
    body = scanner_module.build_email_body(
        pd.DataFrame(),
        10,
        Counter(
            {
                "Filtered": 10,
            }
        ),
        Counter(
            {
                "Volume filter": 10,
            }
        ),
        Counter(
            {
                "Indicator-ready stocks": 10,
            }
        ),
        True,
        600.0,
        550.0,
    )

    assert scanner_module.VERSION in body
    assert "No stocks passed the technical filters" in body
    assert "Volume filter" in body


def test_build_email_body_includes_candidate_details():
    top20 = pd.DataFrame(
        [
            {
                "Rank": 1,
                **create_candidate(),
            }
        ]
    )

    body = scanner_module.build_email_body(
        top20,
        1,
        Counter(
            {
                "Passed": 1,
            }
        ),
        Counter(),
        Counter(
            {
                "Indicator-ready stocks": 1,
            }
        ),
        True,
        600.0,
        550.0,
    )

    assert "TOP CANDIDATES" in body
    assert "Ticker: TEST" in body
    assert "RSComposite: 8.45" in body
    assert "Trade Plan: ✅ ACTIONABLE" in body


def test_send_email_uses_environment_and_smtp(
    monkeypatch,
    tmp_path,
):
    sent_messages = []

    class FakeSMTP:
        def __init__(self, host, port):
            self.host = host
            self.port = port

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def login(self, username, password):
            assert username == "sender@example.com"
            assert password == "secret"

        def send_message(self, message):
            sent_messages.append(message)

    attachment = tmp_path / "report.xlsx"
    attachment.write_bytes(b"test report")

    monkeypatch.setenv(
        "EMAIL_USER",
        "sender@example.com",
    )
    monkeypatch.setenv(
        "EMAIL_PASSWORD",
        "secret",
    )
    monkeypatch.setenv(
        "EMAIL_TO",
        "receiver@example.com",
    )
    monkeypatch.setattr(
        scanner_module.smtplib,
        "SMTP_SSL",
        FakeSMTP,
    )

    scanner_module.send_email(
        "Test subject",
        "Test body",
        str(attachment),
    )

    assert len(sent_messages) == 1
    assert sent_messages[0]["Subject"] == "Test subject"
    assert sent_messages[0]["To"] == "receiver@example.com"


def test_send_bear_market_email(monkeypatch):
    calls = []

    monkeypatch.setattr(
        scanner_module,
        "send_email",
        lambda subject, body, attachment=None: calls.append(
            (subject, body, attachment)
        ),
    )

    scanner_module.send_bear_market_email(
        500.0,
        550.0,
    )

    assert len(calls) == 1
    assert "Bear Market Alert" in calls[0][0]
    assert "BEAR" in calls[0][1]
    assert calls[0][2] is None
