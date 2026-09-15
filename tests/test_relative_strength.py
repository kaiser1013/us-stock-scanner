import pandas as pd

from scanner.indicator import calculate_relative_strength_metrics


def test_rs_composite_calculation():
    """
    Verify RSComposite weighting.
    
    RSComposite =
        0.15 * RS21
      + 0.50 * RS63
      + 0.25 * RS126
      + 0.10 * RS252
    """
    
    close = pd.Series(
        [100 + i for i in range(300)],
        dtype=float,
    )
    
    spy_returns = {
        21: 1.0,
        63: 2.0,
        126: 3.0,
        252: 4.0,
    }
    
    result = calculate_relative_strength_metrics(
        close,
        spy_returns,
    )
    
    expected = (
        result["RS21"] * 0.15
        + result["RS63"] * 0.50
        + result["RS126"] * 0.25
        + result["RS252"] * 0.10
    )
    
    assert abs(
        result["RSComposite"] - expected
    ) < 0.000001
    
def test_rs_fields_exist():
    """
    Ensure all RS fields exist.
    """
    
    close = pd.Series(
        [100 + i for i in range(300)],
        dtype=float,
    )
    
    spy_returns = {
        21: 0.0,
        63: 0.0,
        126: 0.0,
        252: 0.0,
    }
    
    result = calculate_relative_strength_metrics(
        close,
        spy_returns,
    )
    
    assert "RS21" in result
    assert "RS63" in result
    assert "RS126" in result
    assert "RS252" in result
    assert "RSComposite" in result
    
def test_rs_composite_is_float():
    """
    RSComposite should always be numeric.
    """
    
    close = pd.Series(
        [100 + i for i in range(300)],
        dtype=float,
    )
    
    spy_returns = {
        21: 1.0,
        63: 2.0,
        126: 3.6,
        252: 4.0,
    }
    
    result = calculate_relative_strength_metrics(
        close,
        spy_returns,
    )
    
    assert isinstance(
        result["RSComposite"],
        float,
    )
    
def test_positive_trend_creates_positive_rs():
    """
    Strong stock trend versus flat benchmark
    should produce positive RS.
    """
    
    close = pd.Series(
        [100 + i for i in range(300)],
        dtype=float,
    )
    
    spy_returns = {
        21: 0,
        63: 0,
        126: 0,
        252: 0,
    }
    
    result = calculate_relative_strength_metrics(
        close,
        spy_returns,
    )
    
    assert result["RS63"] > 0
''
    
    
    
