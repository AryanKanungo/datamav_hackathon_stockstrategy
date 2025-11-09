import yfinance as yf
import pandas as pd
from datetime import datetime
import streamlit as st # Import streamlit for st.warning

def fetch_data(ticker: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Fetches historical stock data from Yahoo Finance.
    
    Args:
        ticker (str): The stock ticker symbol (e.g., "RELIANCE.NS").
        start_date (datetime): The start date for the data.
        end_date (datetime): The end date for the data.
        
    Returns:
        pd.DataFrame: A DataFrame with historical stock data, indexed by Date.
                      Contains 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'.
    """
    try:
        data = yf.download(ticker, start=start_date, end=end_date)
        
        if data.empty:
            print(f"No data returned for ticker {ticker} from {start_date} to {end_date}.")
            return pd.DataFrame()
            
        # --- FIX for Multi-Ticker input ---
        # If yfinance returns a MultiIndex (because user entered >1 ticker),
        # we select the data for the *first* ticker to proceed.
        if isinstance(data.columns, pd.MultiIndex):
            # Get the first ticker from the 'level 1' of the columns
            first_ticker = data.columns.levels[1][0]
            st.warning(f"Multiple tickers detected. Selecting first ticker: {first_ticker}")
            
            # Select all columns for this first ticker
            # and drop the multi-index
            data = data.xs(first_ticker, axis=1, level=1)
            
            # The columns are now 'Adj Close', 'Close', etc.
            # Let's capitalize them for consistency.
            data.columns = [col.capitalize() for col in data.columns]
        # --- End of Fix ---
            
        # Ensure the index is a DatetimeIndex
        data.index = pd.to_datetime(data.index)
        
        return data
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    # Example usage:
    ticker = "TCS.NS"
    end = datetime.now()
    start = end - pd.DateOffset(years=1)
    
    df = fetch_data(ticker, start, end)
    
    if not df.empty:
        print(f"Successfully fetched {len(df)} rows for {ticker}.")
        print(df.tail())
    else:
        print(f"Failed to fetch data for {ticker}.")