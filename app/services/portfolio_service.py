import os
from typing import Dict
from app.data_loader import load_stock_data
from app.optimizer import compute_weights
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class PortfolioService:
    @staticmethod
    def get_optimized_portfolio(file_path: str, method: str = "equal") -> Dict[str, float]:
        """Orchestrates loading data and computing weights."""
        logger.info(f"Initializing portfolio optimization service flow for method: {method}")
        
        try:
            data = load_stock_data(file_path)
            weights = compute_weights(data, method=method)
            return weights
        except Exception as e:
            logger.error(f"Service layer encountered an error: {e}")
            raise

    @staticmethod
    def get_portfolio_weights(strategy: str) -> Dict[str, float]:
        """Standardized method for API to get weights based on strategy name."""
        # Use default sample data path
        data_path = os.path.join(os.getcwd(), "data", "sample_data.csv")
        return PortfolioService.get_optimized_portfolio(data_path, method=strategy)
