from data_fetcher import fetch_stock_data
from strategy import generate_signals
from backtester import Backtester
import pandas as pd
from datetime import date, timedelta

def main():
    print("=== NSE 500 Moving Average Strategy Backtester ===\n")

    ma_type = input("Enter MA type (SMA / EMA / WMA): ").upper()
    fast = int(input("Enter FAST MA period (e.g., 10): "))
    slow = int(input("Enter SLOW MA period (e.g., 50): "))

    entry_rule = "crossover"
    print("\nExit options:\n1. Opposite crossover\n2. Profit/Stop (10% / 5%)")
    exit_choice = input("Choose exit rule (1 or 2): ")
    exit_rule = "opposite" if exit_choice == "1" else "profit_stop"

    symbol = input("\nEnter NSE stock symbol (e.g., INFY, TCS, RELIANCE): ").upper()

    print(f"\nFetching 3 months of data for {symbol}...")
    data = fetch_stock_data(symbol)

    print("Generating signals...")
    df = generate_signals(data, ma_type, fast, slow)

    print("Running backtest...")
    bt = Backtester(df, entry_rule, exit_rule)
    results = bt.run()

    print("\n=== Strategy Report ===")
    print(f"Strategy: {fast}/{slow}-day {ma_type} crossover")
    print(f"Stock: {symbol}")
    print(f"Period: {df.index[0].date()} to {df.index[-1].date()}")
    print(f"Entry: Buy when {fast}-day {ma_type} crosses above {slow}-day {ma_type}")
    if exit_rule == "opposite":
        print("Exit: Opposite crossover (bearish)")
    else:
        print("Exit: 10% profit or 5% stop-loss")
    print(f"\nTotal Return: {results['total_return']}%")
    print(f"Max Drawdown: {results['drawdown']}%")
    print(f"Win Rate: {results['win_rate']}%")
    print(f"Number of Trades: {results['num_trades']}")
    print("\nTrade Log:")
    print(results["trades"].to_string(index=False))

if __name__ == "__main__":
    main()
