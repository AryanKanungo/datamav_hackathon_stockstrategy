import pandas as pd
import numpy as np

def run_backtest(signals_df: pd.DataFrame, exit_strategy: str, take_profit: float, stop_loss: float, trade_timeout_days: int) -> dict:
    """
    Runs the backtest simulation based on EOD (End of Day) closing prices.
    
    Args:
        signals_df (pd.DataFrame): The DataFrame with signals from strategy.py.
        exit_strategy (str): "Take Profit / Stop Loss" or "Reverse Crossover".
        take_profit (float): The take profit percentage (e.g., 0.10 for 10%).
        stop_loss (float): The stop loss percentage (e.g., 0.05 for 5%).
        trade_timeout_days (int): Max number of days to hold a trade.
        
    Returns:
        dict: A dictionary containing the backtest results.
    """
    trades = []
    in_position = False
    entry_price = 0
    entry_date = None
    
    # Loop through the signals dataframe
    for index, row in signals_df.iterrows():
        
        # --- Check for Exit Conditions FIRST (if in position) ---
        if in_position:
            
            # --- Rule-Compliant EOD (Closing Price) Logic ---
            take_profit_price = entry_price * (1 + take_profit)
            stop_loss_price = entry_price * (1 - stop_loss)
            
            if exit_strategy == "Take Profit / Stop Loss":
                # Check 1: Take-Profit (using Closing price)
                if row['Close'] >= take_profit_price:
                    exit_price = row['Close'] # Exit at this day's close
                    pnl_pct = (exit_price - entry_price) / entry_price
                    trades.append({
                        "Entry Date": entry_date,
                        "Entry Price": entry_price,
                        "Exit Date": index,
                        "Exit Price": exit_price,
                        "P&L %": pnl_pct,
                        "Exit Type": "Take-Profit"
                    })
                    in_position = False
                
                # Check 2: Stop-Loss (using Closing price)
                elif row['Close'] <= stop_loss_price:
                    exit_price = row['Close'] # Exit at this day's close
                    pnl_pct = (exit_price - entry_price) / entry_price
                    trades.append({
                        "Entry Date": entry_date,
                        "Entry Price": entry_price,
                        "Exit Date": index,
                        "Exit Price": exit_price,
                        "P&L %": pnl_pct,
                        "Exit Type": "Stop-Loss"
                    })
                    in_position = False
                
                # Check 3: Trade Timeout (new feature from rules)
                elif (index - entry_date).days >= trade_timeout_days:
                    exit_price = row['Close'] # Exit at this day's close
                    pnl_pct = (exit_price - entry_price) / entry_price
                    trades.append({
                        "Entry Date": entry_date,
                        "Entry Price": entry_price,
                        "Exit Date": index,
                        "Exit Price": exit_price,
                        "P&L %": pnl_pct,
                        "Exit Type": "Timeout"
                    })
                    in_position = False
                
                # Check 4: Reverse Crossover (as a fallback)
                elif row['position'] == -1.0:
                    exit_price = row['Close'] # Exit at close on crossover
                    pnl_pct = (exit_price - entry_price) / entry_price
                    trades.append({
                        "Entry Date": entry_date,
                        "Entry Price": entry_price,
                        "Exit Date": index,
                        "Exit Price": exit_price,
                        "P&L %": pnl_pct,
                        "Exit Type": "Reverse Crossover"
                    })
                    in_position = False
            
            elif exit_strategy == "Reverse Crossover":
                # Check for bearish crossover (sell signal)
                if row['position'] == -1.0:
                    exit_price = row['Close'] # Exit at close on crossover
                    pnl_pct = (exit_price - entry_price) / entry_price
                    trades.append({
                        "Entry Date": entry_date,
                        "Entry Price": entry_price,
                        "Exit Date": index,
                        "Exit Price": exit_price,
                        "P&L %": pnl_pct,
                        "Exit Type": "Reverse Crossover"
                    })
                    in_position = False

        # --- Check for Entry Conditions (if NOT in position) ---
        if not in_position:
            # Check for bullish crossover (buy signal)
            if row['position'] == 1.0:
                in_position = True
                entry_price = row['Close'] # Enter at the close of the signal day
                entry_date = index

    # --- End of Backtest: Close any open position ---
    if in_position:
        last_price = signals_df.iloc[-1]['Close']
        pnl_pct = (last_price - entry_price) / entry_price
        trades.append({
            "Entry Date": entry_date,
            "Entry Price": entry_price,
            "Exit Date": signals_df.index[-1],
            "Exit Price": last_price,
            "P&L %": pnl_pct,
            "Exit Type": "End of Backtest"
        })

    # --- Calculate Metrics ---
    if not trades:
        # No trades were made
        return {
            'trades': pd.DataFrame(),
            'total_return': 0,
            'max_drawdown': 0,
            'win_rate': 0,
            'total_trades': 0
        }

    trades_df = pd.DataFrame(trades)
    trades_df['P&L %'] = trades_df['P&L %'] * 100 # Convert to percentage

    total_trades = len(trades_df)
    winning_trades = trades_df[trades_df['P&L %'] > 0]
    # --- FIX: Corrected typo "winning_ trades" to "winning_trades" ---
    win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
    
    # Calculate total return (compounded)
    trades_df['Return Factor'] = (trades_df['P&L %'] / 100) + 1
    total_return = (trades_df['Return Factor'].prod() - 1) * 100
    
    # Calculate Max Drawdown
    trades_df['Cumulative Return'] = trades_df['Return Factor'].cumprod()
    peak = trades_df['Cumulative Return'].cummax()
    drawdown = (trades_df['Cumulative Return'] - peak) / peak
    max_drawdown = drawdown.min() * 100 # As percentage

    return {
        'trades': trades_df.set_index('Entry Date'),
        'total_return': total_return,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'total_trades': total_trades
    }