import pandas as pd

from scanner.risk import calculate_risk


def create_price_df():
    
    data = {
        "High": [101 + i for i in range(50)],
        "Low": [99 + i for i in range(50)],
        "Close": [100 + i for i in range(50)],
    }
    
    return pd.DataFrame(data)

def create_metrics(price=150):
    
    return {
        "Price": price,
    }

def test_risk_returns_fields():

    result = calculate_risk(
        create_price_df(),
        create_metrics(),
        score=80,
    )
    
    required = [
        "ATR14",
        "StopLoss",
        "TakeProfit1",
        "TakeProfit2",
        "RiskPerShare",
        "RewardPerShare",
        "RiskReward",
        "PositionShares",
        "CapitalRequired",
        "PlannedRiskAmount",
        "TradePlan",
    ]
    
    for field in required:
        assert field in result
        
def test_stop_loss_below_entry():
    
    result = calculate_risk(
        create_price_df(),
        create_metrics(),
        score=80,
    )
    
    assert (
        result["StopLoss"]
        <
        150
    )
    
def test_take_profit_above_entry():
    
    result = calculate_risk(
        create_price_df(),
        create_metrics(),
        score=80,
    )
    
    assert (
        result["TakeProfit1"]
        >
        150
    )
    
    assert (
        result["TakeProfit2"]
        >
        150
    )

def test_risk_reward_positive():
    
    result = calculate_risk(
        create_price_df(),
        create_metrics(),
        score=80,
    )
    
    assert (
        result["RiskReward"]
        >
        0
    )
    
def test_position_size_non_negative():
    
    result = calculate_risk(
        create_price_df(),
        create_metrics(),
        score=80,
    )
    
    assert (
        result["PositionShares"]
        >= 0
    )
    
def test_high_score_actionable_or_watch():
    
    result = calculate_risk(
        create_price_df(),
        create_metrics(),
        score=90,
    )
    
    assert result["TradePlan"] in (
        "✅ ACTIONABLE",
        "👀 WATCH",
        "❌ SKIP",
    )
    
def test_capital_required_non_negative():
        
    result = calculate_risk(
        create_price_df(),
        create_metrics(),
        score=80,
    )
        
    assert (
        result["CapitalRequired"]
        >= 0
    )
        
def test_planned_risk_non_negative():
    result = calculate_risk(
        create_price_df(),
        create_metrics(),
        score=80,
    )
    
    assert (
        result["PlannedRiskAmount"]
        >= 0
    ) 
