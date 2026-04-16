import pandas as pd
import numpy as np

def manual_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def manual_macd(series, fast=12, slow=26, signal=9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def manual_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_cp = np.abs(df['High'] - df['Close'].shift())
    low_cp = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

# Test data
data = {
    'High': [102, 103, 101, 105, 107, 108, 110, 111, 112, 113, 115, 116, 117, 118, 119],
    'Low': [100, 101, 99, 103, 105, 106, 108, 109, 110, 111, 112, 113, 114, 115, 116],
    'Close': [101, 102, 100, 104, 106, 107, 109, 110, 111, 112, 113, 114, 115, 116, 117]
}
df = pd.DataFrame(data)

rsi = manual_rsi(df['Close'])
m, s, h = manual_macd(df['Close'])
atr = manual_atr(df)

print("RSI:", rsi.tail())
print("MACD:", m.tail())
print("ATR:", atr.tail())
