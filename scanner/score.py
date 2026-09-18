def classify_signal(score):
    if score >= 90:
        return "🔥 STRONG BUY"
    if score >= 80:
        return "🟢 BUY"
    if score >= 70:
        return "🟡 WATCH"
    if score >= 60:
        return "⚪️ MONITOR"
    return "❌ NO TRADE"

def calculate_score(metrics, market_bull, market_regime=None):
    """Score Engine v2.6 with a three-state market RegimeScore.
    
    MarketScore is retained as an alias of RegimeScore for compatibility.
    Calls that only supply market_bull continue to behave like v2.5.x.
    """
    
    score = 0
    
    trend_score = 0
    if metrics["Price"] > metrics["MA20"]:
        trend_score += 10
    if metrics["MA20"] > metrics["MA50"]:
        trend_score += 10
    if metrics["MA50"] > metrics["MA200"]:
        trend_score += 10
    score += trend_score

    momentum_score = 0
    rsi = metrics["RSI"]
    if 55 <= rsi <= 65:
        momentum_score += 10
    elif 50 <= rsi < 55:
        momentum_score += 7
    elif 65 < rsi <= 70:
        momentum_score += 5
    
    if metrics["MACD"] > metrics["SignalLine"]:
        momentum_score += 10 if metrics["MACD"] > 0 else 7
    score += momentum_score
    
    relative_strength = metrics["RelativeStrength"]
    strength_score = 0
    if relative_strength > 30:
        strength_score = 15
    elif relative_strength > 20:
        strength_score = 12
    elif relative_strength > 10:
        strength_score = 8
    elif relative_strength > 5:
        strength_score = 5
    score += strength_score
    
    volume_ratio = metrics["VolumeRatio"]
    volume_score = 0
    if volume_ratio > 2.5:
        volume_score = 20
    elif volume_ratio > 2.0:
        volume_score = 18
    elif volume_ratio > 1.5:
        volume_score = 15
    elif volume_ratio > 1.2:
        volume_score = 10
    elif volume_ratio > 1.0:
        volume_score = 5
    score += volume_score

    if market_regime is None:
        market_regime = "BULL" if market_bull else "BEAR"
    
    regime_scores = {
        "BULL": 15,
        "NEUTRAL": 7,
        "BEAR": 0,
    }
    normalised_regime = str(market_regime).upper()
    if normalised_regime not in regime_scores:
        raise ValueError(f"Unsupported market regime: {market_regime}")

    regime_score = regime_scores[normalised_regime]
    market_score = regime_score
    score += regime_score
    
    risk_penalty = 0
    if metrics["RSI"] > 75:
        risk_penalty += 5
    if metrics["Price"] > metrics["UpperBB"]:
        risk_penalty += 5
    score -= risk_penalty
    
    adx_score = 0
    if metrics["ADX"] > 25 and metrics["PlusDI"] > metrics["MinusDI"]:
        adx_score = 6
    elif metrics["ADX"] > 20 and metrics["PlusDI"] > metrics["MinusDI"]:
        adx_score = 4
    score += adx_score
    
    final_score = max(0, min(score, 100))
    
    return {
        "Score": round(final_score, 2),
        "Signal": classify_signal(final_score),
        "TrendScore": trend_score,
        "MomentumScore": momentum_score,
        "StrengthScore": strength_score,
        "VolumeScore": volume_score,
        "MarketRegime": normalised_regime,
        "RegimeScore": regime_score,
        "MarketScore": market_score,
        "ADXScore": adx_score,
        "RiskPenalty": risk_penalty,
    }
    
