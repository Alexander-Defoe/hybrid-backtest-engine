"""Shared plumbing for running a backtest split into a training and a held-back period.

Both the optimiser and the dashboard need the same thing: load the prices once, cut the
history in two, and score a set of settings over each half. That lives here so the two
never drift apart.
"""

import numpy as np

from src.backtester import run_backtest, calculate_volatility
from src.data_manager import DataManager
from src.metrics import summarise, buy_and_hold_curve
from src.strategy import Strategy

# Fraction of the price history used to choose the settings. The remainder is held back
# and never looked at until a single winner has been picked.
DEFAULT_TRAIN_FRACTION = 0.7


class MarketData:
    """The price history, loaded once and reused."""

    def __init__(self, config):
        self.symbols = config['portfolio']['symbols']
        self.initial_cash = config['portfolio']['initial_cash']
        volatility_window = config['strategy'].get('volatility_window', 20)

        db_manager = DataManager()
        self.price_df = db_manager.load_close_prices(self.symbols)
        db_manager.close()

        if self.price_df.empty:
            raise RuntimeError("Database is empty. Please run update_data.py first.")

        self.close_matrix = self.price_df.to_numpy(dtype=np.float64)
        self.rows = self.close_matrix.shape[0]

        # Every indicator only ever looks backwards in time, so volatility is calculated
        # once over the whole history and then sliced. That gives the held-back period the
        # same warm-up a live system would have had, without letting it see the future.
        self.volatility_matrix = calculate_volatility(self.close_matrix, volatility_window)

        self.dates = [d.strftime('%Y-%m-%d') for d in self.price_df.index]

    def split_at(self, train_fraction=DEFAULT_TRAIN_FRACTION):
        return int(self.rows * train_fraction)


def evaluate_period(market, signal_data, risk_config, start, end):
    """Runs the simulation over one slice of history and reports how it went.

    `start` and `end` index into the full history. Slicing prices, signals and volatility
    at the same points keeps them aligned, so the simulation still acts on the previous
    day's figures exactly as it does over the full run.
    """
    close = market.close_matrix[start:end]
    signals = signal_data[start:end]
    volatility = market.volatility_matrix[start:end]

    portfolio = run_backtest(
        close, signals, volatility,
        market.symbols, market.initial_cash, risk_config
    )

    stats = summarise(portfolio.equity_curve)
    benchmark = buy_and_hold_curve(close, market.symbols, market.initial_cash)

    return {
        'stats': stats,
        'benchmark_stats': summarise(benchmark),
        'equity_curve': [float(v) for v in portfolio.equity_curve],
        'benchmark_curve': [float(v) for v in benchmark],
        'dates': market.dates[start:end],
        'positions': {t: int(q) for t, q in portfolio.positions.items()},
        'cash': float(portfolio.cash),
    }


def build_signals(market, strategy_config):
    """Generates the buy and sell signals over the whole history for one set of settings."""
    return Strategy(strategy_config).generate_signals(market.close_matrix)
