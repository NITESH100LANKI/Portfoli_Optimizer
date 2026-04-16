import feedparser
from bs4 import BeautifulSoup
import streamlit as st
from typing import List, Dict
from app.utils.logger import setup_logger

logger = setup_logger("news_analyzer")

@st.cache_data(ttl=1800)  # Cache for 30 mins
def fetch_news_rss(ticker: str) -> List[Dict]:
    """Fetches news from Google News RSS for a given ticker."""
    query = ticker.split(".")[0] # Remove .NS or .BO
    url = f"https://news.google.com/rss/search?q={query}+stock+market+india&hl=en-IN&gl=IN&ceid=IN:en"
    
    logger.info(f"Fetching news for {query}...")
    feed = feedparser.parse(url)
    news_items = []
    
    for entry in feed.entries[:10]: # Limit to 10
        news_items.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.published,
            "summary": BeautifulSoup(entry.summary, "html.parser").get_text() if hasattr(entry, 'summary') else ""
        })
    
    return news_items

def analyze_sentiment_heuristic(news_list: List[Dict]) -> float:
    """
    Simple keyword-based sentiment heuristic.
    Returns a score between -1 and 1.
    """
    if not news_list:
        return 0.0
    
    positive_words = {"strong", "bullish", "buy", "growth", "profit", "surge", "gain", "higher", "positive", "beat", "outperform"}
    negative_words = {"weak", "bearish", "sell", "loss", "fall", "drop", "lower", "negative", "miss", "underperform", "debt"}
    
    total_score = 0
    word_count = 0
    
    for item in news_list:
        text = (item['title'] + " " + item['summary']).lower()
        words = text.split()
        for word in words:
            if word in positive_words:
                total_score += 1
            elif word in negative_words:
                total_score -= 1
            word_count += 1
            
    if word_count == 0: return 0.0
    
    # Normalize
    score = total_score / (len(news_list) * 2) # Heuristic divisor
    return max(-1.0, min(1.0, score))
