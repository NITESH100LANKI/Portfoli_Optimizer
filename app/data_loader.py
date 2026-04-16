import pandas as pd
import os
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

def load_stock_data(file_path: str) -> pd.DataFrame:
    """Loads stock return data from a CSV file."""
    logger.info(f"Attempting to load data from: {file_path}")
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"Data file {file_path} does not exist.")
    
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Successfully loaded data with {len(df)} rows and columns: {list(df.columns)}")
        return df
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        raise
