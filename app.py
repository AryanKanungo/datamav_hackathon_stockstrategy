import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random
import os

# Import your custom modules
import data_fetcher
import strategy 
import backtester
import utils

# ---
# PAGE CONFIG
# ---
st.set_page_config(layout="wide", page_title="Hybrid Strategy Backtester")
st.title("📈 4:1 (20%/5%) Hybrid Strategy Backtester")
st.subheader("Strategy: 1-Day Price / 45-Day SMA Crossover")


# ---
# HARDCODED STRATEGY PARAMETERS
# ---
STRATEGY_NAME = "Hybrid 4:1: 1/45 SMA, 20%/5%"
FAST_PERIOD = 1
SLOW_PERIOD = 45
MA_TYPE = "SMA"
EXIT_STRATEGY = "Take Profit / Stop Loss"
TAKE_PROFIT_PCT = 20.0
STOP_LOSS_PCT = 5.0
TRADE_TIMEOUT_DAYS = 60

# Calculate decimal values
TAKE_PROFIT = TAKE_PROFIT_PCT / 100.0
STOP_LOSS = STOP_LOSS_PCT / 100.0

# Define strategy strings for reports
ENTRY_CRITERIA_STR = f"Buy on {FAST_PERIOD}/{SLOW_PERIOD} {MA_TYPE} bullish crossover (at Close)."
EXIT_CRITERIA_STR = f"Sell at {TAKE_PROFIT_PCT}% T/P, {STOP_LOSS_PCT}% S/L, or {TRADE_TIMEOUT_DAYS}-day timeout (at Close)."


# ---
# HELPER FUNCTION (to run a single test)
# ---
@st.cache_data
def run_full_test_for_ticker(ticker, data_fetch_start_date, selected_end_date, selected_start_date):
    """Helper to run the full data-fetch and backtest pipeline for one ticker."""
    data = data_fetcher.fetch_data(ticker, data_fetch_start_date, selected_end_date)
    if data.empty:
        return None, None

    signals_df = strategy.generate_signals(data, MA_TYPE, FAST_PERIOD, SLOW_PERIOD)
    test_df = signals_df[selected_start_date:selected_end_date].copy()
    if test_df.empty:
        return None, None
        
    results = backtester.run_backtest(
        test_df, EXIT_STRATEGY, TAKE_PROFIT, STOP_LOSS, TRADE_TIMEOUT_DAYS
    )
    return test_df, results


# ---
# SIDEBAR
# ---
st.sidebar.header("Test Configuration")

# --- Section 1: Single Stock Test ---
st.sidebar.markdown("### 1. Single Stock Test")
ticker_input = st.sidebar.text_input("Stock Ticker", "RELIANCE.NS")
st.sidebar.caption("e.g., INFY.NS, TCS.NS, HDFCBANK.NS")

# --- Section 2: Batch Test (NSE 500) ---
st.sidebar.markdown("### 2. Batch Test")
csv_file_path = "nifty500.csv"
st.sidebar.caption(f"Using tickers from: `{csv_file_path}`")
num_stocks_to_test = st.sidebar.number_input(
    "Number of Stocks to Test", min_value=1, value=50
)
st.sidebar.caption(f"Will randomly select {num_stocks_to_test} stocks.")

# --- Section 3: Date Range ---
st.sidebar.markdown("### 3. Backtest Period")
default_start_date = datetime(2025, 8, 1)
default_end_date = datetime(2025, 10, 31)
selected_start_date = st.sidebar.date_input("Backtest Start Date", default_start_date)
selected_end_date = st.sidebar.date_input("Backtest End Date", default_end_date)

# Calculate "Warm-up" period
warm_up_days = SLOW_PERIOD + 60
data_fetch_start_date = selected_start_date - timedelta(days=warm_up_days)
backtest_period_str = f"{selected_start_date.strftime('%Y-%m-%d')} to {selected_end_date.strftime('%Y-%m-%d')}"

# --- Run Backtest Buttons ---
st.sidebar.markdown("---")

# Button 1: Single Stock
if st.sidebar.button("Run Single Stock Test", use_container_width=True, type="primary"):
    st.session_state.clear() # Clear old results
    st.session_state.run_mode = 'single'
    
    with st.spinner(f"Running backtest for {ticker_input}..."):
        test_df, results = run_full_test_for_ticker(
            ticker_input, data_fetch_start_date, selected_end_date, selected_start_date
        )
        if test_df is None:
            st.error("No data found or not enough data for backtest. Check ticker or date range.")
            st.session_state.run_mode = 'none'
        else:
            st.session_state.single_ticker = ticker_input
            st.session_state.single_test_df = test_df
            st.session_state.single_results = results
            st.success(f"Backtest for {ticker_input} complete.")

# Button 2: Batch Test
if st.sidebar.button("Run Batch Backtest", use_container_width=True):
    st.session_state.clear() # Clear old results
    st.session_state.run_mode = 'batch'
    
    # Check for CSV
    if not os.path.exists(csv_file_path):
        st.sidebar.error(f"File not found: {csv_file_path}.")
        st.stop()
    try:
        ticker_list_df = pd.read_csv(csv_file_path)
        NIFTY_500_TICKERS = ticker_list_df['Symbol'].tolist()
    except Exception as e:
        st.error(f"Error reading CSV file: {e}")
        st.stop()

    with st.spinner(f"Running batch backtest on {num_stocks_to_test} random stocks..."):
        tickers = random.sample(NIFTY_500_TICKERS, num_stocks_to_test)
        all_results = []
        progress_bar = st.progress(0, text="Batch test started...")
        
        # --- STAGE 1: Run metrics-only batch test ---
        for i, ticker in enumerate(tickers):
            progress_bar.progress((i+1)/len(tickers), text=f"Running batch test... ({i+1}/{num_stocks_to_test})")
            
            _, results = run_full_test_for_ticker(
                ticker, data_fetch_start_date, selected_end_date, selected_start_date
            )
            if results is None: continue # Skip if error
            
            all_results.append({
                'ticker': ticker,
                'total_return': results['total_return'],
                'max_drawdown': results['max_drawdown'],
                'win_rate': results['win_rate'],
                'total_trades': results['total_trades']
            })

        progress_bar.empty() 
        if not all_results:
            st.error("Batch test completed, but no trades were executed for any stock.")
            st.session_state.run_mode = 'none'
            st.stop()
        
        results_df = pd.DataFrame(all_results)
        st.session_state.batch_results_df = results_df
        st.success("Batch test complete. Analyzing top/worst performers...")

    # --- STAGE 2: Re-run detailed analysis for Top/Worst 5 ---
    with st.spinner("Analyzing top/worst 5 performers..."):
        sorted_df = results_df.sort_values(by='total_return', ascending=False)
        top_5_tickers = sorted_df.head(5)['ticker'].tolist()
        worst_5_tickers = sorted_df.tail(5)['ticker'].tolist()
        
        top_performers_data = []
        worst_performers_data = []

        for ticker in top_5_tickers:
            test_df, results = run_full_test_for_ticker(
                ticker, data_fetch_start_date, selected_end_date, selected_start_date
            )
            if test_df is not None:
                top_performers_data.append((ticker, test_df, results))
        
        for ticker in worst_5_tickers:
            test_df, results = run_full_test_for_ticker(
                ticker, data_fetch_start_date, selected_end_date, selected_start_date
            )
            if test_df is not None:
                worst_performers_data.append((ticker, test_df, results))
                
        st.session_state.top_performers_data = top_performers_data
        st.session_state.worst_performers_data = worst_performers_data
        st.success("Full analysis complete.")


# ---
# MAIN PAGE - DYNAMIC CONTENT
# ---

# Get current run mode
run_mode = st.session_state.get('run_mode', 'none')

# 1. Main Metrics Container (always visible at top, below title)
main_metrics_container = st.container()

# 2. Tabbed Interface
tab_titles = ["Strategy Rationale"]
if run_mode == 'single':
    tab_titles.append("Single Stock Analysis")
elif run_mode == 'batch':
    tab_titles.extend(["Batch Test Analysis", "Top 5 Performers", "Worst 5 Performers"])

tabs = st.tabs(tab_titles)

# --- Tab 1: Strategy Rationale (Always Shown) ---
with tabs[0]:
    with st.expander("💡 Strategy Rationale: The 1/45 SMA (4:1 P/L) Hybrid Model", expanded=True):
        st.markdown(f"""
        This backtester is locked to a specific hybrid strategy designed to capture quick, high-momentum trades and exit them with a clear, predefined risk-to-reward ratio.
        
        ### Strategy Components:
        * **Entry Signal:** `1-Day MA` (Price) crossing *above* the `45-Day SMA`.
            * **Why?** This is one of the fastest possible trend-confirmation signals. We act the *moment* the current price breaks above its 45-day simple average.
        
        * **Exit Strategy:** `20% Take Profit` / `5% Stop Loss` (a 4:1 Ratio).
            * **Why?** The exit is based on price targets, not a reverse crossover. This is crucial.
            * **Faster Exits:** A price-target exit locks in our `20%` profit (or cuts our `5%` loss) at the close of the day it's hit, rather than waiting for MAs to slowly cross back.
            * **Asymmetric Risk:** The 4:1 ratio means we only need to win **one out of every five trades** (a 20% win rate) to break even. This allows us to be wrong more often, as long as our wins are significantly larger than our losses.

        ### Future Benefit:
        This model is built to find and exploit strong, medium-term trends, aiming for significant wins while strictly managing downside risk.
        """)

# --- Handle Drawing Logic Based on Run Mode ---

if run_mode == 'none':
    main_metrics_container.info("Select a test from the sidebar and click 'Run'.")

elif run_mode == 'single':
    # --- Populate Main Metrics Container ---
    ticker = st.session_state.single_ticker
    results = st.session_state.single_results
    with main_metrics_container:
        st.subheader(f"Single Stock Report: {ticker}")
        utils.display_metrics_table(
            results, STRATEGY_NAME, ticker, backtest_period_str, ENTRY_CRITERIA_STR, EXIT_CRITERIA_STR
        )
        st.subheader("Trade Log")
        st.dataframe(results['trades'], use_container_width=True)

    # --- Populate "Single Stock Analysis" Tab ---
    with tabs[1]:
        test_df = st.session_state.single_test_df
        utils.display_single_stock_analysis(test_df, results['trades'], STRATEGY_NAME)

elif run_mode == 'batch':
    results_df = st.session_state.batch_results_df
    
    # --- Populate Main Metrics Container ---
    with main_metrics_container:
        st.subheader(f"Batch Test Report: {num_stocks_to_test} Stocks")
        utils.display_batch_metrics_summary(
            results_df, STRATEGY_NAME, backtest_period_str, ENTRY_CRITERIA_STR, EXIT_CRITERIA_STR, num_stocks_to_test
        )

    # --- Populate "Batch Test Analysis" Tab ---
    with tabs[1]:
        st.subheader("Aggregated Performance Charts")
        utils.display_batch_analysis_charts(results_df)

    # --- Populate "Top 5 Performers" Tab ---
    with tabs[2]:
        st.subheader("Detailed Analysis: Top 5 Performers")
        st.caption("This shows the full 4-chart analysis for each of the top 5 performing stocks from the batch test.")
        top_data = st.session_state.top_performers_data
        if not top_data:
            st.warning("No data for top performers.")
        else:
            for ticker, test_df, results in top_data:
                exp_title = f"📈 {ticker} (Total Return: {results['total_return']:.2f}%)"
                with st.expander(exp_title, expanded=False):
                    utils.display_single_stock_analysis(test_df, results['trades'], STRATEGY_NAME)

    # --- Populate "Worst 5 Performers" Tab ---
    with tabs[3]:
        st.subheader("Detailed Analysis: Worst 5 Performers")
        st.caption("This shows the full 4-chart analysis for each of the 5 worst performing stocks from the batch test.")
        worst_data = st.session_state.worst_performers_data
        if not worst_data:
            st.warning("No data for worst performers.")
        else:
            # Sort by return ascending (worst first)
            worst_data.sort(key=lambda x: x[2]['total_return'])
            for ticker, test_df, results in worst_data:
                exp_title = f"📉 {ticker} (Total Return: {results['total_return']:.2f}%)"
                with st.expander(exp_title, expanded=False):
                    utils.display_single_stock_analysis(test_df, results['trades'], STRATEGY_NAME)