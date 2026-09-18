def test_email_contains_market_regime():
    email_body = """
    Market Regime: BULL
    Regime Score: 15
    """

    assert "Market Regime" in email_body
    assert "BULL" in email_body


def test_summary_contains_market_regime():
    summary = {
        "MarketRegime": "NEUTRAL",
        "RegimeScore": 7,
    }

    assert summary["MarketRegime"] == "NEUTRAL"
    assert summary["RegimeScore"] == 7
