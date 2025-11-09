import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ---
# 1. METRICS TABLE (For Single Stock Report)
# ---

def display_metrics_table(metrics: dict, strategy_name: str, ticker: str, period_str: str, entry_str: str, exit_str: str):
    """
    Displays the final results table for a SINGLE stock,
    formatted to the user's specification.
    """
    
    report_data = {
        "Metric": [
            "Strategy name / MA types and periods",
            "Stocks tested",
            "Backtest period",
            "Entry criteria",
            "Exit criteria",
            "Return",
            "Max drawdown",
            "Win rate",
            "Number of trades"
        ],
        "Value": [
            strategy_name,
            ticker,
            period_str,
            entry_str,
            exit_str,
            f"{metrics['total_return']:.2f}%",
            f"{metrics['max_drawdown']:.2f}%",
            f"{metrics['win_rate']:.2f}%",
            metrics['total_trades']
        ]
    }
    
    report_df = pd.DataFrame(report_data)
    st.dataframe(report_df.set_index("Metric"), use_container_width=True)

# ---
# 2. BATCH REPORTING (Refactored into smaller functions)
# ---

def display_batch_metrics_summary(
    results_df: pd.DataFrame, 
    strategy_name: str,
    backtest_period: str,
    entry_criteria: str,
    exit_criteria: str,
    num_stocks_tested: int
):
    """
    Displays the top-level summary for the batch report,
    including new metric cards and the main data table
    formatted to the user's specification.
    """
    if results_df.empty:
        st.warning("No trades were made across all stocks.")
        return

    # 1. Calculate Average Metrics
    avg_return = results_df['total_return'].mean()
    avg_max_drawdown = results_df['max_drawdown'].mean()
    avg_win_rate = results_df['win_rate'].mean()
    total_trades = results_df['total_trades'].sum()

    # --- NEW: Metric Cards ---
    st.subheader("Batch Performance At-a-Glance")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Avg. Return", f"{avg_return:.2f}%")
    col2.metric("Avg. Win Rate", f"{avg_win_rate:.2f}%")
    col3.metric("Avg. Max Drawdown", f"{avg_max_drawdown:.2f}%")
    col4.metric("Total Trades", f"{total_trades:,.0f}")
    
    st.markdown("---")

    # 2. Create the Main Report Table
    st.subheader("Backtest Strategy Results")
    report_data = {
        "Metric": [
            "Strategy name / MA types and periods",
            "Stocks tested (NSE 500 list subset)",
            "Backtest period",
            "Entry criteria",
            "Exit criteria",
            "Avg. Return",
            "Avg. Max drawdown",
            "Avg. Win rate",
            "Total number of trades"
        ],
        "Value": [
            strategy_name,
            f"{num_stocks_tested} random stocks from NSE 500",
            backtest_period,
            entry_criteria,
            exit_criteria,
            f"{avg_return:.2f}%",
            f"{avg_max_drawdown:.2f}%",
            f"{avg_win_rate:.2f}%",
            f"{total_trades:,.0f}"
        ]
    }
    report_df = pd.DataFrame(report_data)
    st.dataframe(report_df.set_index("Metric"), use_container_width=True)

    # 3. Full Results (in Expander)
    with st.expander("Show Full Results for All Stocks"):
        st.dataframe(results_df.sort_values(by='total_return', ascending=False).set_index('ticker'), use_container_width=True)


def _plot_distributions(results_df: pd.DataFrame):
    """
    Helper function to plot the distribution histograms.
    """
    st.subheader("Strategy Performance Distribution")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig_return = px.histogram(
            results_df, x='total_return', title='Distribution of Returns (%)',
            labels={'total_return': 'Total Return (%)'}, template="plotly_dark"
        )
        fig_return.update_layout(yaxis_title="Number of Stocks")
        # *** PROACTIVE FIX: Added key ***
        st.plotly_chart(fig_return, use_container_width=True, key="dist_return")
    
    with col2:
        fig_winrate = px.histogram(
            results_df, x='win_rate', title='Distribution of Win Rates (%)',
            labels={'win_rate': 'Win Rate (%)'}, color_discrete_sequence=['#2ca02c'], template="plotly_dark"
        )
        fig_winrate.update_layout(yaxis_title="Number of Stocks")
        # *** PROACTIVE FIX: Added key ***
        st.plotly_chart(fig_winrate, use_container_width=True, key="dist_winrate")

    with col3:
        fig_drawdown = px.histogram(
            results_df, x='max_drawdown', title='Distribution of Max Drawdown (%)',
            labels={'max_drawdown': 'Max Drawdown (%)'}, color_discrete_sequence=['#d62728'], template="plotly_dark"
        )
        fig_drawdown.update_layout(yaxis_title="Number of Stocks")
        # *** PROACTIVE FIX: Added key ***
        st.plotly_chart(fig_drawdown, use_container_width=True, key="dist_drawdown")

def _plot_top_bottom_performers(results_df: pd.DataFrame):
    """
    Helper function to plot the top/bottom 10 bar charts.
    """
    st.subheader("Performance by Stock")
    
    sorted_df = results_df.sort_values(by='total_return', ascending=False)
    top_n = min(10, len(sorted_df))
    if top_n == 0:
        st.warning("No data to display for top/bottom performers.")
        return

    top_10 = sorted_df.head(top_n)
    bottom_10 = sorted_df.tail(top_n)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_top = px.bar(
            top_10.sort_values(by='total_return', ascending=True),
            x='total_return', y='ticker', orientation='h', title=f'Top {top_n} Best Performers',
            labels={'total_return': 'Total Return (%)', 'ticker': 'Stock'}, text='total_return',
            color_discrete_sequence=['#2ca02c']
        )
        fig_top.update_traces(texttemplate='%{x:.2f}%', textposition='outside')
        fig_top.update_layout(template="plotly_dark")
        # *** PROACTIVE FIX: Added key ***
        st.plotly_chart(fig_top, use_container_width=True, key="bar_top")
        
    with col2:
        fig_bottom = px.bar(
            bottom_10.sort_values(by='total_return', ascending=False),
            x='total_return', y='ticker', orientation='h', title=f'Top {top_n} Worst Performers',
            labels={'total_return': 'Total Return (%)', 'ticker': 'Stock'}, text='total_return',
            color_discrete_sequence=['#d62728']
        )
        fig_bottom.update_traces(texttemplate='%{x:.2f}%', textposition='outside')
        fig_bottom.update_layout(template="plotly_dark")
        # *** PROACTIVE FIX: Added key ***
        st.plotly_chart(fig_bottom, use_container_width=True, key="bar_bottom")

def _plot_correlation(results_df: pd.DataFrame):
    """
    Helper function to plot the correlation scatter plot.
    """
    st.subheader("Performance Correlation")
    fig_scatter = px.scatter(
        results_df, x='win_rate', y='total_return', title='Win Rate vs. Total Return',
        labels={'win_rate': 'Win Rate (%)', 'total_return': 'Total Return (%)'},
        hover_name='ticker', template="plotly_dark", trendline="ols",
        color_discrete_sequence=['#1f77b4']
    )
    # *** PROACTIVE FIX: Added key ***
    st.plotly_chart(fig_scatter, use_container_width=True, key="scatter_corr")

def display_batch_analysis_charts(results_df: pd.DataFrame):
    """
    NEW: Main function to call all the individual chart plots
    for the "Batch Test Analysis" tab.
    """
    if results_df.empty:
        st.warning("No batch results to display.")
        return
        
    _plot_distributions(results_df)
    st.markdown("---")
    _plot_top_bottom_performers(results_df)
    st.markdown("---")
    _plot_correlation(results_df)


# ---
# 3. SINGLE-STOCK ANALYSIS (Unchanged, now re-used)
# ---

def _plot_trade_markers(fig: go.Figure, trades_df: pd.DataFrame):
    """Helper function to add common trade markers to any chart."""
    if not trades_df.empty:
        # Note: Your backtester.py sets the index to 'Entry Date'
        # So we use trades_df.index for entry
        fig.add_trace(go.Scatter(
            x=trades_df.index, y=trades_df['Entry Price'], mode='markers', name='Buy Signal',
            marker=dict(color='green', symbol='triangle-up', size=10, line=dict(width=1, color='Black'))
        ))
        fig.add_trace(go.Scatter(
            x=trades_df['Exit Date'], y=trades_df['Exit Price'], mode='markers', name='Sell Signal',
            marker=dict(color='red', symbol='triangle-down', size=10, line=dict(width=1, color='Black'))
        ))
    return fig

def _plot_ma_lines(fig: go.Figure, signals_df: pd.DataFrame):
    """Helper function to add common MA lines to any chart."""
    fig.add_trace(go.Scatter(
        x=signals_df.index, y=signals_df['fast_ma'], mode='lines', name='Fast MA (Price)',
        line=dict(color='cyan', width=1)
    ))
    fig.add_trace(go.Scatter(
        x=signals_df.index, y=signals_df['slow_ma'], mode='lines', name='Slow MA',
        line=dict(color='orange', width=2)
    ))
    return fig

def _plot_candlestick_chart(signals_df: pd.DataFrame, trades_df: pd.DataFrame, strategy_name: str) -> go.Figure:
    fig = go.Figure(data=[go.Candlestick(
        x=signals_df.index, open=signals_df['Open'], high=signals_df['High'],
        low=signals_df['Low'], close=signals_df['Close'], name='Price'
    )])
    fig = _plot_ma_lines(fig, signals_df)
    fig = _plot_trade_markers(fig, trades_df)
    fig.update_layout(
        title=f"Candlestick Chart: {strategy_name}", xaxis_title="Date", yaxis_title="Stock Price",
        legend_title="Legend", xaxis_rangeslider_visible=False, template="plotly_dark"
    )
    return fig

def _plot_line_chart(signals_df: pd.DataFrame, trades_df: pd.DataFrame, strategy_name: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=signals_df.index, y=signals_df['Close'], mode='lines', name='Close Price',
        line=dict(color='lightgray', width=1.5)
    ))
    fig = _plot_ma_lines(fig, signals_df)
    fig = _plot_trade_markers(fig, trades_df)
    fig.update_layout(
        title=f"Line Chart (Close): {strategy_name}", xaxis_title="Date", yaxis_title="Stock Price",
        legend_title="Legend", xaxis_rangeslider_visible=False, template="plotly_dark"
    )
    return fig

def _plot_heikin_ashi_chart(signals_df: pd.DataFrame, trades_df: pd.DataFrame, strategy_name: str) -> go.Figure:
    ha_df = signals_df.copy()
    ha_df['HA_Close'] = (ha_df['Open'] + ha_df['High'] + ha_df['Low'] + ha_df['Close']) / 4
    ha_df['HA_Open'] = 0.0
    ha_df.iloc[0, ha_df.columns.get_loc('HA_Open')] = (ha_df.iloc[0]['Open'] + ha_df.iloc[0]['Close']) / 2
    for i in range(1, len(ha_df)):
        ha_df.iloc[i, ha_df.columns.get_loc('HA_Open')] = (ha_df.iloc[i-1]['HA_Open'] + ha_df.iloc[i-1]['HA_Close']) / 2
    ha_df['HA_High'] = ha_df[['High', 'HA_Open', 'HA_Close']].max(axis=1)
    ha_df['HA_Low'] = ha_df[['Low', 'HA_Open', 'HA_Close']].min(axis=1)

    fig = go.Figure(data=[go.Candlestick(
        x=ha_df.index, open=ha_df['HA_Open'], high=ha_df['HA_High'],
        low=ha_df['HA_Low'], close=ha_df['HA_Close'], name='Heikin-Ashi',
        increasing_line_color='green', decreasing_line_color='red'
    )])
    fig = _plot_ma_lines(fig, signals_df)
    fig = _plot_trade_markers(fig, trades_df)
    fig.update_layout(
        title=f"Heikin-Ashi Chart: {strategy_name}", xaxis_title="Date", yaxis_title="Stock Price",
        legend_title="Legend", xaxis_rangeslider_visible=False, template="plotly_dark"
    )
    return fig

def _plot_pnl_analysis(trades_df: pd.DataFrame) -> go.Figure:
    if trades_df.empty:
        return go.Figure().update_layout(
            title="P&L Analysis", template="plotly_dark",
            annotations=[dict(text="No trades to analyze.", showarrow=False)]
        )
        
    # Check for required columns for P&L plot
    if 'Cumulative Return' not in trades_df.columns or 'P&L %' not in trades_df.columns:
        st.warning("P&L analysis requires 'Cumulative Return' and 'P&L %' columns from backtester.")
        return go.Figure().update_layout(title="P&L Analysis (Data Missing)", template="plotly_dark")


    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=False, vertical_spacing=0.1,
        subplot_titles=("Cumulative Compounded Return", "Distribution of Trade P&L (%)")
    )
    fig.add_trace(
        go.Scatter(
            x=trades_df['Exit Date'], y=trades_df['Cumulative Return'],
            mode='lines+markers', name='Equity Curve', line=dict(color='cyan', width=2)
        ), row=1, col=1
    )
    fig.add_trace(
        go.Histogram(
            x=trades_df['P&L %'], name='P&L %', marker_color='#1f77b4'
        ), row=2, col=1
    )
    fig.update_layout(
        title_text="Strategy P&L Analysis", template="plotly_dark", showlegend=False
    )
    fig.update_yaxes(title_text="Cumulative Return (Factor)", row=1, col=1)
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_yaxes(title_text="Number of Trades", row=2, col=1)
    fig.update_xaxes(title_text="P&L per Trade (%)", row=2, col=1)
    return fig


def display_single_stock_analysis(context: str, ticker: str, signals_df: pd.DataFrame, trades_df: pd.DataFrame, strategy_name: str):
    """
    Main function to create and display the tabbed chart interface.
    (This is the function that is re-used for all single-stock analysis)
    
    *** FIX 1: 'context' and 'ticker' are added as new arguments ***
    """
    
    tab1, tab2, tab3, tab4 = st.tabs(["Candlestick", "Heikin-Ashi", "Line (Close)", "P&L Analysis"])
    
    with tab1:
        fig_candle = _plot_candlestick_chart(signals_df, trades_df, strategy_name)
        # *** FIX 2: Added unique key using context and ticker ***
        st.plotly_chart(fig_candle, use_container_width=True, key=f"{context}_candle_{ticker}")

    with tab2:
        fig_ha = _plot_heikin_ashi_chart(signals_df, trades_df, strategy_name)
        # *** FIX 3: Added unique key using context and ticker ***
        st.plotly_chart(fig_ha, use_container_width=True, key=f"{context}_ha_{ticker}")
        st.caption("Heikin-Ashi charts help visualize the trend's momentum and direction by averaging price data.")

    with tab3:
        fig_line = _plot_line_chart(signals_df, trades_df, strategy_name)
        # *** FIX 4: Added unique key using context and ticker ***
        st.plotly_chart(fig_line, use_container_width=True, key=f"{context}_line_{ticker}")

    with tab4:
        fig_pnl = _plot_pnl_analysis(trades_df)
        # *** FIX 5: Added unique key using context and ticker ***
        st.plotly_chart(fig_pnl, use_container_width=True, key=f"{context}_pnl_{ticker}")
        st.caption("The Equity Curve shows the compounded growth of your portfolio over time. The Histogram shows the frequency of winning vs. losing trades.")