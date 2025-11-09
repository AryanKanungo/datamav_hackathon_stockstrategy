import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def display_metrics_table(metrics: dict, strategy_name: str, ticker: str, period_str: str, entry_str: str, exit_str: str):
    """
    Displays the final hackathon-specific results table.
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