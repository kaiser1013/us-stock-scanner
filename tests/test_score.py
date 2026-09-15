from scanner.score import (
    calculate_score,
)


def create_metrics(**overrides):
    
    metrics = {
        "Price": 100,
        "MA20": 95,
        "MA50": 90,
        "MA200": 80,
        "RSI": 60,
        "MACD": 2,
        "SignalLine": 1,
        "RelativeStrength": 15,
        "VolumeRatio": 1.5,
        "UpperBB": 110,
        "ADX": 28,
        "PlusDI": 30,
        "MinusDI": 20,
    }
        
    metrics.update(overrides)
    
    return metrics
    
def test_score_returns_required_fields():
    
    result = calculate_score(
        create_metrics(),
        market_bull=True,
    )
    
    required = [
        "Score",
        "Signal",
        "TrendScore",
        "MomentumScore",
        "StrengthScore",
        "VolumeScore",
        "MarketScore",
        "ADXScore",
        "RiskPenalty",
    ]
    
    for field in required:
        assert field in result
    
def test_bull_market_bonus():

    bullish = calculate_score(
        create_metrics(),
        market_bull=True,
    )
    
    bearish = calculate_score(
        create_metrics(),
        market_bull=False,
    )
    
    assert bullish["Score"] > bearish["Score"]
    
def test_score_capped_between_0_and_100():

    result = calculate_score(
        create_metrics(),
        market_bull=True,
    )
    
    assert result["Score"] >= 0
    
    assert result["Score"] <= 100
    
def test_high_relative_strength_scores_higher():

    high_rs = calculate_score(
        create_metrics(
            RelativeStrength=35
        ),
        market_bull=True,
    )
    
    low_rs = calculate_score(
        create_metrics(
            RelativeStrength=5
        ),
        market_bull=True,
    )
    
    assert (
        high_rs["StrengthScore"]
        >
        low_rs["StrengthScore"]
    )
    
def test_risk_penalty_high_rsi():
    
    result = calculate_score(
        create_metrics(
            RSI=80
        ),
        market_bull=True,
    )
    
    assert result["RiskPenalty"] >= 5
    
def test_risk_penalty_price_above_upper_bb():

    result = calculate_score(
        create_metrics(
            Price=120,
            UpperBB=100,
        ),
        market_bull=True,
    )

    assert result["RiskPenalty"] >= 5

def test_adx_bonus():

    result = calculate_score(
        create_metrics(
            ADX=30,
            PlusDI=35,
            MinusDI=15,
        ),
        market_bull=True,
    )

    assert result["ADXScore"] > 0

def test_signal_is_string():

    result = calculate_score(
        create_metrics(),
        market_bull=True,
    )

    assert isinstance(
        result["Signal"],
        str,
    )
