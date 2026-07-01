import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import sys
import os
from typing import List, Dict
import plotly.express as px

# Ensure the project root is in the path for absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Internal imports
from app.market_data import fetch_stock_data, NIFTY_50_TICKERS, get_ticker_info
from app.technical_indicators import add_technical_indicators, detect_support_resistance
from app.news_analyzer import fetch_news_rss, analyze_sentiment_heuristic
from app.stock_ranking import calculate_stock_score, rank_top_stocks
from app.watchlist_manager import manage_watchlist
from app.ai_advisor import AIAdvisor
from app.utils.logger import setup_logger

logger = setup_logger("streamlit_app")

# Page Config
st.set_page_config(
    page_title="Indian Stock Research Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional Look
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { border: 1px solid #e1e4e8; padding: 10px; border-radius: 5px; background-color: white; }
    .stock-card { border: 1px solid #ddd; padding: 15px; border-radius: 8px; margin-bottom: 10px; background: white; }
    .buy-signal { color: green; font-weight: bold; }
    .avoid-signal { color: red; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- Sidebar: Control Center ---
st.sidebar.title("🛠️ Control Center")

with st.sidebar.expander("📈 Analysis Strategy", expanded=True):
    strategy_mode = st.selectbox("Strategy Mode", ["Conservative", "Balanced", "Aggressive"], index=1)
    conf_threshold = st.slider("Signal Confidence Filter (%)", 0, 100, 60)
    timeframe_label = st.selectbox("Market Timeframe", ["1 Hour", "1 Day", "1 Week"], index=1)
    tf_map = {"1 Hour": "1h", "1 Day": "1d", "1 Week": "1wk"}
    selected_interval = tf_map[timeframe_label]

with st.sidebar.expander("⚙️ Feature Toggles", expanded=False):
    f_tech = st.toggle("Technical Indicators", value=True)
    f_patt = st.toggle("Chart Patterns", value=True)
    f_candle = st.toggle("Candlestick Patterns", value=True)
    f_vol = st.toggle("Volume Analysis", value=True)
    f_news = st.toggle("News Sentiment", value=True)
    f_signals = st.toggle("Buy/Sell Signals", value=True)
    f_ai = st.toggle("AI Research Panel", value=True)

with st.sidebar.expander("🎯 Watchlist Settings", expanded=False):
    watch_mode = st.radio("Mode", ["Auto Top 50", "Manual Selection"])
    if watch_mode == "Manual Selection":
        custom_tickers = st.text_input("Enter Tickers (comma separated)", value="RELIANCE.NS, SBIN.NS, TCS.NS")
        active_tickers = [t.strip().upper() for t in custom_tickers.split(",")]
    else:
        active_tickers = NIFTY_50_TICKERS

# Consolidate Config
user_config = {
    'strategy': strategy_mode,
    'confidence_threshold': conf_threshold,
    'interval': selected_interval,
    'features': {
        'technical_indicators': f_tech,
        'chart_patterns': f_patt,
        'candlestick_patterns': f_candle,
        'volume_analysis': f_vol,
        'news_sentiment': f_news,
        'buy_sell_signals': f_signals,
        'ai_panel': f_ai
    }
}

# Application Logic
def load_all_market_data(tickers: List[str], config: Dict):
    """Modular data fetching and scoring."""
    interval = config['interval']
    with st.spinner(f"Analyzing {len(tickers)} stocks [Mode: {config['strategy']}]..."):
        all_data = fetch_stock_data(tickers, interval=interval)
        
        processed_stats = []
        full_stats = []
        for ticker, df in all_data.items():
            if config['features']['technical_indicators']:
                df = add_technical_indicators(df)
            
            sentiment = 0.0
            if config['features']['news_sentiment']:
                news = fetch_news_rss(ticker)
                sentiment = analyze_sentiment_heuristic(news)
            
            score_data = calculate_stock_score(ticker, df, sentiment, config)
            full_stats.append(score_data)
            
            # Filter by confidence
            if score_data['total_score'] >= config['confidence_threshold']:
                processed_stats.append(score_data)
            
            all_data[ticker] = df
            
        ranked_list = rank_top_stocks(processed_stats)
        full_ranked_list = rank_top_stocks(full_stats)
        return all_data, ranked_list, full_ranked_list

# Load Data
all_dfs, ranked_stocks, full_ranked_stocks = load_all_market_data(active_tickers, user_config)
watchlist = manage_watchlist(ranked_stocks)
advisor = AIAdvisor(full_ranked_stocks, all_dfs, user_config)

# --- Navigation State Management ---
if "target_stock" not in st.session_state:
    st.session_state.target_stock = ranked_stocks[0]['ticker'] if ranked_stocks else "RELIANCE.NS"

if "messages" not in st.session_state:
    st.session_state.messages = []

def set_stock(ticker):
    st.session_state.target_stock = ticker

# --- Page Header & Quick Insights ---
st.title("🏛️ Professional Market Terminal")

if ranked_stocks:
    movers_col, losers_col, vol_col = st.columns(3)
    with movers_col:
        top_gainer = max(ranked_stocks, key=lambda x: x['metrics']['Change'])
        st.metric("🚀 Top Mover", f"{top_gainer['ticker']}", f"+{top_gainer['metrics']['Change']}%")
    with losers_col:
        top_colored = min(ranked_stocks, key=lambda x: x['metrics']['Change'])
        st.metric("📉 Top Loser", f"{top_colored['ticker']}", f"{top_colored['metrics']['Change']}%", delta_color="inverse")
    with vol_col:
        top_vol = max(ranked_stocks, key=lambda x: x['metrics']['Volume'])
        st.metric("🔊 Volume Leader", f"{top_vol['ticker']}", f"{round(top_vol['metrics']['Volume']/1e6, 1)}M")
else:
    st.warning("⚠️ No stocks match the current filtering criteria. Please lower the Signal Confidence Filter in the Control Center.")

st.markdown("---")

# --- Institutional Tabs ---
tab_heat, tab_screen, tab_anal, tab_ai = st.tabs(["🔥 Market Heatmap", "📋 Institutional Screener", "📊 Deep Analysis", "🤖 AI Advisor"])

# --- Tab: Market Heatmap ---
with tab_heat:
    st.subheader("Sector Performance Treemap")
    if ranked_stocks:
        h_df = pd.DataFrame(ranked_stocks)
        h_df['Price'] = h_df['metrics'].apply(lambda x: x['Close'])
        h_df['Change'] = h_df['metrics'].apply(lambda x: x['Change'])
        h_df['Volume'] = h_df['metrics'].apply(lambda x: x['Volume'])
        
        fig_heat = px.treemap(h_df, path=['sector', 'ticker'], values='Volume',
                             color='Change', color_continuous_scale='RdYlGn',
                             color_continuous_midpoint=0,
                             hover_data=['Price', 'Change', 'total_score'],
                             title="Nifty 50 Performance by Sector & Volume")
        
        fig_heat.update_layout(height=600, margin=dict(t=30, l=10, r=10, b=10))
        st.plotly_chart(fig_heat, use_container_width=True)
        
        st.info("💡 Larger tiles represent higher trading volume today. Grouped by Sector.")

# --- Tab: Institutional Screener ---
with tab_screen:
    st.subheader("Real-Time Research Screener")
    if ranked_stocks:
        s_df = pd.DataFrame(ranked_stocks)
        s_df['Price'] = s_df['metrics'].apply(lambda x: x['Close'])
        s_df['Change %'] = s_df['metrics'].apply(lambda x: x['Change'])
        s_df['RSI'] = s_df['metrics'].apply(lambda x: x['RSI'])
        s_df['Score'] = s_df['total_score']
        
        disp_cols = ["rank", "ticker", "sector", "Price", "Change %", "RSI", "signal", "Score"]
        
        # Display Table
        st.dataframe(s_df[disp_cols].sort_values("Score", ascending=False), use_container_width=True, hide_index=True)
        
        search_col, nav_col = st.columns([2, 1])
        with nav_col:
            quick_nav = st.selectbox("Detailed Analysis Jump", [s['ticker'] for s in ranked_stocks], key="screen_nav")
            if st.button("Analyze Selected", use_container_width=True):
                set_stock(quick_nav)
                st.success(f"Context switched to {quick_nav}. Navigate to 'Deep Analysis' tab.")
    else:
        st.info("💡 No stocks passed the confidence threshold to be listed in the Screener.")

# --- Tab: Deep Analysis ---
with tab_anal:
    from app.technical_indicators import (
        calculate_buy_sell_signals, 
        detect_chart_patterns, 
        identify_candlestick_patterns,
        identify_geometric_patterns
    )
    
    if not all_dfs:
        st.error("No stock data could be loaded. Please check your internet connection or ticker configuration.")
    else:
        current_ticker = st.session_state.target_stock
        if current_ticker not in all_dfs:
            current_ticker = list(all_dfs.keys())[0] if all_dfs else "RELIANCE.NS"
            st.session_state.target_stock = current_ticker
            
        st.subheader(f"Strategy Research: {current_ticker}")
        
        col_a, col_b = st.columns([2, 1])
        with col_a:
            # Stock Selector for this tab
            ticker_options = list(all_dfs.keys())
            new_ticker = st.selectbox("Switch Ticker", ticker_options, 
                                    index=ticker_options.index(current_ticker) if current_ticker in ticker_options else 0)
            if new_ticker != current_ticker:
                set_stock(new_ticker)
                st.rerun()

        df = all_dfs[current_ticker]
        
        # Financial Stats Row
        s_info_list = [s for s in ranked_stocks if s['ticker'] == current_ticker]
        s_info = s_info_list[0] if s_info_list else None
        
        # Fetching score from full_ranked_stocks if it didn't pass filter
        if not s_info:
            full_info_list = [s for s in full_ranked_stocks if s['ticker'] == current_ticker]
            s_info = full_info_list[0] if full_info_list else None
            is_filtered = True
        else:
            is_filtered = False
            
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Score", f"{s_info['total_score']}/100" if s_info else "N/A")
        m2.metric("Signal", (s_info['signal'] + " (Filtered)" if is_filtered else s_info['signal']) if s_info else "HOLD")
        
        rsi_val = s_info['metrics']['RSI'] if s_info else (round(df['RSI'].iloc[-1], 2) if 'RSI' in df.columns else "N/A")
        m3.metric("RSI", rsi_val)
        
        ema_cross_val = "N/A"
        if 'MA20' in df.columns:
            ema_cross_val = "Bullish" if df['Close'].iloc[-1] > df['MA20'].iloc[-1] else "Bearish"
        m4.metric("EMA Cross", ema_cross_val)

        # Conditional Indicators
        if user_config['features']['buy_sell_signals']:
            df = calculate_buy_sell_signals(df) 
            
        patterns = detect_chart_patterns(df) if user_config['features']['chart_patterns'] else {}
        candle_patterns = identify_candlestick_patterns(df) if user_config['features']['candlestick_patterns'] else []
        geo_patterns = identify_geometric_patterns(df) if user_config['features']['chart_patterns'] else []
        
        sup, res = None, None
        if user_config['features']['technical_indicators']:
            sup, res = detect_support_resistance(df)
        
        # Plotly Chart
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.03, subplot_titles=(current_ticker, 'Volume'), 
                           row_width=[0.2, 0.7])

        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                                    low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
        
        if 'MA20' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1.5), name="MA20"), row=1, col=1)
        if 'MA50' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], line=dict(color='blue', width=1.5), name="MA50"), row=1, col=1)
        
        if sup and user_config['features']['technical_indicators']: 
            fig.add_hline(y=sup, line_dash="dash", line_color="rgba(0,255,0,0.5)", row=1, col=1)
        if res and user_config['features']['technical_indicators']: 
            fig.add_hline(y=res, line_dash="dash", line_color="rgba(255,0,0,0.5)", row=1, col=1)
        
        if user_config['features']['buy_sell_signals'] and 'Signal' in df.columns:
            buys, sells = df[df['Signal'] == 'BUY'], df[df['Signal'] == 'SELL']
            fig.add_trace(go.Scatter(x=buys.index, y=buys['Low']*0.98, mode='markers', marker=dict(symbol='triangle-up', size=12, color='green'), name='BUY'), row=1, col=1)
            fig.add_trace(go.Scatter(x=sells.index, y=sells['High']*1.02, mode='markers', marker=dict(symbol='triangle-down', size=12, color='red'), name='SELL'), row=1, col=1)

        if user_config['features']['chart_patterns']:
            for tp in patterns.get('trendlines', []):
                fig.add_trace(go.Scatter(x=tp['x'], y=tp['y'], mode='lines', line=dict(color='gray', dash='dash'), name='Trendline'), row=1, col=1)
            for gp in geo_patterns:
                fig.add_trace(go.Scatter(x=gp['support_points']['x'], y=gp['support_points']['y'], mode='lines', line=dict(color='rgba(0,100,255,0.4)', width=3), name='Support'), row=1, col=1)
                fig.add_trace(go.Scatter(x=gp['resistance_points']['x'], y=gp['resistance_points']['y'], mode='lines', line=dict(color='rgba(255,100,0,0.4)', width=3), name='Resist'), row=1, col=1)

        if user_config['features']['candlestick_patterns'] and candle_patterns:
            for cp in candle_patterns:
                if cp['x'] >= df.index[-40]:
                    fig.add_annotation(x=cp['x'], y=cp['y'], text=cp['label'], showarrow=True, arrowhead=1, ax=0, ay=-30, font=dict(size=10, color="orange"), row=1, col=1)

        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color='rgba(100,149,237,0.5)'), row=2, col=1)
        fig.update_layout(height=700, template="plotly_white", margin=dict(t=30, l=10, r=10, b=10), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

    # Watchlist Summary
    if watchlist:
        st.markdown("---")
        st.subheader("⭐ Breakout Watchlist Preview")
        cols = st.columns(3)
        for i, stock in enumerate(watchlist[:3]):
            with cols[i]:
                st.info(f"**{stock['ticker']}**\n\n{stock['watchlist_reason']}")

# --- Tab: AI Research Assistant ---
with tab_ai:
    st.subheader("AI Tactical Analyst")
    current_ticker = st.session_state.target_stock
    
    context_col, chat_col = st.columns([1, 2])
    with context_col:
        st.write(f"**Focused Research:** {current_ticker}")
        if st.button("Generate Diagnostic Report"):
            report = advisor.analyze_stock(current_ticker)
            st.markdown(report)
            
    with chat_col:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]): st.markdown(message["content"])

        if prompt := st.chat_input("Ask about the market or specific stocks..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("AI is thinking..."):
                    resp = advisor.process_query(prompt)
                    st.markdown(resp)
            st.session_state.messages.append({"role": "assistant", "content": resp})

# --- Footer ---
st.markdown("---")
st.caption("Finviz-Style Professional Market Research Hub | Powered by AI Analyzer")
