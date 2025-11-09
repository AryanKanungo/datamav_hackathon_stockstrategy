# strategy.py
import pandas as pd
import numpy as np

def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period).mean()

def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()

def wma(series: pd.Series, period: int) -> pd.Series:
    weights = np.arange(1, period + 1)
    return series.rolling(period).apply(lambda x: np.dot(x, weights)/weights.sum(), raw=True)

def apply_ma(df: pd.DataFrame, ma_type: str, period: int, column: str = "Close") -> pd.Series:
    ma_type = ma_type.upper()
    if ma_type == "SMA":
        return sma(df[column], period)
    elif ma_type == "EMA":
        return ema(df[column], period)
    elif ma_type == "WMA":
        return wma(df[column], period)
    else:
        raise ValueError("ma_type must be SMA/EMA/WMA")

def generate_signals(df: pd.DataFrame, ma_type: str, fast: int, slow: int) -> pd.DataFrame:
    """Add Fast_MA, Slow_MA, Signal columns to dataframe.
       Signal: 1 for bullish (fast > slow), -1 for bearish (fast < slow), 0 otherwise.
    """
    df = df.copy()
    df['Fast_MA'] = apply_ma(df, ma_type, fast)
    df['Slow_MA'] = apply_ma(df, ma_type, slow)
    df['Signal'] = 0
    df.loc[df['Fast_MA'] > df['Slow_MA'], 'Signal'] = 1
    df.loc[df['Fast_MA'] < df['Slow_MA'], 'Signal'] = -1
    return df

def heikin_ashi(df: pd.DataFrame) -> pd.DataFrame:
    """Return heikin-ashi candles as a DataFrame with columns HA_Open, HA_High, HA_Low, HA_Close."""
    ha = pd.DataFrame(index=df.index)
    ha['HA_Close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4.0
    ha['HA_Open'] = 0.0
    ha['HA_Open'].iat[0] = (df['Open'].iat[0] + df['Close'].iat[0]) / 2.0
    for i in range(1, len(df)):
        ha['HA_Open'].iat[i] = (ha['HA_Open'].iat[i-1] + ha['HA_Close'].iat[i-1]) / 2.0
    ha['HA_High'] = pd.concat([df['High'], ha['HA_Open'], ha['HA_Close']], axis=1).max(axis=1)
    ha['HA_Low']  = pd.concat([df['Low'], ha['HA_Open'], ha['HA_Close']], axis=1).min(axis=1)
    return ha[['HA_Open','HA_High','HA_Low','HA_Close']]

def renko_bricks(df: pd.DataFrame, brick_size: float = None, atr_period: int = 14) -> pd.DataFrame:
    """
    Simple Renko brick construction:
    - If brick_size is None, use ATR-based brick: avg true range of last atr_period closes.
    - Returns a DataFrame with columns: 'brick_index', 'brick_price', 'direction' (1 up, -1 down)
    """
    from ta.volatility import AverageTrueRange
    df2 = df.copy()
    if brick_size is None:
        try:
            atr = AverageTrueRange(df2['High'], df2['Low'], df2['Close'], window=atr_period)
            brick_size = max(0.5, atr.average_true_range().dropna().iloc[-1])  # minimum sensible brick
        except Exception:
            # fallback: percentage of median price
            brick_size = max(0.5, df2['Close'].median() * 0.01)

    bricks = []
    last_brick_price = df2['Close'].iat[0]
    direction = 0
    for price in df2['Close']:
        diff = price - last_brick_price
        while abs(diff) >= brick_size:
            if diff > 0:
                last_brick_price = last_brick_price + brick_size
                direction = 1
            else:
                last_brick_price = last_brick_price - brick_size
                direction = -1
            bricks.append({'brick_price': last_brick_price, 'direction': direction})
            diff = price - last_brick_price
    return pd.DataFrame(bricks)
