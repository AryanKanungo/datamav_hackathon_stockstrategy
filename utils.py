# utils.py
import plotly.graph_objects as go
import pandas as pd

def plot_candlestick(df: pd.DataFrame, title: str = "Candlestick"):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='OHLC'
    )])
    fig.update_layout(title=title, xaxis_rangeslider_visible=False)
    return fig

def plot_heikin_ashi(df: pd.DataFrame, ha_df: pd.DataFrame, title: str = "Heikin-Ashi"):
    fig = go.Figure(data=[go.Candlestick(
        x=ha_df.index,
        open=ha_df['HA_Open'],
        high=ha_df['HA_High'],
        low=ha_df['HA_Low'],
        close=ha_df['HA_Close'],
        name='Heikin-Ashi'
    )])
    fig.update_layout(title=title, xaxis_rangeslider_visible=False)
    return fig

def plot_line(df: pd.DataFrame, column='Close', title: str = "Line"):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df[column], mode='lines', name=column))
    fig.update_layout(title=title)
    return fig

def plot_ohlc_bar(df: pd.DataFrame, title: str = "OHLC Bars"):
    fig = go.Figure(data=[go.Ohlc(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    )])
    fig.update_layout(title=title, xaxis_rangeslider_visible=False)
    return fig

def plot_renko(bricks_df, title: str = "Renko"):
    # bricks_df: DataFrame with 'brick_price' and 'direction' and implicitly index order
    fig = go.Figure()
    if not bricks_df.empty:
        xs = list(range(len(bricks_df)))
        ys = bricks_df['brick_price']
        colors = ['green' if d == 1 else 'red' for d in bricks_df['direction']]
        fig.add_trace(go.Bar(x=xs, y=ys, marker_color=colors, name='Renko bricks'))
    fig.update_layout(title=title, xaxis={'visible': False})
    return fig
