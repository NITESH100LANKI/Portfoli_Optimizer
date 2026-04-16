from typing import List, Dict
import streamlit as st

def manage_watchlist(ranked_stocks: List[Dict]) -> List[Dict]:
    """
    Automated watchlist logic based on rank and signal changes.
    For this demo, we auto-include stocks with score > 75 or top 10 rank.
    """
    watchlist = []
    for stock in ranked_stocks:
        reason = ""
        if stock['total_score'] >= 80:
            reason = "Exceptional scoring across all factors"
        elif stock['rank'] <= 5:
            reason = "Top 5 Leaderboard position"
        elif "Significant volume surge" in stock['reasons']:
            reason = "Price breakout with high volume"
            
        if reason:
            stock_copy = stock.copy()
            stock_copy['watchlist_reason'] = reason
            watchlist.append(stock_copy)
            
    return watchlist
