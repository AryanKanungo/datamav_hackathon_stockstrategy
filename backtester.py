# backtester.py
import pandas as pd
import numpy as np
from datetime import timedelta

class Backtester:
    def __init__(self, df: pd.DataFrame, profit_target: float = 0.10, stop_loss: float = 0.05,
                 exit_rule: str = "profit_stop", trailing_stop_pct: float = None, max_hold_days: int = None):
        """
        df: must have columns ['Close', 'Signal'] plus datetime index
        profit_target, stop_loss: e.g., 0.10 means 10%
        exit_rule: 'profit_stop' or 'opposite' or 'days' or 'trailing'
        trailing_stop_pct: e.g., 0.05 for trailing 5% from peak
        max_hold_days: integer number of calendar days to force exit
        """
        self.df = df.copy()
        self.profit_target = float(profit_target)
        self.stop_loss = float(stop_loss)
        self.exit_rule = exit_rule
        self.trailing_stop_pct = trailing_stop_pct
        self.max_hold_days = max_hold_days
        self.trades = []

    def run(self):
        df = self.df
        in_trade = False
        entry_price = 0.0
        entry_date = None
        peak_price = None

        for i in range(1, len(df)):
            idx = df.index[i]
            prev_sig = df['Signal'].iat[i-1]
            cur_sig  = df['Signal'].iat[i]
            price = float(df['Close'].iat[i])

            # Entry: bullish crossover (previous <=0 and now >0)
            if not in_trade and prev_sig <= 0 and cur_sig > 0:
                in_trade = True
                entry_price = price
                peak_price = price
                entry_date = idx

            elif in_trade:
                # update peak for trailing stop
                if price > peak_price:
                    peak_price = price

                price_change = (price - entry_price) / entry_price

                # Exit by opposite crossover
                if self.exit_rule == 'opposite' and cur_sig < 0:
                    self._record(entry_date, idx, entry_price, price)

                    in_trade = False
                    entry_price = 0.0
                    peak_price = None

                # Exit by profit / stop
                elif self.exit_rule == 'profit_stop':
                    if price_change >= self.profit_target or price_change <= -self.stop_loss:
                        self._record(entry_date, idx, entry_price, price)
                        in_trade = False
                        entry_price = 0.0
                        peak_price = None

                # Exit by trailing stop
                elif self.exit_rule == 'trailing' and (self.trailing_stop_pct is not None):
                    drop_from_peak = (peak_price - price) / peak_price
                    if drop_from_peak >= self.trailing_stop_pct:
                        self._record(entry_date, idx, entry_price, price)
                        in_trade = False
                        entry_price = 0.0
                        peak_price = None

                # Exit by fixed days
                if in_trade and self.max_hold_days is not None:
                    # uses calendar days difference
                    hold_days = (idx.date() - entry_date.date()).days
                    if hold_days >= int(self.max_hold_days):
                        self._record(entry_date, idx, entry_price, price)
                        in_trade = False
                        entry_price = 0.0
                        peak_price = None

        return self._performance()

    def _record(self, entry_date, exit_date, entry_price, exit_price):
        profit_pct = ((exit_price - entry_price) / entry_price) * 100.0
        self.trades.append({
            'Entry Date': entry_date,
            'Exit Date': exit_date,
            'Entry Price': float(round(entry_price, 2)),
            'Exit Price': float(round(exit_price, 2)),
            'Profit %': float(round(profit_pct, 2))
        })

    def _performance(self):
        if not self.trades:
            return {
                "total_return": 0.0,
                "drawdown": 0.0,
                "win_rate": 0.0,
                "num_trades": 0,
                "trades": pd.DataFrame()
            }
        trades_df = pd.DataFrame(self.trades)
        trades_df['Profit %'] = pd.to_numeric(trades_df['Profit %'], errors='coerce').fillna(0.0)
        trades_df['Cumulative Return'] = trades_df['Profit %'].cumsum().astype(float)

        cumulative = trades_df['Cumulative Return'].values
        rolling_max = np.maximum.accumulate(cumulative)
        drawdowns = rolling_max - cumulative
        max_dd = float(drawdowns.max()) if len(drawdowns) > 0 else 0.0

        total_return = float(trades_df['Profit %'].sum())
        win_rate = float((trades_df['Profit %'] > 0).mean() * 100.0)
        return {
            "total_return": round(total_return, 2),
            "drawdown": round(max_dd, 2),
            "win_rate": round(win_rate, 2),
            "num_trades": len(trades_df),
            "trades": trades_df
        }
