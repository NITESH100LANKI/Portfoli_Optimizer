import pytest
import pandas as pd
from app.optimizer import compute_weights

def test_compute_weights_equal():
    """Test equal weight computation."""
    data = pd.DataFrame({
        'StockA': [0.1, 0.2],
        'StockB': [0.2, 0.1]
    })
    weights = compute_weights(data, method="equal")
    assert weights == {'StockA': 0.5, 'StockB': 0.5}

def test_compute_weights_mean():
    """Test mean-based weight computation."""
    # StockA has absolute mean 1.5, StockB has absolute mean 0.5
    # Total = 2.0. StockA = 0.75, StockB = 0.25
    data = pd.DataFrame({
        'StockA': [1.0, 2.0],
        'StockB': [0.5, 0.5]
    })
    weights = compute_weights(data, method="mean")
    assert weights['StockA'] == pytest.approx(0.75)
    assert weights['StockB'] == pytest.approx(0.25)

def test_compute_weights_sharpe():
    """Test Sharpe Ratio weight computation."""
    # Create data where StockA clearly outperforms StockB
    data = pd.DataFrame({
        'StockA': [0.05, 0.06, 0.04, 0.05],
        'StockB': [0.01, 0.02, 0.01, 0.02]
    })
    weights = compute_weights(data, method="sharpe")
    # StockA should have significantly more weight than StockB
    assert weights['StockA'] > weights['StockB']
    assert sum(weights.values()) == pytest.approx(1.0)

def test_compute_weights_invalid_method():
    """Test response to invalid method."""
    data = pd.DataFrame({'S1': [0.1]})
    with pytest.raises(ValueError):
        compute_weights(data, method="invalid")
