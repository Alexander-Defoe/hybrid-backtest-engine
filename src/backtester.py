import my_cpp_module

from src.portfolio import Portfolio

# Volatility assumed on the very first day, before there is any history to measure it from
STARTING_VOLATILITY = 0.001


def calculate_volatility(close_matrix, window):
    """Works out how much each stock has been moving about, one column per stock."""
    return my_cpp_module.calculate_volatility(close_matrix, window)


def run_backtest(close_matrix, signal_data, volatility_matrix, symbols, initial_cash, risk_config):
    """Replays the price history one day at a time and returns the finished portfolio.

    The simulation always acts on the *previous* day's signal and volatility. Using the
    current day's figures would mean trading on information that was not available at the
    time, which is called lookahead bias and makes any strategy look far better than it is.
    """
    portfolio = Portfolio(symbols, initial_cash, risk_config)

    rows = close_matrix.shape[0]

    for r in range(rows):
        # Loops through each stock for the current day
        for i, ticker in enumerate(symbols):

            current_price = close_matrix[r, i]

            if r == 0:
                # No previous day exists yet, so nothing is traded on the first day
                current_signal = 0.0
                current_volatility = STARTING_VOLATILITY
            else:
                current_signal = signal_data[r - 1, i]
                current_volatility = volatility_matrix[r - 1, i]

            portfolio.handle_signal(ticker, current_price, current_signal, current_volatility)

        # A dictionary mapping each ticker to its closing price for the day
        day_prices = {ticker: close_matrix[r, j] for j, ticker in enumerate(symbols)}

        # Records the total net worth at the end of the day
        portfolio.update_equity(day_prices)

    return portfolio
