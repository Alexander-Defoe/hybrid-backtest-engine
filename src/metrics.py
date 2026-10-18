import numpy as np

# Number of trading days in a year, used to turn daily figures into annual ones
TRADING_DAYS_PER_YEAR = 252


def summarise(equity_curve):
    """Turns a list of daily account values into the headline performance figures."""
    curve = np.asarray(equity_curve, dtype=np.float64)

    # Not enough days to measure anything meaningful
    if curve.size < 2:
        return {
            'final_equity': float(curve[-1]) if curve.size else 0.0,
            'total_return': 0.0,
            'sharpe': 0.0,
            'max_drawdown': 0.0,
        }

    # The daily percentage change in account value
    returns = np.diff(curve) / curve[:-1]

    # Average daily profit and how much it varies day to day
    avg_return = np.mean(returns)
    std_return = np.std(returns)

    # Sharpe ratio: profit per unit of risk, scaled up to an annual figure
    sharpe = (avg_return / std_return) * np.sqrt(TRADING_DAYS_PER_YEAR) if std_return != 0 else 0.0

    # The highest the account ever reached at each point in time
    peak = np.maximum.accumulate(curve)
    # How far below that peak the account was on each day
    drawdown = (curve - peak) / peak

    return {
        'final_equity': float(curve[-1]),
        'total_return': float((curve[-1] - curve[0]) / curve[0]) if curve[0] != 0 else 0.0,
        'sharpe': float(sharpe),
        'max_drawdown': float(np.min(drawdown)),
    }


def buy_and_hold_shares(close_matrix, symbols, initial_cash):
    """Whole shares of each stock that the starting cash could buy on the first day."""
    # The starting cash is split evenly between the stocks
    capital_per_stock = initial_cash / len(symbols)
    return np.array([capital_per_stock // close_matrix[0, i] for i in range(len(symbols))])


def buy_and_hold(close_matrix, symbols, initial_cash):
    """Works out what simply buying all the stocks on day one and holding would have made."""
    shares = buy_and_hold_shares(close_matrix, symbols, initial_cash)
    return float(np.sum(shares * close_matrix[-1]))


def buy_and_hold_curve(close_matrix, symbols, initial_cash):
    """The day by day value of the buy and hold benchmark, for charting alongside the strategy."""
    shares = buy_and_hold_shares(close_matrix, symbols, initial_cash)
    # Any cash left over after buying whole shares just sits there
    leftover_cash = initial_cash - float(np.sum(shares * close_matrix[0]))
    return (close_matrix @ shares + leftover_cash).tolist()
