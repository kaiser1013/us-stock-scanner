import os

import pandas as pd
from ta.volatility import AverageTrueRange

# =======================
# Portfolio Settings
# =======================

ACCOUNT_SIZE = float(os.getenv("ACCOUNT_SIZE", "10000"))
RISK_PER_TRADE = float(os.getenv("RISK_PER_TRAFE", "0.01"))
ATR_STOP_MULTIPLIER = float(os.getenv("ATR_STOP_MULTIPLIER", "1.5"))
TP1_R_MULTIPLIER = float(os.getenv("TP1_R_MULTIPLIER", "1.5"))
TP2_R_MULTIPLIER = float(os.getenv("TP2_R_MULTIPLIER", "2.0"))

def create_trade_plan(score, rr_ratio, shares):
    if shares <= 0:
        return "❌ SKIP"
    if score >= 80 and rr_ratio >= 2.0:    
        return "✅ ACTIONABLE"        
    if score >= 70 and rr_ratio >= 1.5:
        return "👀 WATCH"
    return "❌ SKIP"
        
def calculate_position_size(
    account_size,
    risk_percent,
    risk_per_share,
    current_price
):
    """Return risk-based shares, capital required and planned risk amount."""
    if account_size <= 0 or risk_percent <= 0:
        return 0, 0.0, 0.0
    if risk_per_share <= 0 or current_price <= 0:        
        return 0, 0.0, 0.0

    maximum_risk_amount = account_size * risk_percent
    risk_based_shares = int(maximum_risk_amount / risk_per_share)
    cash_limited_shares = int(account_size / current_price)
    shares = max(0, min(risk_based_shares, cash_limited_shares))

    capital_required = shares * current_price
    planned_risk_amount = shares * risk_per_share
    return shares, capital_required, planned_risk_amount

def calculate_risk(df, metrics, score):
    """Calculate ATR stop, R-multiple targets and position sizing."""
    atr_indicator = AverageTrueRange(
        high=df["High"].astype(float),
        low=df["Low"].astype(float),
        close=df["Close"].astype(float),
        window=14,
    )
    atr = atr_indicator.average_true_range().iloc[-1]
    if pd.isna(atr) or atr <= 0:
        raise ValueError("ATR14 is invalid")

    atr = float(atr)
    current_price = float(metrics["Price"])

    # =======================
    # Stop Loss
    # =======================
    
    stop_loss = max(0.01, current_price - atr * ATR_STOP_MULTIPLIER)
    risk_per_share = current_price - stop_loss
    
    # =======================
    # Take Profit
    # =======================
    
    take_profit_1 = current_price + risk_per_share * TP1_R_MULTIPLIER
    take_profit_2 = current_price + risk_per_share * TP2_R_MULTIPLIER
    
    # =======================
    # Risk Reward
    # =======================

    reward_per_share = take_profit_2 - current_price
    rr_ratio = reward_per_share / risk_per_share if risk_per_share > 0 else 0.0

    # =======================
    # Position Size
    # =======================
    
    shares, capital_required, planned_risk_amount = calculate_position_size(
        ACCOUNT_SIZE,
        RISK_PER_TRADE,
        risk_per_share,
        current_price,
    )
    
    trade_plan = create_trade_plan(score, rr_ratio, shares)
    
    return {
        "ATR14": round(atr, 2),
        "StopLoss": round(stop_loss, 2),
        "TakeProfit1": round(take_profit_1, 2),
        "TakeProfit2": round(take_profit_2,2),
        "RiskPerShare": round(risk_per_share, 2),
        "RewardPerShare": round(reward_per_share, 2),
        "RiskReward": round(rr_ratio, 2),
        "PositionShares": shares,
        "CapitalRequired": round(capital_required, 2),
        "PlannedRiskAmount": round(planned_risk_amount, 2),
        "TradePlan": trade_plan,
    }
        
