import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Import your custom modules
import data_fetcher
import strategy # <-- Using your 'strategy' file name
import backtester
import utils

# Set up the Streamlit page
st.set_page_config(layout="wide")
st.title("📈 Moving Average Crossover Backtesting Engine")

# --- Sidebar for User Inputs ---
st.sidebar.header("Strategy Configuration")

# --- Section 1: Single Stock Test ---
st.sidebar.markdown("### 1. Single Stock Test")
ticker = st.sidebar.text_input("Stock Ticker", "RELIANCE.NS")
st.sidebar.caption("Use tickers from Yahoo Finance (e.g., INFY.NS, TCS.NS, HDFCBANK.NS)")

# --- Section 2: Batch Test (NSE 500) ---
st.sidebar.markdown("### 2. Batch Test (NSE 500)")
uploaded_file = st.sidebar.file_uploader("Upload NSE 500 Tickers CSV", type="csv")
st.sidebar.caption("CSV must have a 'Symbol' column with .NS tickers.")


# --- Section 3: Shared Parameters ---
st.sidebar.markdown("### 3. Strategy Parameters")
# Date Range
# Set a default 3-month backtest period
default_start_date = datetime.now() - timedelta(days=90)
default_end_date = datetime.now()

# CHANGED: These labels are now specific
selected_start_date = st.sidebar.date_input("Backtest Start Date", default_start_date)
selected_end_date = st.sidebar.date_input("Backtest End Date", default_end_date)


# --- Strategy Parameters ---
ma_type = st.sidebar.selectbox("Moving Average Type", ["EMA", "SMA", "WMA"])
fast_period = st.sidebar.number_input("Fast MA Period", min_value=1, max_value=100, value=12)
slow_period = st.sidebar.number_input("Slow MA Period", min_value=1, max_value=250, value=26)

# Validate that slow > fast
if slow_period <= fast_period:
    st.sidebar.error("Slow MA Period must be greater than Fast MA Period.")
    st.stop()

# --- NEW: Calculate "Warm-up" period ---
# We must fetch data from *before* the backtest start date to calculate the MAs.
# We'll add a buffer (e.g., 60 days) to the slow_period to be safe.
warm_up_days = slow_period + 60
data_fetch_start_date = selected_start_date - timedelta(days=warm_up_days)


# --- Exit Rules ---
exit_strategy = st.sidebar.selectbox("Exit Strategy", ["Take Profit / Stop Loss", "Reverse Crossover"])

take_profit = None
stop_loss = None
strategy_name = f"{fast_period}/{slow_period}-day {ma_type} Crossover"

if exit_strategy == "Take Profit / Stop Loss":
    take_profit_pct = st.sidebar.number_input("Take Profit %", min_value=0.1, max_value=100.0, value=10.0, step=0.5)
    stop_loss_pct = st.sidebar.number_input("Stop Loss %", min_value=0.1, max_value=100.0, value=5.0, step=0.5)
    
    # Convert from % to decimal
    take_profit = take_profit_pct / 100.0
    stop_loss = stop_loss_pct / 100.0
    
    exit_criteria_str = f"Sell at {take_profit_pct}% profit or {stop_loss_pct}% loss."
else:
    exit_criteria_str = "Sell when Fast MA crosses below Slow MA."


# --- Run Backtest Buttons ---
st.sidebar.markdown("---")

# Button 1: Single Stock
if st.sidebar.button("Run Single Stock Test", use_container_width=True):
    with st.spinner(f"Running backtest for {ticker}..."):
        
        # 1. Fetch Data
        try:
            # CHANGED: Fetch data from the *earlier* warm-up date
            data = data_fetcher.fetch_data(ticker, data_fetch_start_date, selected_end_date)
            if data.empty:
                st.error("No data found for the given ticker and date range. Please check the ticker symbol.")
                st.stop()
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            st.stop()

        # 2. Generate Signals (on all fetched data)
        signals_df = strategy.generate_signals(data, ma_type, fast_period, slow_period)
        
        # 3. CHANGED: Slice the DataFrame to the *exact* backtest period
        test_df = signals_df[selected_start_date:selected_end_date].copy()
        
        if test_df.empty:
            st.error("Not enough data for the selected backtest period. Try an earlier start date or later end date.")
            st.stop()

        # 4. Run Backtest
        results = backtester.run_backtest(test_df, exit_strategy, take_profit, stop_loss)

        # 5. Prepare Report
        backtest_period = f"{test_df.index.min().strftime('%Y-%m-%d')} to {test_df.index.max().strftime('%Y-%m-%d')}"
        entry_criteria = f"Buy when {fast_period}-day {ma_type} crosses above {slow_period}-day {ma_type}"

        # --- Display Results ---
        st.subheader(f"Single Stock Report: {ticker}")
        
        utils.display_metrics_table(
            results,
            strategy_name,
            ticker,
            backtest_period,
            entry_criteria,
            exit_criteria_str
        )
        st.markdown("---")
        st.subheader("Performance Graph")
        fig = utils.plot_backtest_graph(test_df, results['trades'], strategy_name)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")
        st.subheader("Trade Log")
        st.dataframe(results['trades'])

# Button 2: Batch Test
elif st.sidebar.button("Run Batch Backtest", use_container_width=True):
    if uploaded_file is None:
        st.sidebar.error("Please upload a 'nifty500.csv' file to run a batch test.")
        st.stop()

    with st.spinner("Running batch backtest... This may take a while. Grab a coffee. ☕"):
        # Load ticker list
        try:
            ticker_list_df = pd.read_csv(uploaded_file)
            if 'Symbol' not in ticker_list_df.columns:
                st.error("CSV file must have a column named 'Symbol'.")
                st.stop()
            tickers = ticker_list_df['Symbol'].tolist()
        except Exception as e:
            st.error(f"Error reading CSV file: {e}")
            st.stop()
        
        all_results = []
        total_tickers = len(tickers)
        progress_bar = st.progress(0, text="Batch test started...")
        
        # Loop through all tickers
        for i, ticker in enumerate(tickers):
            progress_bar.progress((i+1)/total_tickers, text=f"Testing {ticker} ({i+1}/{total_tickers})")
            
            # 1. Fetch Data
            # CHANGED: Fetch data from the *earlier* warm-up date
            data = data_fetcher.fetch_data(ticker, data_fetch_start_date, selected_end_date, is_batch=True)
            if data.empty:
                print(f"Skipping {ticker}: No data fetched.")
                continue

            # 2. Generate Signals
            signals_df = strategy.generate_signals(data, ma_type, fast_period, slow_period)
            
            # 3. CHANGED: Slice the DataFrame to the *exact* backtest period
            test_df = signals_df[selected_start_date:selected_end_date].copy()
            
            if test_df.empty:
                print(f"Skipping {ticker}: No data in test period.")
                continue

            # 4. Run Backtest
            results = backtester.run_backtest(test_df, exit_strategy, take_profit, stop_loss)
            
            # 5. Store results
            all_results.append({
                'ticker': ticker,
                'total_return': results['total_return'],
                'max_drawdown': results['max_drawdown'],
                'win_rate': results['win_rate'],
                'total_trades': results['total_trades']
            })

        progress_bar.empty() # Remove progress bar when done
        
        if not all_results:
            st.error("Batch test completed, but no trades were executed for any stock in the list.")
            st.stop()

        # Convert final list to a DataFrame
        results_df = pd.DataFrame(all_results)
        
        # --- Display Batch Results ---
        utils.display_batch_results(results_df, strategy_name)

else:
    st.info("Configure your strategy in the sidebar and click a 'Run' button.")