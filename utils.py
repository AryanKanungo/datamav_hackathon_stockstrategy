import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def display_metrics_table(metrics: dict, strategy_name: str, ticker: str, period_str: str, entry_str: str, exit_str: str):
    """
    Displays the final hackathon-specific results table for a SINGLE stock.
    """
    
    report_data = {
        "Metric": [
            "Strategy Name",
            "Stocks Tested",
            "Backtest Period",
            "Entry Criteria",
            "Exit Criteria",
            "Return (%)",
            "Max Drawdown (%)",
            "Win Rate (%)",
            "Number of Trades"
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

def plot_backtest_graph(signals_df: pd.DataFrame, trades_df: pd.DataFrame, strategy_name: str) -> go.Figure:
    """
    Creates the Plotly graph with price, MAs, and trade markers.
    """
    
    # Create a figure with candlestick chart
    fig = go.Figure(data=[go.Candlestick(
        x=signals_df.index,
        open=signals_df['Open'],
        high=signals_df['High'],
        low=signals_df['Low'],
        close=signals_df['Close'],
        name='Price'
    )])
    
    # Add Moving Averages
    fig.add_trace(go.Scatter(
        x=signals_df.index,
        y=signals_df['fast_ma'],
        mode='lines',
        name='Fast MA',
        line=dict(color='cyan', width=1)
    ))
    
    fig.add_trace(go.Scatter(
        x=signals_df.index,
        y=signals_df['slow_ma'],
        mode='lines',
        name='Slow MA',
        line=dict(color='orange', width=1)
    ))
    
    # Add Trade Markers (if any trades)
    if not trades_df.empty:
        # Re-index trades_df if it's not already
        if 'Entry Date' in trades_df.columns:
             trades_df = trades_df.set_index('Entry Date')
             
        # Buy Markers
        fig.add_trace(go.Scatter(
            x=trades_df.index,
            y=trades_df['Entry Price'],
            mode='markers',
            name='Buy Signal',
            marker=dict(color='green', symbol='triangle-up', size=10)
        ))
        
        # Sell Markers
        fig.add_trace(go.Scatter(
            x=trades_df['Exit Date'],
            y=trades_df['Exit Price'],
            mode='markers',
            name='Sell Signal',
            marker=dict(color='red', symbol='triangle-down', size=10)
        ))

    # Update layout
    fig.update_layout(
        title=f"Backtest Results for {strategy_name}",
        xaxis_title="Date",
        yaxis_title="Stock Price",
        legend_title="Legend",
        xaxis_rangeslider_visible=False,
        template="plotly_dark"
    )
    
    return fig

# --- THIS IS THE NEW FUNCTION YOU NEED ---
def display_batch_results(results_df: pd.DataFrame, strategy_name: str):
    """
    Displays the aggregated results from a batch backtest.
    """
    st.subheader(f"Batch Test Results: {strategy_name}")
    
    if results_df.empty:
        st.warning("No trades were made across all stocks.")
        return

    # 1. Top-Level Metrics
    num_stocks_tested = len(results_df)
    total_trades = results_df['total_trades'].sum()
    
    # Strategy Win Rate = % of stocks that were profitable
    profitable_stocks = results_df[results_df['total_return'] > 0]
    strategy_win_rate = (len(profitable_stocks) / num_stocks_tested) * 100 if num_stocks_tested > 0 else 0
    
    # Average Return (mean of all stock returns)
    avg_return = results_df['total_return'].mean()
    
    # Average Win Rate (mean of all individual trade win rates)
    avg_trade_win_rate = results_df['win_rate'].mean()

    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Stocks Tested", f"{num_stocks_tested}")
    col2.metric("Total Trades", f"{total_trades:,.0f}")
    col3.metric("Strategy Win Rate", f"{strategy_win_rate:.2f}%",
               help="Percentage of stocks that had a positive return.")
    col4.metric("Avg. Stock Return", f"{avg_return:.2f}%",
               help="The average P&L % across all stocks tested.")
    
    st.markdown("---")

    # 2. Top/Bottom Performers
    st.subheader("Performance by Stock")
    
    # Sort by total return, descending
    sorted_df = results_df.sort_values(by='total_return', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Top 10 Best Performers")
        st.dataframe(sorted_df[['ticker', 'total_return', 'win_rate', 'total_trades']].head(10),
                       use_container_width=True)
    
    with col2:
        st.markdown("#### Top 10 Worst Performers")
        st.dataframe(sorted_df[['ticker', 'total_return', 'win_rate', 'total_trades']].tail(10).sort_values(by='total_return', ascending=True),
                       use_container_width=True)

    # 3. Full Results
    with st.expander("Show Full Results for All Stocks"):
        st.dataframe(sorted_df, use_container_width=True)