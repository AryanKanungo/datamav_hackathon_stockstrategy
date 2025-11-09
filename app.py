import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Import your custom modules
import data_fetcher
import strategy
import backtester
import utils

# Set up the Streamlit page
st.set_page_config(layout="wide")
st.title("📈 Moving Average Crossover Backtesting Engine")

# --- Sidebar for User Inputs ---
st.sidebar.header("Strategy Configuration")

# Stock Selection
st.sidebar.markdown("### 1. Stock Data")
ticker = st.sidebar.text_input("Stock Ticker", "RELIANCE.NS")
st.sidebar.caption("Use tickers from Yahoo Finance (e.g., INFY.NS, TCS.NS, HDFCBANK.NS)")

# Date Range
end_date = datetime.now()
start_date = end_date - timedelta(days=3*365) # Default to 3 years for better MA calculation
selected_start_date = st.sidebar.date_input("Start Date", start_date)
selected_end_date = st.sidebar.date_input("End Date", end_date)

# --- Strategy Parameters ---
st.sidebar.markdown("### 2. Strategy Parameters")
ma_type = st.sidebar.selectbox("Moving Average Type", ["EMA", "SMA", "WMA"])
fast_period = st.sidebar.number_input("Fast MA Period", min_value=1, max_value=100, value=12)
slow_period = st.sidebar.number_input("Slow MA Period", min_value=1, max_value=250, value=26)

# Validate that slow > fast
if slow_period <= fast_period:
    st.sidebar.error("Slow MA Period must be greater than Fast MA Period.")
    st.stop()

# --- Exit Rules ---
st.sidebar.markdown("### 3. Exit Rules")
exit_strategy = st.sidebar.selectbox("Exit Strategy", ["Take Profit / Stop Loss", "Reverse Crossover"])

take_profit = None
stop_loss = None

if exit_strategy == "Take Profit / Stop Loss":
    take_profit_pct = st.sidebar.number_input("Take Profit %", min_value=0.1, max_value=100.0, value=10.0, step=0.5)
    stop_loss_pct = st.sidebar.number_input("Stop Loss %", min_value=0.1, max_value=100.0, value=5.0, step=0.5)
    
    # Convert from % to decimal
    take_profit = take_profit_pct / 100.0
    stop_loss = stop_loss_pct / 100.0
    
    exit_criteria_str = f"Sell at {take_profit_pct}% profit or {stop_loss_pct}% loss."
else:
    exit_criteria_str = "Sell when Fast MA crosses below Slow MA."


# --- Run Backtest Button ---
st.sidebar.markdown("---")
if st.sidebar.button("Run Backtest", use_container_width=True):
    with st.spinner("Running backtest... This may take a moment."):
        
        # 1. Fetch Data
        try:
            data = data_fetcher.fetch_data(ticker, selected_start_date, selected_end_date)
            if data.empty:
                st.error("No data found for the given ticker and date range. Please check the ticker symbol.")
                st.stop()
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            st.stop()

        # 2. Generate Signals
        signals_df = strategy.generate_signals(data, ma_type, fast_period, slow_period)
        
        # Filter signals_df to the hackathon's 3-month period (Aug 1 - Oct 31, 2025)
        # We use *longer* data to calculate MAs, but *test* on the specific period.
        
        # Let's make the 3-month period dynamic, based on the *end date*
        # As per prompt: "last 3 months"
        test_end_date = selected_end_date
        test_start_date = test_end_date - timedelta(days=90)
        
        # Filter the dataframe for the actual 3-month test period
        test_df = signals_df[test_start_date:test_end_date].copy()
        
        if test_df.empty:
            st.error("Not enough data in the selected 3-month test period. Please select a later End Date.")
            st.stop()

        # 3. Run Backtest
        results = backtester.run_backtest(test_df, exit_strategy, take_profit, stop_loss)

        # 4. Prepare Report Strings
        strategy_name = f"{fast_period}/{slow_period}-day {ma_type} Crossover"
        backtest_period = f"{test_df.index.min().strftime('%Y-%m-%d')} to {test_df.index.max().strftime('%Y-%m-%d')}"
        entry_criteria = f"Buy when {fast_period}-day {ma_type} crosses above {slow_period}-day {ma_type}"

        # --- Display Results ---
        st.subheader("Backtest Report")
        
        # 4a. Display Hackathon Metrics Table
        utils.display_metrics_table(
            results,
            strategy_name,
            ticker,
            backtest_period,
            entry_criteria,
            exit_criteria_str
        )
        
        st.markdown("---")

        # 4b. Display Performance Graph
        st.subheader("Performance Graph")
        fig = utils.plot_backtest_graph(test_df, results['trades'], strategy_name)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")

        # 4c. Display Trade Log
        st.subheader("Trade Log")
        st.dataframe(results['trades'])

else:
    st.info("Configure your strategy in the sidebar and click 'Run Backtest'.")