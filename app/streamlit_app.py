import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import sys
import os
from typing import List, Dict

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
        for ticker, df in all_data.items():
            if config['features']['technical_indicators']:
                df = add_technical_indicators(df)
            
            sentiment = 0.0
            if config['features']['news_sentiment']:
                news = fetch_news_rss(ticker)
                sentiment = analyze_sentiment_heuristic(news)
            
            score_data = calculate_stock_score(ticker, df, sentiment, config)
            # Filter by confidence
            if score_data['total_score'] >= config['confidence_threshold']:
                processed_stats.append(score_data)
            
        ranked_list = rank_top_stocks(processed_stats)
        return all_data, ranked_list

# Load Data
all_dfs, ranked_stocks = load_all_market_data(active_tickers, user_config)
watchlist = manage_watchlist(ranked_stocks)
advisor = AIAdvisor(ranked_stocks, all_dfs, user_config)

# Initialize Session State for Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar Navigation
st.sidebar.title("🔍 Stock Analytics")
page = st.sidebar.radio("Navigate", 
    ["Overview", "Top 50 Leaderboard", "Watchlist", "Technical Analysis", "Research Details", "AI Research Assistant"])

st.sidebar.markdown("---")
st.sidebar.info("Disclaimer: This tool is for research & education only. No real trading execution or guaranteed returns.")

# --- Page: Overview ---
if page == "Overview":
    st.title("🇮🇳 Indian Market Research Hub")
    st.markdown("Automated analysis of Nifty 50 for 2-4 week research horizons.")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Coverage", f"{len(NIFTY_50_TICKERS)} Stocks")
    col2.metric("Top Pick", ranked_stocks[0]['ticker'])
    col3.metric("Strong Candidates", len([s for s in ranked_stocks if s['total_score'] > 75]))
    col4.metric("Avg Market RSI", round(sum([s['metrics']['RSI'] for s in ranked_stocks])/len(ranked_stocks), 1))
    
    st.subheader("Leaderboard Preview")
    preview_df = pd.DataFrame(ranked_stocks[:10])[["rank", "ticker", "total_score", "signal"]]
    st.table(preview_df)

# --- Page: Top 50 Leaderboard ---
elif page == "Top 50 Leaderboard":
    st.title("🏆 Top 50 Stock Scores")
    
    # Filter
    score_filter = st.slider("Min Score Filter", 0, 100, 50)
    filtered_list = [s for s in ranked_stocks if s['total_score'] >= score_filter]
    
    df_display = pd.DataFrame(filtered_list)
    if not df_display.empty and 'metrics' in df_display.columns:
        # Extracting metrics for display
        df_display['Price'] = df_display['metrics'].apply(lambda x: x.get('Close', 0))
        df_display['RSI'] = df_display['metrics'].apply(lambda x: x.get('RSI', 0))
    
    cols_to_show = ["rank", "ticker", "total_score", "signal", "Price", "RSI"] if 'Price' in df_display.columns else ["rank", "ticker", "total_score", "signal"]
    st.dataframe(df_display[cols_to_show], width="stretch")
    
    st.subheader("Detailed Analysis Cards")
    for stock in filtered_list[:12]:
        with st.expander(f"#{stock['rank']} - {stock['ticker']} (Score: {stock['total_score']})"):
            c1, c2 = st.columns([1, 2])
            with c1:
                st.write(f"**Signal:** {stock['signal']}")
                st.write(f"**Price:** ₹{stock['metrics']['Close']}")
            with c2:
                st.write("**Why this rank?**")
                for r in stock['reasons']:
                    st.write(f"- {r}")

# --- Page: Watchlist ---
elif page == "Watchlist":
    st.title("⭐ Automated Watchlist")
    st.markdown("Stocks entering 'High Potential' zones based on breakouts, sentiment, and volume.")
    
    if not watchlist:
        st.info("No stocks currently meet the automated watchlist criteria.")
    else:
        for stock in watchlist:
            st.markdown(f"""
            <div class="stock-card">
                <h3>{stock['ticker']} - <span class="buy-signal">{stock['total_score']} pts</span></h3>
                <p><b>Reason for Watchlist:</b> {stock['watchlist_reason']}</p>
                <p><b>Last Close:</b> ₹{stock['metrics']['Close']} | <b>Signal:</b> {stock['signal']}</p>
            </div>
            """, unsafe_allow_html=True)

# --- Page: Technical Analysis ---
elif page == "Technical Analysis":
    from app.technical_indicators import (
        calculate_buy_sell_signals, 
        detect_chart_patterns, 
        identify_candlestick_patterns,
        identify_geometric_patterns
    )
    
    st.title("📊 High-Grade Pattern Intelligence")
    
    col_a, col_b, col_c = st.columns([2, 1, 1])
    with col_a:
        target_stock = st.selectbox("Select Stock", [s['ticker'] for s in ranked_stocks])
    with col_b:
        st.info(f"Strategy: {user_config['strategy']}")
    with col_c:
        st.info(f"Interval: {user_config['interval']}")

    df = all_dfs[target_stock]
    
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
                       vertical_spacing=0.03, subplot_titles=(target_stock, 'Volume'), 
                       row_width=[0.2, 0.7])

    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                                low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1.5), name="MA20"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], line=dict(color='blue', width=1.5), name="MA50"), row=1, col=1)
    
    # 1. Add Support/Resistance Lines
    if sup and user_config['features']['technical_indicators']: 
        fig.add_hline(y=sup, line_dash="dash", line_color="rgba(0,255,0,0.5)", row=1, col=1)
    if res and user_config['features']['technical_indicators']: 
        fig.add_hline(y=res, line_dash="dash", line_color="rgba(255,0,0,0.5)", row=1, col=1)
    
    # 2. Add Buy/Sell Markers
    if user_config['features']['buy_sell_signals'] and 'Signal' in df.columns:
        buys = df[df['Signal'] == 'BUY']
        sells = df[df['Signal'] == 'SELL']
        
        fig.add_trace(go.Scatter(x=buys.index, y=buys['Low']*0.98, mode='markers', 
                                marker=dict(symbol='triangle-up', size=12, color='green'), 
                                name='BUY Signal', hovertext=buys['Signal_Reason']), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=sells.index, y=sells['High']*1.02, mode='markers', 
                                marker=dict(symbol='triangle-down', size=12, color='red'), 
                                name='SELL Signal', hovertext=sells['Signal_Reason']), row=1, col=1)

    # 3. Add Chart Patterns
    if user_config['features']['chart_patterns']:
        # Double Bottoms
        for db in patterns.get('double_bottom', []):
            fig.add_trace(go.Scatter(x=db['x'], y=db['y'], mode='lines+markers', 
                                    line=dict(color='purple', width=2, dash='dot'), name='Double Bottom'), row=1, col=1)
        
        # Trendlines
        for tl in patterns.get('trendlines', []):
            color = 'green' if tl['type'] == 'support' else 'red'
            fig.add_trace(go.Scatter(x=tl['x'], y=tl['y'], mode='lines', 
                                    line=dict(color=color, width=2, dash='dash'), name=f'Auto {tl["type"]}'), row=1, col=1)

        # 5. Geometric Patterns (Triangles/Channels)
        for gp in geo_patterns:
            fig.add_trace(go.Scatter(x=gp['support_points']['x'], y=gp['support_points']['y'], 
                                    mode='lines', line=dict(color='rgba(0,100,255,0.4)', width=3), 
                                    name='Pattern Support'), row=1, col=1)
            fig.add_trace(go.Scatter(x=gp['resistance_points']['x'], y=gp['resistance_points']['y'], 
                                    mode='lines', line=dict(color='rgba(255,100,0,0.4)', width=3), 
                                    name='Pattern Resistance'), row=1, col=1)

    # 4. Candlestick Patterns
    if user_config['features']['candlestick_patterns']:
        # Show labels for the last 60 days to keep it clean
        recent_boundary = df.index[-60]
        for cp in candle_patterns:
            if cp['x'] >= recent_boundary:
                fig.add_annotation(x=cp['x'], y=cp['y'], text=cp['label'], 
                                   showarrow=True, arrowhead=1, ax=0, ay=-30,
                                   font=dict(size=10, color="orange"), row=1, col=1)

    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color='rgba(100,149,237,0.5)'), row=2, col=1)
    
    fig.update_layout(height=800, template="plotly_white", showlegend=True, 
                      xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, width="stretch")
    
    # Explainability Section
    if user_config['features']['buy_sell_signals']:
        last_signal = df[df['Signal'] != 'HOLD'].tail(3)
        if not last_signal.empty:
            st.subheader("💡 Recent Signal Logic")
            for _, row in last_signal.iterrows():
                color = "green" if row['Signal'] == "BUY" else "red"
                st.markdown(f"- **{row.name.date()}**: :{color}[{row['Signal']}] | Reason: *{row['Signal_Reason']}*")

# --- Page: Research Details ---
elif page == "Research Details":
    st.title("🧪 Full Research Report")
    search_query = st.text_input("Search Stock Ticker (e.g., RELIANCE.NS)", "").upper()
    
    if search_query:
        if search_query not in all_dfs:
            st.error("Stock data not found in Nifty 50 or fetch error.")
        else:
            stock_info = [s for s in ranked_stocks if s['ticker'] == search_query][0]
            news = fetch_news_rss(search_query)
            
            t1, t2, t3 = st.tabs(["Score Breakdown", "Technical Metrics", "Latest News"])
            
            with t1:
                st.header(f"Strategy Signal: {stock_info['signal']}")
                st.write(f"Overall Research Score: **{stock_info['total_score']} / 100**")
                st.subheader("Insights")
                for r in stock_info['reasons']:
                    st.success(r)
                    
            with t2:
                df_last = all_dfs[search_query].iloc[-1]
                c1, c2, c3 = st.columns(3)
                c1.metric("RSI (14)", round(df_last['RSI'], 2))
                c2.metric("MA 20 Cross", "Above" if df_last['Close'] > df_last['MA20'] else "Below")
                c3.metric("10 Day Momentm", f"{round(df_last['Momentum'], 2)}%")
                
            with t3:
                for n in news:
                    st.markdown(f"**[{n['title']}]({n['link']})**")
                    st.caption(f"Published: {n['published']}")
                    st.write(n['summary'])
                    st.markdown("---")

# --- Page: AI Research Assistant ---
elif page == "AI Research Assistant":
    st.title("🤖 AI Research Assistant")
    st.markdown("Ask questions about the Indian stock market, Nifty 50 trends, or specific tickers.")

    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("Ask: 'Which are the top stocks?' or 'Why is SBIN.NS trending?'"):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate Response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing market data..."):
                response = advisor.process_query(prompt)
                st.markdown(response)
        
        # Add assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": response})
