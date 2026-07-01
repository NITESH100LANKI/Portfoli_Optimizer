import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from app.utils.logger import setup_logger

logger = setup_logger("technical_indicators")

def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Manual implementation of technical indicators with aggressive 1D safety."""
    if df.empty:
        return df
    
    # 1. Aggressive Data Cleaning
    # Remove any duplicate columns and indices that might cause dimension doubling
    df = df.loc[:, ~df.columns.duplicated()].copy()
    df = df.loc[~df.index.duplicated(keep='first')].copy()
    
    # Ensure dataframe has a datetime index
    df.index = pd.to_datetime(df.index)
    
    # helper for safe 1D series
    def get_1d_array(name):
        col = df[name]
        if isinstance(col, pd.DataFrame):
            col = col.iloc[:, 0]
        return col.values.flatten()

    close_arr = get_1d_array('Close')
    high_arr = get_1d_array('High')
    low_arr = get_1d_array('Low')
    
    # 1. Moving Averages (SMA)
    df['MA20'] = pd.Series(close_arr, index=df.index).rolling(window=20).mean()
    df['MA50'] = pd.Series(close_arr, index=df.index).rolling(window=50).mean()
    df['MA200'] = pd.Series(close_arr, index=df.index).rolling(window=200).mean()
    
    # 2. RSI (14)
    delta = pd.Series(close_arr).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = (100 - (100 / (1 + rs))).values
    
    # 3. MACD (12, 26, 9)
    close_ser = pd.Series(close_arr, index=df.index)
    exp1 = close_ser.ewm(span=12, adjust=False).mean()
    exp2 = close_ser.ewm(span=26, adjust=False).mean()
    df['MACD_12_26_9'] = exp1 - exp2
    df['MACDs_12_26_9'] = df['MACD_12_26_9'].ewm(span=9, adjust=False).mean()
    df['MACDh_12_26_9'] = df['MACD_12_26_9'] - df['MACDs_12_26_9']
    
    # 4. ATR (14)
    tr1 = high_arr - low_arr
    tr2 = np.abs(high_arr - np.roll(close_arr, 1))
    tr3 = np.abs(low_arr - np.roll(close_arr, 1))
    tr = np.maximum(tr1, np.maximum(tr2, tr3))
    df['ATR'] = pd.Series(tr, index=df.index).rolling(window=14).mean()
    
    # 5. Bollinger Bands (20, 2)
    ma20 = pd.Series(close_arr, index=df.index).rolling(window=20).mean()
    std20 = pd.Series(close_arr, index=df.index).rolling(window=20).std()
    df['BBM_20_2.0'] = ma20
    df['BBU_20_2.0'] = ma20 + (std20 * 2)
    df['BBL_20_2.0'] = ma20 - (std20 * 2)
        
    # 6. ADX (14)
    upmove = np.diff(high_arr, prepend=high_arr[0])
    downmove = np.diff(low_arr, prepend=low_arr[0])
    
    pos_dm = np.where((upmove > downmove) & (upmove > 0), upmove, 0)
    neg_dm = np.where((downmove > upmove) & (downmove > 0), downmove, 0)
    
    smooth_pos_dm = pd.Series(pos_dm).rolling(14).mean()
    smooth_neg_dm = pd.Series(neg_dm).rolling(14).mean()
    tr_sum = pd.Series(tr).rolling(14).sum()
    
    di_pos = 100 * (smooth_pos_dm / tr_sum)
    di_neg = 100 * (smooth_neg_dm / tr_sum)
    dx = 100 * np.abs(di_pos - di_neg) / (di_pos + di_neg)
    
    df['ADX_14'] = dx.rolling(14).mean().values
        
    # 7. Momentum
    df['Momentum'] = pd.Series(close_arr, index=df.index).diff(10)
    
    return df

def detect_support_resistance(df: pd.DataFrame, window: int = 20):
    """Simple support and resistance detection based on local min/max."""
    if len(df) < window: return (None, None)
    
    recent_data = df.tail(window * 2)
    res = recent_data['High'].max()
    sup = recent_data['Low'].min()
    return sup, res

def calculate_buy_sell_signals(df: pd.DataFrame) -> pd.DataFrame:
    """ Generates Buy/Sell signals based on combined technical conditions. """
    if df.empty or 'RSI' not in df.columns:
        return df

    df['Signal'] = 'HOLD'
    df['Signal_Reason'] = ''

    # BUY CONDITIONS
    req_cols = ['RSI', 'MACD_12_26_9', 'MACDs_12_26_9', 'MA20']
    if not all(col in df.columns for col in req_cols):
        logger.warning(f"Missing required columns for signals: {[c for c in req_cols if c not in df.columns]}")
        return df

    for i in range(1, len(df)):
        # Buy Signal
        buy_cond = (
            (df['RSI'].iloc[i] > 30 and df['RSI'].iloc[i-1] <= 30) or  # RSI reversal
            (df['MACD_12_26_9'].iloc[i] > df['MACDs_12_26_9'].iloc[i] and df['MACD_12_26_9'].iloc[i-1] <= df['MACDs_12_26_9'].iloc[i-1]) or # MACD cross
            (df['Close'].iloc[i] > df['MA20'].iloc[i] and df['Close'].iloc[i-1] <= df['MA20'].iloc[i-1]) # EMA breakout
        )
        
        # Sell Signal
        sell_cond = (
            (df['RSI'].iloc[i] < 70 and df['RSI'].iloc[i-1] >= 70) or # RSI overbought reversal
            (df['MACD_12_26_9'].iloc[i] < df['MACDs_12_26_9'].iloc[i] and df['MACD_12_26_9'].iloc[i-1] >= df['MACDs_12_26_9'].iloc[i-1]) # MACD death cross
        )

        if buy_cond:
            df.iloc[i, df.columns.get_loc('Signal')] = 'BUY'
            reasons = []
            if df['RSI'].iloc[i] > 30 and df['RSI'].iloc[i-1] <= 30: reasons.append("RSI Reversal")
            if df['MACD_12_26_9'].iloc[i] > df['MACDs_12_26_9'].iloc[i]: reasons.append("MACD Bullish Cross")
            if df['Close'].iloc[i] > df['MA20'].iloc[i]: reasons.append("EMA20 Breakout")
            df.iloc[i, df.columns.get_loc('Signal_Reason')] = " + ".join(reasons)
        elif sell_cond:
            df.iloc[i, df.columns.get_loc('Signal')] = 'SELL'
            df.iloc[i, df.columns.get_loc('Signal_Reason')] = "Technical Reversal / Overbought"

    return df

def detect_chart_patterns(df: pd.DataFrame):
    """ 
    Detects Double Top, Double Bottom and Trendlines using pivot analysis.
    Returns a dictionary of detected patterns.
    """
    if len(df) < 60: return {}
    
    data = df['Close'].values
    patterns = {'double_bottom': [], 'double_top': [], 'trendlines': []}
    
    # Finding peaks and troughs (Pivots)
    from scipy.signal import argrelextrema
    import numpy as np
    
    # Local Minima (Bottoms)
    min_idx = argrelextrema(data, np.less, order=10)[0]
    # Local Maxima (Tops)
    max_idx = argrelextrema(data, np.greater, order=10)[0]
    
    # 1. Double Bottom Detection
    if len(min_idx) >= 2:
        for i in range(len(min_idx)-1):
            p1, p2 = min_idx[i], min_idx[i+1]
            price1, price2 = data[p1], data[p2]
            
            # Check price similarity (within 2%)
            if abs(price1 - price2) / max(price1, price2) < 0.02:
                # Ensure there is a "peak" in between
                between = data[p1:p2]
                if len(between) > 5 and max(between) > max(price1, price2) * 1.05:
                    patterns['double_bottom'].append({'x': [df.index[p1], df.index[p2]], 'y': [price1, price2]})

    # 2. Automated Trendlines (Support)
    if len(min_idx) >= 3:
        # Simple support line connecting last two troughs if sloping up
        p1, p2 = min_idx[-2], min_idx[-1]
        patterns['trendlines'].append({'x': [df.index[p1], df.index[p2]], 'y': [data[p1], data[p2]], 'type': 'support'})

    # 3. Automated Trendlines (Resistance)
    if len(max_idx) >= 3:
        p1, p2 = max_idx[-2], max_idx[-1]
        patterns['trendlines'].append({'x': [df.index[p1], df.index[p2]], 'y': [data[p1], data[p2]], 'type': 'resistance'})

    return patterns

def identify_candlestick_patterns(df: pd.DataFrame) -> Dict[str, List[Dict]]:
    """Detects major candlestick patterns using TA-Lib."""
    import talib
    if len(df) < 5: return {}
    
    patterns = []
    
    O, H, L, C = df['Open'], df['High'], df['Low'], df['Close']
    
    # 1. Bullish Engulfing
    eng_bull = talib.CDLENGULFING(O, H, L, C)
    for idx in eng_bull[eng_bull > 0].index:
        patterns.append({'x': idx, 'y': H.loc[idx], 'label': '🐂 Bull Engulf', 'type': 'bullish'})
        
    # 2. Bearish Engulfing
    eng_bear = talib.CDLENGULFING(O, H, L, C)
    for idx in eng_bear[eng_bear < 0].index:
        patterns.append({'x': idx, 'y': H.loc[idx], 'label': '🐻 Bear Engulf', 'type': 'bearish'})
        
    # 3. Hammer
    hammer = talib.CDLHAMMER(O, H, L, C)
    for idx in hammer[hammer > 0].index:
        patterns.append({'x': idx, 'y': L.loc[idx], 'label': '🔨 Hammer', 'type': 'bullish'})
        
    # 4. Shooting Star
    star = talib.CDLSHOOTINGSTAR(O, H, L, C)
    for idx in star[star > 0].index:
        patterns.append({'x': idx, 'y': H.loc[idx], 'label': '⭐ Shooting Star', 'type': 'bearish'})
        
    # 5. Morning Star
    m_star = talib.CDLMORNINGSTAR(O, H, L, C)
    for idx in m_star[m_star > 0].index:
        patterns.append({'x': idx, 'y': L.loc[idx], 'label': '🌅 Morning Star', 'type': 'bullish'})
        
    return patterns

def identify_geometric_patterns(df: pd.DataFrame) -> Dict[str, List[Dict]]:
    """ 
    Detects complex geometric patterns like Triangles and Channels.
    Uses linear regression on pivots.
    """
    from scipy.signal import argrelextrema
    from scipy.stats import linregress
    import numpy as np
    
    if len(df) < 60: return {}
    
    data = df['Close'].values
    patterns = []
    
    # Finding pivots
    min_idx = argrelextrema(data, np.less, order=15)[0]
    max_idx = argrelextrema(data, np.greater, order=15)[0]
    
    if len(min_idx) >= 3 and len(max_idx) >= 3:
        # Check for Triangle (Diverging/Converging)
        # S1: Support Line
        slope_min, intercept_min, r_min, p_min, std_min = linregress(min_idx[-3:], data[min_idx[-3:]])
        # R1: Resistance Line
        slope_max, intercept_max, r_max, p_max, std_max = linregress(max_idx[-3:], data[max_idx[-3:]])
        
        # Ascending Triangle: slope_min > 0, abs(slope_max) ~ 0
        # Descending Triangle: abs(slope_min) ~ 0, slope_max < 0
        # Symmetrical Triangle: slope_min > 0, slope_max < 0
        
        # We'll return the trendlines for the last section
        patterns.append({
            'type': 'Triangle/Channel Bounds',
            'support_points': {'x': [df.index[min_idx[-3]], df.index[-1]], 
                             'y': [data[min_idx[-3]], slope_min * (len(df)-1 - min_idx[-3]) + data[min_idx[-3]]]},
            'resistance_points': {'x': [df.index[max_idx[-3]], df.index[-1]], 
                                'y': [data[max_idx[-3]], slope_max * (len(df)-1 - max_idx[-3]) + data[max_idx[-3]]]}
        })
        
    return patterns
