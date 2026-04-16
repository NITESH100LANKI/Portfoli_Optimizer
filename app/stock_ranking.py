import pandas as pd
from typing import Dict, List
from app.utils.logger import setup_logger

logger = setup_logger("stock_ranking")

def calculate_stock_score(ticker: str, df: pd.DataFrame, news_sentiment: float, config: Dict) -> Dict:
    """
    Calculates a modular score for a stock based on user configuration.
    """
    if df.empty or len(df) < 50:
        return {
            "ticker": ticker,
            "total_score": 0, "signal": "N/A", "breakdown": "Insufficient data", 
            "reasons": ["Data history too short for analysis"],
            "metrics": {"RSI": 0, "Close": 0, "Volume_Surge": 0}
        }
    
    last_row = df.iloc[-1]
    reasons = []
    
    # Strategy Tuning
    strategy = config.get('strategy', 'Balanced')
    feat = config.get('features', {})
    
    trend_score = 0
    mom_score = 0
    vol_score = 0
    sent_score = 0
    max_possible = 0

    # 1. Trend (Price vs MAs)
    if feat.get('technical_indicators', True):
        max_possible += 30
        if last_row['Close'] > last_row['MA20']: trend_score += 10
        if last_row['Close'] > last_row['MA50']: trend_score += 10
        if last_row['MA20'] > last_row['MA50']: trend_score += 10
        if trend_score >= 20: reasons.append("Strong technical trend alignment")

    # 2. Momentum (RSI)
    if feat.get('technical_indicators', True):
        max_possible += 20
        rsi = last_row['RSI']
        # Conservative wants tight 40-65, Aggressive accepts 35-75
        if strategy == 'Conservative':
            if 45 < rsi < 65: mom_score += 20; reasons.append("Stable moderate momentum")
        elif strategy == 'Aggressive':
            if 35 < rsi < 75: mom_score += 20; reasons.append("High-velocity breakout momentum")
        else: # Balanced
            if 40 < rsi < 70: mom_score += 20; reasons.append("Healthy bullish momentum")

    # 3. Volume
    if feat.get('volume_analysis', True):
        max_possible += 20
        avg_vol = df['Volume'].tail(20).mean()
        v_surge = last_row['Volume'] / avg_vol
        if v_surge > 1.5: 
            vol_score += 20; reasons.append("Institutional volume surge detected")
        elif v_surge > 1.1:
            vol_score += 10; reasons.append("Accumulation volume signs")

    # 4. News Sentiment
    if feat.get('news_sentiment', True):
        max_possible += 10
        sent_score = int(news_sentiment * 10)
        if news_sentiment > 0.4: reasons.append("Positive news catalyst")

    # Normalize to 100 base
    raw_total = trend_score + mom_score + vol_score + sent_score
    total_score = int((raw_total / max_possible) * 100) if max_possible > 0 else 0
    total_score = min(100, max(0, total_score))
    
    # Strategy Signal Logic
    buy_thresh = 80 if strategy == 'Conservative' else 70 if strategy == 'Balanced' else 60
    avoid_thresh = 40 if strategy == 'Conservative' else 35
    
    signal = "HOLD"
    if total_score >= buy_thresh: signal = "BUY (Research)"
    elif total_score < avoid_thresh: signal = "AVOID"
    
    return {
        "ticker": ticker,
        "total_score": total_score,
        "signal": signal,
        "reasons": reasons[:3],
        "metrics": {
            "RSI": round(last_row.get('RSI', 0), 2),
            "Close": round(last_row['Close'], 2),
            "Volume_Surge": round(last_row['Volume'] / df['Volume'].tail(20).mean(), 2) if df['Volume'].tail(20).mean() > 0 else 1
        }
    }

def rank_top_stocks(stock_stats: List[Dict]) -> List[Dict]:
    """Sorts and ranks stocks (1 to 50)."""
    sorted_stocks = sorted(stock_stats, key=lambda x: x['total_score'], reverse=True)
    for i, stock in enumerate(sorted_stocks):
        stock['rank'] = i + 1
    return sorted_stocks[:50]
