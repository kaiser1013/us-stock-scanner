from unittest.mock import Mock, call

from scanner import scanner as scanner_module


def make_passed_outcome(
    ticker="AAPL",
    score=85,
    risk_reward=2.0,
    market_regime="BULL",
    regime_score=15,
):
    """Create a valid Passed outcome for scanner.main tests."""
    return {
        "Ticker": ticker,
        "Status": "Passed",
        "Reason": "PASS",
        "Metrics": {
            "Price": 150.0,
            "MA20": 145.0,
            "MA50": 140.0,
            "MA200": 130.0,
            "RSI": 60.0,
            "VolumeRatio": 1.2,
            "RelativeStrength": 5.0,
            "RSComposite": 4.0,
        },
        "FilterEvaluations": [
            {
                "Passed": True,
                "Reason": "PASS",
            }
        ],
        "Result": {
            "Ticker": ticker,
            "TradePlan": "✅ ACTIONABLE",
            "Signal": "STRONG BUY",
            "Score": score,
            "MarketRegime": market_regime,
            "RegimeScore": regime_score,
            "RiskReward": risk_reward,
            "RS21": 2.0,
            "RS63": 5.0,
            "RS126": 6.0,
            "RS252": 8.0,
            "RSComposite": 4.0,
            "VolumeSource": "Latest completed session",
            "VolumeRatio": 1.2,
        },
    }


def make_filtered_outcome(ticker="MSFT"):
    """Create a valid Filtered outcome for scanner.main tests."""
    return {
        "Ticker": ticker,
        "Status": "Filtered",
        "Reason": "VolumeRatio below 0.8",
        "Metrics": {
            "Price": 300.0,
            "MA20": 295.0,
            "MA50": 290.0,
            "MA200": 275.0,
            "RSI": 55.0,
            "VolumeRatio": 0.6,
            "RelativeStrength": 3.0,
            "RSComposite": 2.0,
        },
        "FilterEvaluations": [
            {
                "Passed": True,
                "Reason": "PASS",
            },
            {
                "Passed": False,
                "Reason": "VolumeRatio below 0.8",
            },
        ],
        "Result": None,
    }


def make_data_failure_outcome(ticker="NVDA"):
    """Create a valid Data Failure outcome for scanner.main tests."""
    return {
        "Ticker": ticker,
        "Status": "Data Failure",
        "Reason": "Download returned no usable data",
        "Metrics": None,
        "FilterEvaluations": [],
        "Result": None,
    }


def test_main_exits_early_for_bear_market(monkeypatch):
    """BEAR regime sends an alert and stops before scanning stocks."""
    tickers = ["AAPL", "MSFT"]

    mock_get_tickers = Mock(return_value=tickers)
    mock_get_market_context = Mock(
        return_value={
            "spy_price": 400.0,
            "spy_ma200": 450.0,
            "spy_returns": {
                21: -2.0,
                63: -5.0,
                126: -8.0,
                252: -10.0,
            },
            "market_bull": False,
        }
    )
    mock_classify_regime = Mock(return_value="BEAR")
    mock_bear_email = Mock()
    mock_analyse_stock = Mock()
    mock_export_excel = Mock()
    mock_send_email = Mock()

    monkeypatch.setattr(scanner_module, "USE_SP500", True)
    monkeypatch.setattr(
        scanner_module,
        "get_sp500_tickers",
        mock_get_tickers,
    )
    monkeypatch.setattr(
        scanner_module,
        "get_market_context",
        mock_get_market_context,
    )
    monkeypatch.setattr(
        scanner_module,
        "classify_market_regime",
        mock_classify_regime,
    )
    monkeypatch.setattr(
        scanner_module,
        "send_bear_market_email",
        mock_bear_email,
    )
    monkeypatch.setattr(
        scanner_module,
        "analyse_stock",
        mock_analyse_stock,
    )
    monkeypatch.setattr(
        scanner_module,
        "export_excel",
        mock_export_excel,
    )
    monkeypatch.setattr(
        scanner_module,
        "send_email",
        mock_send_email,
    )

    scanner_module.main()

    mock_get_tickers.assert_called_once_with()
    mock_get_market_context.assert_called_once_with()
    mock_classify_regime.assert_called_once_with(400.0, 450.0)

    mock_bear_email.assert_called_once_with(
        400.0,
        450.0,
        "BEAR",
    )

    mock_analyse_stock.assert_not_called()
    mock_export_excel.assert_not_called()
    mock_send_email.assert_not_called()


def test_main_runs_complete_bull_market_scan(monkeypatch):
    """BULL regime processes Passed and Filtered scanner outcomes."""
    tickers = ["AAPL", "MSFT"]
    spy_returns = {
        21: 1.0,
        63: 3.0,
        126: 5.0,
        252: 8.0,
    }

    mock_get_tickers = Mock(return_value=tickers)
    mock_get_market_context = Mock(
        return_value={
            "spy_price": 500.0,
            "spy_ma200": 450.0,
            "spy_returns": spy_returns,
            "market_bull": True,
        }
    )
    mock_classify_regime = Mock(return_value="BULL")
    mock_analyse_stock = Mock(
        side_effect=[
            make_passed_outcome("AAPL"),
            make_filtered_outcome("MSFT"),
        ]
    )
    mock_export_excel = Mock(return_value="bull_report.xlsx")
    mock_build_email_body = Mock(
        return_value="Bull diagnostic report"
    )
    mock_send_email = Mock()
    mock_bear_email = Mock()
    mock_sleep = Mock()

    monkeypatch.setattr(scanner_module, "USE_SP500", True)
    monkeypatch.setattr(
        scanner_module,
        "get_sp500_tickers",
        mock_get_tickers,
    )
    monkeypatch.setattr(
        scanner_module,
        "get_market_context",
        mock_get_market_context,
    )
    monkeypatch.setattr(
        scanner_module,
        "classify_market_regime",
        mock_classify_regime,
    )
    monkeypatch.setattr(
        scanner_module,
        "analyse_stock",
        mock_analyse_stock,
    )
    monkeypatch.setattr(
        scanner_module,
        "export_excel",
        mock_export_excel,
    )
    monkeypatch.setattr(
        scanner_module,
        "build_email_body",
        mock_build_email_body,
    )
    monkeypatch.setattr(
        scanner_module,
        "send_email",
        mock_send_email,
    )
    monkeypatch.setattr(
        scanner_module,
        "send_bear_market_email",
        mock_bear_email,
    )
    monkeypatch.setattr(
        scanner_module.time,
        "sleep",
        mock_sleep,
    )

    scanner_module.main()

    assert mock_analyse_stock.call_args_list == [
        call("AAPL", True, spy_returns, "BULL"),
        call("MSFT", True, spy_returns, "BULL"),
    ]

    assert mock_sleep.call_count == 2
    mock_sleep.assert_has_calls([call(0.2), call(0.2)])
    mock_bear_email.assert_not_called()

    mock_export_excel.assert_called_once()

    export_arguments = mock_export_excel.call_args[0]
    exported_top20 = export_arguments[0]
    summary_df = export_arguments[1]
    rejection_df = export_arguments[2]
    all_failures_df = export_arguments[3]
    breadth_df = export_arguments[4]

    assert len(exported_top20) == 1
    assert exported_top20.iloc[0]["Rank"] == 1
    assert exported_top20.iloc[0]["Ticker"] == "AAPL"
    assert exported_top20.iloc[0]["MarketRegime"] == "BULL"
    assert exported_top20.iloc[0]["RegimeScore"] == 15

    assert not summary_df.empty
    assert not rejection_df.empty
    assert not all_failures_df.empty
    assert not breadth_df.empty

    summary_values = dict(
        zip(
            summary_df["Metric"],
            summary_df["Value"],
            strict=True,
        )
    )

    assert summary_values["Market Regime"] == "BULL"
    assert summary_values["Regime Score"] == 15
    assert summary_values["Stocks Scanned"] == 2
    assert summary_values["Stocks Passed"] == 1
    assert summary_values["Stocks Filtered"] == 1

    mock_build_email_body.assert_called_once()

    email_arguments = mock_build_email_body.call_args[0]
    email_top20 = email_arguments[0]
    email_total_scanned = email_arguments[1]
    email_status_counts = email_arguments[2]
    email_rejection_counts = email_arguments[3]
    email_breadth_counts = email_arguments[4]
    email_market_bull = email_arguments[5]
    email_spy_price = email_arguments[6]
    email_spy_ma200 = email_arguments[7]
    email_market_regime = email_arguments[8]

    assert len(email_top20) == 1
    assert email_total_scanned == 2
    assert email_status_counts["Passed"] == 1
    assert email_status_counts["Filtered"] == 1

    assert (
        email_rejection_counts["VolumeRatio below 0.8"]
        == 1
    )

    assert email_breadth_counts["Indicator-ready stocks"] == 2
    assert email_market_bull is True
    assert email_spy_price == 500.0
    assert email_spy_ma200 == 450.0
    assert email_market_regime == "BULL"

    mock_send_email.assert_called_once_with(
        (
            f"📈 US Scanner {scanner_module.VERSION} "
            "Daily Diagnostic Report"
        ),
        "Bull diagnostic report",
        "bull_report.xlsx",
    )


def test_main_runs_neutral_market_with_empty_results(monkeypatch):
    """NEUTRAL regime continues scanning and exports an empty Top20."""
    tickers = ["NVDA"]
    spy_returns = {
        21: 0.0,
        63: 0.5,
        126: 1.0,
        252: 2.0,
    }

    mock_get_tickers = Mock(return_value=tickers)
    mock_get_market_context = Mock(
        return_value={
            "spy_price": 501.0,
            "spy_ma200": 500.0,
            "spy_returns": spy_returns,
            "market_bull": True,
        }
    )
    mock_classify_regime = Mock(return_value="NEUTRAL")
    mock_analyse_stock = Mock(
        return_value=make_data_failure_outcome("NVDA")
    )
    mock_export_excel = Mock(return_value="neutral_report.xlsx")
    mock_build_email_body = Mock(
        return_value="Neutral diagnostic report"
    )
    mock_send_email = Mock()
    mock_bear_email = Mock()
    mock_sleep = Mock()

    monkeypatch.setattr(scanner_module, "USE_SP500", True)
    monkeypatch.setattr(
        scanner_module,
        "get_sp500_tickers",
        mock_get_tickers,
    )
    monkeypatch.setattr(
        scanner_module,
        "get_market_context",
        mock_get_market_context,
    )
    monkeypatch.setattr(
        scanner_module,
        "classify_market_regime",
        mock_classify_regime,
    )
    monkeypatch.setattr(
        scanner_module,
        "analyse_stock",
        mock_analyse_stock,
    )
    monkeypatch.setattr(
        scanner_module,
        "export_excel",
        mock_export_excel,
    )
    monkeypatch.setattr(
        scanner_module,
        "build_email_body",
        mock_build_email_body,
    )
    monkeypatch.setattr(
        scanner_module,
        "send_email",
        mock_send_email,
    )
    monkeypatch.setattr(
        scanner_module,
        "send_bear_market_email",
        mock_bear_email,
    )
    monkeypatch.setattr(
        scanner_module.time,
        "sleep",
        mock_sleep,
    )

    scanner_module.main()

    mock_bear_email.assert_not_called()

    mock_analyse_stock.assert_called_once_with(
        "NVDA",
        True,
        spy_returns,
        "NEUTRAL",
    )

    mock_sleep.assert_called_once_with(0.2)
    mock_export_excel.assert_called_once()

    export_arguments = mock_export_excel.call_args[0]
    exported_top20 = export_arguments[0]
    summary_df = export_arguments[1]

    assert exported_top20.empty
    assert "MarketRegime" in exported_top20.columns
    assert "RegimeScore" in exported_top20.columns

    summary_values = dict(
        zip(
            summary_df["Metric"],
            summary_df["Value"],
            strict=True,
        )
    )

    assert summary_values["Market Regime"] == "NEUTRAL"
    assert summary_values["Regime Score"] == 7
    assert summary_values["Stocks Scanned"] == 1
    assert summary_values["Stocks Passed"] == 0
    assert summary_values["Data Failures"] == 1

    mock_build_email_body.assert_called_once()

    email_arguments = mock_build_email_body.call_args[0]
    email_status_counts = email_arguments[2]
    email_rejection_counts = email_arguments[3]

    assert email_status_counts["Data Failure"] == 1
    assert (
        email_rejection_counts[
            "Download returned no usable data"
        ]
        == 1
    )
    assert email_arguments[8] == "NEUTRAL"

    mock_send_email.assert_called_once_with(
        (
            f"📊 US Scanner {scanner_module.VERSION} "
            "Daily Diagnostic Report"
        ),
        "Neutral diagnostic report",
        "neutral_report.xlsx",
    )


def test_main_uses_local_tickers_in_test_mode(monkeypatch):
    """USE_SP500=False uses local tickers and BULL defaults."""
    expected_spy_returns = {
        21: 0.0,
        63: 0.0,
        126: 0.0,
        252: 0.0,
    }

    mock_get_tickers = Mock()
    mock_get_market_context = Mock()
    mock_classify_regime = Mock()
    mock_analyse_stock = Mock(
        return_value=make_data_failure_outcome("TEST")
    )
    mock_export_excel = Mock(return_value="test_report.xlsx")
    mock_build_email_body = Mock(return_value="Test mode report")
    mock_send_email = Mock()
    mock_bear_email = Mock()
    mock_sleep = Mock()

    monkeypatch.setattr(scanner_module, "USE_SP500", False)
    monkeypatch.setattr(scanner_module, "TICKERS", ["TEST"])
    monkeypatch.setattr(
        scanner_module,
        "get_sp500_tickers",
        mock_get_tickers,
    )
    monkeypatch.setattr(
        scanner_module,
        "get_market_context",
        mock_get_market_context,
    )
    monkeypatch.setattr(
        scanner_module,
        "classify_market_regime",
        mock_classify_regime,
    )
    monkeypatch.setattr(
        scanner_module,
        "analyse_stock",
        mock_analyse_stock,
    )
    monkeypatch.setattr(
        scanner_module,
        "export_excel",
        mock_export_excel,
    )
    monkeypatch.setattr(
        scanner_module,
        "build_email_body",
        mock_build_email_body,
    )
    monkeypatch.setattr(
        scanner_module,
        "send_email",
        mock_send_email,
    )
    monkeypatch.setattr(
        scanner_module,
        "send_bear_market_email",
        mock_bear_email,
    )
    monkeypatch.setattr(
        scanner_module.time,
        "sleep",
        mock_sleep,
    )

    scanner_module.main()

    mock_get_tickers.assert_not_called()
    mock_get_market_context.assert_not_called()
    mock_classify_regime.assert_not_called()
    mock_bear_email.assert_not_called()

    mock_analyse_stock.assert_called_once_with(
        "TEST",
        True,
        expected_spy_returns,
        "BULL",
    )

    mock_sleep.assert_called_once_with(0.2)
    mock_export_excel.assert_called_once()
    mock_build_email_body.assert_called_once()

    email_arguments = mock_build_email_body.call_args[0]

    assert email_arguments[1] == 1
    assert email_arguments[2]["Data Failure"] == 1
    assert email_arguments[5] is True
    assert email_arguments[6] == 0.0
    assert email_arguments[7] == 0.0
    assert email_arguments[8] == "BULL"

    mock_send_email.assert_called_once_with(
        (
            f"📊 US Scanner {scanner_module.VERSION} "
            "Daily Diagnostic Report"
        ),
        "Test mode report",
        "test_report.xlsx",
    )
