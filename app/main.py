import os
from app.services.portfolio_service import PortfolioService
from app.utils.logger import setup_logger

logger = setup_logger("main")

def main():
    logger.info("Portfolio Optimizer Application Started")
    
    # Define paths
    data_dir = os.path.join(os.getcwd(), "data")
    file_path = os.path.join(data_dir, "sample_data.csv")
    
    # Ensure data directory exists
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    try:
        # Run Equal Weight optimization
        logger.info("Requesting equal-weighted portfolio...")
        eq_weights = PortfolioService.get_optimized_portfolio(file_path, method="equal")
        
        # Run Sharpe Ratio optimization
        logger.info("Requesting Sharpe-ratio optimized portfolio...")
        sr_weights = PortfolioService.get_optimized_portfolio(file_path, method="sharpe")
        
        print("\n" + "="*40)
        print("PORTFOLIO OPTIMIZATION RESULTS")
        print("="*40)
        print(f"{'Stock': <10} | {'Equal Weight': <12} | {'Sharpe Weight': <12}")
        print("-" * 40)
        for stock in eq_weights.keys():
            print(f"{stock: <10} | {eq_weights[stock]: <12.4f} | {sr_weights.get(stock, 0): <12.4f}")
        print("="*40 + "\n")
        
        logger.info("Application finished successfully")
        
    except Exception as e:
        logger.critical(f"Application failed to complete: {e}")

if __name__ == "__main__":
    main()
