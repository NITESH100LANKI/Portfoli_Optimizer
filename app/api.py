import os
import sys

# Ensure local app directory is in path for imports when running directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Query
from services.portfolio_service import PortfolioService
from utils.logger import setup_logger

logger = setup_logger("api")

app = FastAPI(
    title="Portfolio Optimizer API",
    description="A modular REST API for stock portfolio weight optimization.",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Root endpoint to verify API health."""
    logger.info("Health check endpoint called")
    return {
        "status": "online",
        "message": "Portfolio Optimizer API is running",
        "docs": "/docs"
    }

@app.get("/optimize")
async def optimize(strategy: str = Query(..., description="Optimization strategy: equal, mean, or sharpe")):
    """
    Returns optimized portfolio weights based on the requested strategy.
    """
    logger.info(f"API optimization request received for strategy: {strategy}")
    
    valid_strategies = ["equal", "mean", "sharpe"]
    if strategy.lower() not in valid_strategies:
        logger.error(f"Invalid strategy requested: {strategy}")
        raise HTTPException(status_code=400, detail=f"Invalid strategy. Supported: {valid_strategies}")

    try:
        weights = PortfolioService.get_portfolio_weights(strategy.lower())
        return {
            "strategy": strategy.lower(),
            "weights": weights
        }
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
