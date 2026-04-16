import yfinance as yf
import pandas as pd
from typing import List, Dict
import streamlit as st
from app.utils.logger import setup_logger

logger = setup_logger("market_data")

# Top 50 Indian Stocks (Nifty 50 constituents)
NIFTY_50_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "BHARTIARTL.NS", "ICICIBANK.NS",
    "INFY.NS", "ITC.NS", "LT.NS", "SBIN.NS", "BAJFINANCE.NS",
    "HINDUNILVR.NS", "AXISBANK.NS", "MARUTI.NS", "SUNPHARMA.NS", "TATASTEEL.NS",
    "BAJAJFINSV.NS", "NTPC.NS", "TITAN.NS", "TATAMOTORS.NS", "KOTAKBANK.NS",
    "ADANIENT.NS", "M&M.NS", "ONGC.NS", "HCLTECH.NS", "COALINDIA.NS",
    "ASIANPAINT.NS", "ADANIPORTS.NS", "WIPRO.NS", "ULTRACEMCO.NS", "POWERGRID.NS",
    "HDFCLIFE.NS", "GRASIM.NS", "BAJAJ-AUTO.NS", "JSWSTEEL.NS", "NESTLEIND.NS",
    "INDUSINDBK.NS", "TECHM.NS", "SBILIFE.NS", "BRITANNIA.NS", "HINDALCO.NS",
    "CIPLA.NS", "EICHERMOT.NS", "DIVISLAB.NS", "BPCL.NS", "DRREDDY.NS",
    "APOLLOHOSP.NS", "TATACONSUM.NS", "HEROMOTOCO.NS", "SHRIRAMFIN.NS", "BEL.NS"
]

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_stock_data(tickers: List[str], period: str = "1y", interval: str = "1d") -> Dict[str, pd.DataFrame]:
    """Fetches historical data for multiple tickers with specified interval."""
    logger.info(f"Fetching data for {len(tickers)} stocks [Interval: {interval}]...")
    data_map = {}
    try:
        # Fetching individually to handle errors gracefully per ticker
        for ticker in tickers:
            try:
                # yfinance returns multi-index columns for single ticker in 0.2.0+
                df = yf.download(ticker, period=period, interval=interval, progress=False)
                if not df.empty:
                    # Flatten MultiIndex columns if present
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    data_map[ticker] = df
            except Exception as e:
                logger.error(f"Failed to fetch {ticker}: {e}")
        return data_map
    except Exception as e:
        logger.error(f"Global fetch error: {e}")
        return {}

def get_ticker_info(ticker: str) -> Dict:
    """Gets info for a specific ticker."""
    try:
        t = yf.Ticker(ticker)
        return t.info
    except:
        return {}
