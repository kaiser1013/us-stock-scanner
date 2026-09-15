from scanner.filter import run_filters


def create_metrics(**overrides):
    """
    Base metrics representing
    a healthy candidate.
    """
    
    metrics = {
        "Price": 100,
        "AvgVolume": 2_000_000,
        "MA20": 95,
        "MA50": 90,
        "RSI": 60,
        "VolumeRatio": 1.2,
        "MACD": 1.5,
        "SignalLine": 1.0,
        "RelativeStrength": 10,
    }
    
    metrics.update(overrides)
    
    return metrics
    
def test_candidate_passes_filters():
    
    metrics = create_metrics()
    
    passed, reason = run_filters(
        "TEST",
        metrics,
    )
    
    assert passed is True
    
    assert reason == "PASS"
    
def test_price_filter():
    
    metrics = create_metrics(
        Price=15
    )
    
    passed, reason = run_filters(
        "TEST",
        metrics,
    )
    
    assert passed is False
    
    assert reason == "Price filter"
    
def test_average_volume_filter():
    
    metrics = create_metrics(
        AvgVolume=500000
    )
    
    passed, reason = run_filters(
        "TEST",
        metrics,
    )
    
    assert passed is False
    
    assert reason == "Volume filter"
    
def test_trend_filter_price_below_ma20():
    
    metrics = create_metrics(
        Price=90,
        MA20=100,
    )
    
    passed, reason = run_filters(
        "TEST",
        metrics,
    )
    
    assert passed is False
    
    assert reason == "Price below MA20"
    
def test_trend_filter_ma20_below_ma50():
    
    metrics = create_metrics(
        MA20=80,
        MA50=90,
    )
    
    passed, reason = run_filters(
        "TEST",
        metrics,
    )
    
    assert passed is False
    
    assert reason == "MA20 below MA50"
    
def test_rsi_too_weak():
    
    metrics = create_metrics(
        RSI=35
    )
    
    passed, reason = run_filters(
        "TEST",
        metrics,
    )
    
    assert passed is False
    
    assert reason == "RSI too weak"
    
def test_rsi_overextended():
    
    metrics = create_metrics(
        RSI=85
    )
    
    passed, reason = run_filters(
        "TEST",
        metrics,
    )
    
    assert passed is False
    
    assert reason == "RSI over-extended"
    
def test_volume_ratio_filter():
    
    metrics = create_metrics(
        VolumeRatio=0.5
    )
    
    passed, reason = run_filters(
        "TEST",
        metrics,
    )
    
    assert passed is False
    
    assert reason == "Low completed-session volume ratio"
    
def test_macd_filter():
    
    metrics = create_metrics(
        MACD=0.5,
        SignalLine=1.0,
    )
    
    passed, reason = run_filters(
        "TEST",
        metrics,
    )
    
    assert passed is False
    
    assert reason == "MACD below signal"
    
def test_relative_strength_filter():
    
    metrics = create_metrics(
        RelativeStrength=-6
    )
    
    passed, reason = run_filters(
        "TEST",
        metrics,
    )
    
    assert passed is False
    
    assert reason == "Weak Relative Strength"
    
    
