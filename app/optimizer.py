import pandas as pd
import numpy as np
from typing import Dict
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

def compute_weights(data: pd.DataFrame, method: str = "equal") -> Dict[str, float]:
    """
    Computes portfolio weights based on the specified method.
    """
    logger.info(f"Computing portfolio weights using method: {method}")
    
    numeric_df = data.select_dtypes(include=[np.number])
    if numeric_df.empty:
        logger.warning("No numeric stock data found in the input DataFrame.")
        return {}

    if method == "equal":
        weights = equal_weight_allocation(numeric_df)
    elif method == "mean":
        weights = mean_based_weights(numeric_df)
    elif method == "sharpe":
        weights = sharpe_ratio_weights(numeric_df)
    else:
        logger.error(f"Unsupported optimization method: {method}")
        raise ValueError(f"Method '{method}' is not supported.")

    logger.info(f"Weight computation complete: {weights}")
    return weights

def equal_weight_allocation(returns: pd.DataFrame) -> Dict[str, float]:
    """Computes equal weights for all assets."""
    stocks = list(returns.columns)
    weight = 1.0 / len(stocks)
    return {stock: round(weight, 4) for stock in stocks}

def mean_based_weights(returns: pd.DataFrame) -> Dict[str, float]:
    """Computes weights proportional to absolute mean returns."""
    means = returns.mean()
    abs_means = means.abs()
    total = abs_means.sum()
    if total == 0:
        return equal_weight_allocation(returns)
    return (abs_means / total).round(4).to_dict()

def sharpe_ratio_weights(returns: pd.DataFrame, risk_free_rate: float = 0.0) -> Dict[str, float]:
    """
    Computes weights that maximize the Sharpe Ratio using scipy optimization.
    Sharpe Ratio = (Expected Portfolio Return - Risk Free Rate) / Portfolio Volatility
    """
    from scipy.optimize import minimize
    
    logger.info("Performing mathematical optimization for Sharpe Ratio")
    
    mean_returns = returns.mean()
    cov_matrix = returns.cov()
    num_assets = len(mean_returns)
    
    # Objective function: negative Sharpe Ratio
    def objective(weights):
        port_return = np.sum(mean_returns * weights)
        port_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe_ratio = (port_return - risk_free_rate) / port_volatility if port_volatility != 0 else 0
        return -sharpe_ratio

    # Constraints: weights sum to 1
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    
    # Boundaries: weights between 0 and 1 (long-only)
    bounds = tuple((0, 1) for _ in range(num_assets))
    
    # Initial guess: equal weights
    init_guess = num_assets * [1. / num_assets]
    
    # Optimization
    result = minimize(objective, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
    
    if not result.success:
        logger.warning(f"Optimization failed: {result.message}. Falling back to equal weights.")
        return {stock: round(1.0/num_assets, 4) for stock in mean_returns.index}

    optimized_weights = {stock: round(weight, 4) for stock, weight in zip(mean_returns.index, result.x)}
    return optimized_weights
