# app.py
import streamlit as st
import pandas as pd
from datetime import date
from data_fetcher import fetch_stock_data
from strategy import generate_signals, heikin_ashi, renko_bricks
from backtester import Backtester
from utils import plot_candlestick, plot_heikin_ashi, plot_line, plot_renko, plot_ohlc_bar
from nse500_list import nse_500
import io

st.set_page_config(layout="wide", page_title="MA Crossover Backtester")

# Header
st.title("📈 MA Crossover Backtester — NSE (EOD)")
st.markdown("""
**Strategy:** Moving Average Crossover (EMA/SMA/WMA)  
**Data:** Last 3 months EOD close prices (3:30pm official close) — NSE stocks  
Use the controls in the sidebar to choose MA type, fast/slow windows, and exit rules.
""")

# Sidebar: Strategy controls
with st.sidebar:
    st.header("Strategy Parameters")
    ma_type = st.selectbox("MA Type", ["EMA", "SMA", "WMA"], index=0)
    fast = st.number_input("Fast MA period (days)", min_value=2, max_value=50, value=10)
    slow = st.number_input("Slow MA period (days)", min_value=5, max_value=200, value=50)
    if slow <= fast:
        st.warning("Slow period should be greater than fast period for meaningful crossover.")
    st.markdown("---")
    st.header("Exit Rules")
    exit_choice = st.selectbox("Exit Rule", ["profit_stop", "opposite", "trailing", "days"])
    profit_target = st.number_input("Profit target (%)", min_value=0.5, max_value=50.0, value=10.0) / 100.0
    stop_loss = st.number_input("Stop loss (%)", min_value=0.5, max_value=50.0, value=4.0) / 100.0
    trailing_pct = None
    max_days = None
    if exit_choice == "trailing":
        trailing_pct = st.number_input("Trailing stop (%)", min_value=0.5, max_value=50.0, value=5.0) / 100.0
    if exit_choice == "days":
        max_days = st.number_input("Hold days", min_value=1, max_value=90, value=15)

    st.markdown("---")
    st.header("Backtest Options")
    mode = st.radio("Run mode", ["Single stock", "Bulk NSE500 (sample list)"])
    symbol = None
    if mode == "Single stock":
        symbol = st.text_input("Stock symbol (e.g., INFY, TCS, RELIANCE)", value="INFY").upper()
    run_btn = st.button("Run Backtest")

# Execution
if run_btn:
    stocks_to_run = [symbol] if mode == "Single stock" else nse_500
    summary_rows = []
    detailed_results = {}

    progress = st.progress(0)
    total = len(stocks_to_run)
    processed = 0

    for s in stocks_to_run:
        processed += 1
        try:
            st.info(f"Fetching {s} ({processed}/{total})...")
            df = fetch_stock_data(s, months=3)
            if df.empty:
                st.warning(f"No data for {s}. Skipping.")
                progress.progress(processed/total)
                continue

            st.info(f"Generating signals for {s}...")
            df_signals = generate_signals(df, ma_type, fast, slow)

            bt = Backtester(df_signals, profit_target=profit_target, stop_loss=stop_loss,
                            exit_rule=exit_choice, trailing_stop_pct=trailing_pct, max_hold_days=max_days)

            stats = bt.run()

            summary_rows.append({
                "Stock": s,
                "Return (%)": stats["total_return"],
                "Max Drawdown (%)": stats["drawdown"],
                "Win Rate (%)": stats["win_rate"],
                "Trades": stats["num_trades"]
            })
            detailed_results[s] = {"df": df_signals, "stats": stats}

            progress.progress(processed/total)
        except Exception as e:
            st.error(f"Error for {s}: {e}")
            progress.progress(processed/total)
            continue

    # Summary table
    summary_df = pd.DataFrame(summary_rows).sort_values(by="Return (%)", ascending=False)
    st.subheader("Backtest Summary")
    st.write(f"Strategy: {fast}/{slow} {ma_type} crossover | Exit: {exit_choice} | Profit target: {profit_target*100:.2f}% | Stop loss: {stop_loss*100:.2f}%")
    st.dataframe(summary_df)

    # Download CSV
    csv = summary_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Summary CSV", csv, file_name=f"backtest_summary_{date.today()}.csv", mime='text/csv')

    # Show top N stocks details
    top_n = st.number_input("Show top N stocks detail", min_value=1, max_value=20, value=3)
    top_stocks = summary_df.head(top_n)['Stock'].tolist()

    for stock in top_stocks:
        if stock not in detailed_results:
            continue
        st.markdown(f"---\n## {stock} — Detailed View")
        info_col, chart_col = st.columns([1, 2])

        with info_col:
            st.write("**Performance**")
            stats = detailed_results[stock]['stats']
            st.metric("Total Return (%)", stats['total_return'])
            st.metric("Max Drawdown (%)", stats['drawdown'])
            st.metric("Win Rate (%)", f"{stats['win_rate']}%")
            st.metric("Trades", stats['num_trades'])

            st.write("**Trade Log (latest)**")
            trades_df = stats['trades']
            if not trades_df.empty:
                st.dataframe(trades_df.tail(10))
                csv_buf = trades_df.to_csv(index=False).encode('utf-8')
                st.download_button(f"Download {stock} trades CSV", csv_buf, file_name=f"{stock}_trades_{date.today()}.csv")
            else:
                st.write("No trades were generated.")

        with chart_col:
            df_stock = detailed_results[stock]['df']
            fig1 = plot_candlestick(df_stock, title=f"{stock} Candlestick")
            st.plotly_chart(fig1, use_container_width=True)

            fig2 = plot_ohlc_bar(df_stock, title=f"{stock} OHLC Bars")
            st.plotly_chart(fig2, use_container_width=True)

            fig3 = plot_line(df_stock, column='Close', title=f"{stock} Close Price")
            st.plotly_chart(fig3, use_container_width=True)

            ha = heikin_ashi(df_stock)
            fig4 = plot_heikin_ashi(df_stock, ha, title=f"{stock} Heikin-Ashi")
            st.plotly_chart(fig4, use_container_width=True)

            bricks = renko_bricks(df_stock)
            fig5 = plot_renko(bricks, title=f"{stock} Renko (approx)")
            st.plotly_chart(fig5, use_container_width=True)

    st.success("Backtest completed.")
