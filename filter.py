# ==========================
# LIQUIDITY FILTER
# ==========================

def liquidity_filter(metrics):
    if metrics["Price"] < 20:
        return False, "Price filter"
    if metrics["AvgVolume"] < 1_000_000:
        return False, "Volume filter"
    return True, "OK"

# ==========================
# TREND FILTER
# ==========================

def trend_filter(metrics):
    if metrics["Price"] < metrics["MA20"]:
        return False, "Price below MA20"
    if metrics["MA20"] < metrics["MA50"]:
        return False, "MA20 below MA50"
    return True, "OK"
        
# ==========================
# MOMENTUM FILTER
# ==========================

def momentum_filter(metrics):
    if metrics["RSI"] < 40:
        return False, "RSI too weak"
    if metrics["RSI"] > 80:
        return False, "RSI over-extended"
    if metrics["VolumeRatio"] < 0.8:
        return False, "Low volume ratio"
    if metrics["MACD"] < metrics["SignalLine"] - 0.1:
        return False, "MACD below signal"
    return True, "OK"

# ==========================
# RELATIVE STRENGTH FILTER
# ==========================

def relative_strength_filter(metrics):
    if metrics["RelativeStrength"] < -5:
        return False, "Weak Relative Strength"
    return True, "OK"

def run_filters(ticker, metrics):
    """Run scanner filters in clear production order."""
    filters = [
        liquidity_filter,
        trend_filter,
        momentum_filter,
        relative_strength_filter,
    ]
    
    for rule in filters:
        passed, reason = rule(metrics)
        if not passed:
            print(f"{ticker}: {reason}")
            return False, reason
            
    return True, "PASS"
