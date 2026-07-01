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

TICKER_SECTOR_MAP = {
    "RELIANCE.NS": "Energy/Oil & Gas", "ONGC.NS": "Energy/Oil & Gas", "BPCL.NS": "Energy/Oil & Gas", "COALINDIA.NS": "Energy/Oil & Gas",
    "TCS.NS": "Information Technology", "INFY.NS": "Information Technology", "HCLTECH.NS": "Information Technology", "WIPRO.NS": "Information Technology", "TECHM.NS": "Information Technology",
    "HDFCBANK.NS": "Financial Services", "ICICIBANK.NS": "Financial Services", "AXISBANK.NS": "Financial Services", "SBIN.NS": "Financial Services", "KOTAKBANK.NS": "Financial Services",
    "BAJFINANCE.NS": "Financial Services", "BAJAJFINSV.NS": "Financial Services", "INDUSINDBK.NS": "Financial Services", "HDFCLIFE.NS": "Financial Services", "SBILIFE.NS": "Financial Services", "SHRIRAMFIN.NS": "Financial Services",
    "ITC.NS": "Consumer Goods", "HINDUNILVR.NS": "Consumer Goods", "NESTLEIND.NS": "Consumer Goods", "BRITANNIA.NS": "Consumer Goods", "TATACONSUM.NS": "Consumer Goods", "TITAN.NS": "Consumer Goods", "ASIANPAINT.NS": "Consumer Goods",
    "MARUTI.NS": "Automobile", "TATAMOTORS.NS": "Automobile", "M&M.NS": "Automobile", "BAJAJ-AUTO.NS": "Automobile", "HEROMOTOCO.NS": "Automobile", "EICHERMOT.NS": "Automobile",
    "SUNPHARMA.NS": "Healthcare/Pharma", "CIPLA.NS": "Healthcare/Pharma", "DRREDDY.NS": "Healthcare/Pharma", "DIVISLAB.NS": "Healthcare/Pharma", "APOLLOHOSP.NS": "Healthcare/Pharma",
    "TATASTEEL.NS": "Metals & Mining", "JSWSTEEL.NS": "Metals & Mining", "HINDALCO.NS": "Metals & Mining",
    "NTPC.NS": "Utilities", "POWERGRID.NS": "Utilities", "ADANIPORTS.NS": "Infrastructure", "ADANIENT.NS": "Infrastructure", "LT.NS": "Capital Goods", "BEL.NS": "Capital Goods",
    "ULTRACEMCO.NS": "Construction Materials", "GRASIM.NS": "Construction Materials",
    "BHARTIARTL.NS": "Telecommunication"
}

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
