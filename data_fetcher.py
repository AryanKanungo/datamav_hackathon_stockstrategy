# data_fetcher.py
import yfinance as yf
from datetime import date, timedelta
import pandas as pd

def fetch_stock_data(symbol: str, months: int = 3) -> pd.DataFrame:
    """Fetch EOD OHLCV data for a given NSE symbol using yfinance.
       Symbol can be provided without .NS (we append if missing).
    """
    if not symbol.upper().endswith(".NS"):
        ticker = f"{symbol}.NS"
    else:
        ticker = symbol

    end_date = date.today()
    start_date = end_date - timedelta(days=months * 30)
    df = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)
    if df is None or df.empty:
        return pd.DataFrame()
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
    return df
