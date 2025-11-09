import pandas as pd
import numpy as np

def calculate_ma(data: pd.Series, ma_type: str, period: int) -> pd.Series:
    """
    Calculates a single moving average.
    
    Args:
        data (pd.Series): Series of closing prices.
        ma_type (str): "SMA", "EMA", or "WMA".
        period (int): The window period for the MA.
        
    Returns:
        pd.Series: The calculated moving average.
    """
    if ma_type == "SMA":
        return data.rolling(window=period).mean()
    elif ma_type == "EMA":
        return data.ewm(span=period, adjust=False).mean()
    elif ma_type == "WMA":
        weights = np.arange(1, period + 1)
        return data.rolling(window=period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    else:
        raise ValueError("Invalid MA Type. Use 'SMA', 'EMA', or 'WMA'.")

def generate_signals(data: pd.DataFrame, ma_type: str, fast_period: int, slow_period: int) -> pd.DataFrame:
    """
    Generates trading signals based on MA crossover.
    
    Args:
        data (pd.DataFrame): The input stock data (from data_fetcher).
        ma_type (str): "SMA", "EMA", or "WMA".
        fast_period (int): The window for the fast MA.
        slow_period (int): The window for the slow MA.
        
    Returns:
        pd.DataFrame: A copy of the input DataFrame with new columns:
                      'fast_ma', 'slow_ma', 'signal', 'position'.
    """
    df = data.copy()
    
    # Calculate MAs
    df['fast_ma'] = calculate_ma(df['Close'], ma_type, fast_period)
    df['slow_ma'] = calculate_ma(df['Close'], ma_type, slow_period)
    
    # Drop rows with NaN values (which occur at the beginning due to MA calculation)
    df.dropna(inplace=True)
    
    # Generate the signal (1 if fast > slow, 0 otherwise)
    # This tells us the *state* we want to be in.
    df['signal'] = np.where(df['fast_ma'] > df['slow_ma'], 1, 0)
    
    # Generate the position (the *action* to take)
    # .diff() finds the day the signal *changes*.
    # 1.0 means a bullish crossover (Buy)
    # -1.0 means a bearish crossover (Sell)
    df['position'] = df['signal'].diff()
    
    return df
