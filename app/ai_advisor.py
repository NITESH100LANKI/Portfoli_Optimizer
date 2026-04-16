import pandas as pd
from typing import List, Dict, Optional
from app.technical_indicators import identify_candlestick_patterns, identify_geometric_patterns
from app.utils.logger import setup_logger

logger = setup_logger("ai_advisor")

class AIAdvisor:
    def __init__(self, ranked_stocks: List[Dict], all_dfs: Dict[str, pd.DataFrame], config: Dict):
        self.ranked_stocks = {s['ticker']: s for s in ranked_stocks}
        self.all_dfs = all_dfs
        self.config = config
        self.disclaimer = "\n\n*⚠️ This is for research and educational purposes only. Not financial advice.*"

    def process_query(self, query: str) -> str:
        """Parses the user query and dispatches to the correct diagnostic function."""
        query = query.lower().strip()
        logger.info(f"AI Advisor processing query: {query}")

        # 1. Suggest Top Stocks
        if any(word in query for word in ["top", "best", "lead", "rank", "suggest"]):
            return self.suggest_top_stocks()

        # 2. Analyze Specific Stock
        # Look for tickers in the query (e.g. RELIANCE.NS)
        found_ticker = None
        for ticker in self.ranked_stocks.keys():
            if ticker.lower() in query:
                found_ticker = ticker
                break
        
        if found_ticker:
            if any(word in query for word in ["why", "reason", "trend"]):
                return self.explain_signal(found_ticker)
            elif any(word in query for word in ["buy", "should", "worth", "signal"]):
                return self.analyze_stock(found_ticker)
            else:
                return self.analyze_stock(found_ticker)

        # 3. Default Response
        return (
            "I'm your Portfolio AI Analyst. I can help with queries like:\n"
            "- 'Which are the top stocks for the next 2 weeks?'\n"
            "- 'Why is RELIANCE.NS trending?'\n"
            "- 'Should I buy HDFCBANK.NS?'\n"
            "- 'Tell me about the market leaderboard.'"
        )

    def suggest_top_stocks(self) -> str:
        """Returns a summary of the current top candidates."""
        top_3 = sorted(self.ranked_stocks.values(), key=lambda x: x['total_score'], reverse=True)[:3]
        
        response = "### 🏆 Top Market Candidates (Next 2-4 Weeks)\n"
        response += "Based on current trend, momentum, and volume analysis, here are the leaders:\n\n"
        
        for stock in top_3:
            response += f"1. **{stock['ticker']}** (Score: {stock['total_score']}/100)\n"
            response += f"   - Signal: {stock['signal']}\n"
            response += f"   - Key Driver: {stock['reasons'][0] if stock['reasons'] else 'Strong Technicals'}\n\n"
            
        response += "These stocks show the best risk-balanced alignment for medium-term upside."
        return response + self.disclaimer

    def analyze_stock(self, ticker: str) -> str:
        """Generates a comprehensive research report for a stock."""
        stock = self.ranked_stocks.get(ticker)
        if not stock: return f"I don't have enough data for {ticker} in the Nifty 50 universe."

        df = self.all_dfs[ticker].iloc[-1]
        
        response = f"### 📊 Research Analysis: {ticker}\n"
        response += f"**Current Signal: {stock['signal']}** (Score: {stock['total_score']}/100)\n\n"
        
        response += "#### 🏁 Performance Summary\n"
        if self.config['features'].get('technical_indicators', True):
            response += f"- **Trend:** {'Bullish' if df['Close'] > df['MA50'] else 'Neutral/Bearish'} (Price vs 50-day MA)\n"
            response += f"- **Momentum:** {'Strong' if df['RSI'] > 60 else 'Stable' if df['RSI'] > 40 else 'Weak'} (RSI: {round(df['RSI'],1)})\n"
        
        if self.config['features'].get('volume_analysis', True):
            response += f"- **Volume:** {'Surge Detected' if stock['metrics']['Volume_Surge'] > 1.2 else 'Normal'}\n\n"
        else:
            response += "\n"
        
        response += "#### 🧐 Why this signal?\n"
        for reason in stock['reasons']:
            response += f"- {reason}\n"
            
        # Add Pattern Analysis
        if self.config['features'].get('chart_patterns', True) or self.config['features'].get('candlestick_patterns', True):
            df_full = self.all_dfs[ticker]
            
            if self.config['features'].get('candlestick_patterns', True):
                candle_p = identify_candlestick_patterns(df_full)
                recent_candle = [p for p in candle_p if p['x'] >= df_full.index[-5]]
                if recent_candle:
                    response += "\n#### 🕯️ Candlestick Intelligence\n"
                    for p in recent_candle:
                        response += f"- Detected **{p['label']}** ({p['type'].capitalize()})\n"

            if self.config['features'].get('chart_patterns', True):
                geo_p = identify_geometric_patterns(df_full)
                if geo_p:
                    response += "\n#### 📐 Chart Geometry\n"
                    response += f"- System detected active **{geo_p[0]['type']}** structure.\n"
            
        response += "\n#### ⚖️ Risk Level\n"
        if df['RSI'] > 75:
            response += "⚠️ **High (Overbought)**: Short-term pullback risk is elevated."
        elif stock['total_score'] > 75:
            response += "✅ **Low to Moderate**: Stock is showing healthy trend alignment."
        else:
            response += "📉 **Moderate to High**: Technicals are not yet fully aligned."

        return response + self.disclaimer

    def explain_signal(self, ticker: str) -> str:
        """Explains the recent trending behavior of a stock."""
        stock = self.ranked_stocks.get(ticker)
        if not stock: return f"I can't analyze the trend for {ticker} right now."
        
        response = f"### 🚀 Trend Breakdown: {ticker}\n"
        response += f"{ticker} is currently ranked #{stock['rank']} on the leaderboard.\n\n"
        
        response += "**What's driving the movement?**\n"
        for reason in stock['reasons']:
            response += f"- {reason}\n"
        
        if stock['metrics']['Volume_Surge'] > 1.0:
            response += f"\nWe are also seeing volume activity at **{stock['metrics']['Volume_Surge']}x** of the 20-day average, indicating institutional interest or a breakout."
            
        return response + self.disclaimer
