import getPriceData
import my_cpp_module 
from portfolio import Portfolio
import numpy as np
import matplotlib.pyplot as plt

# The list of stocks to be iterated over
symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']

# Calls the modular function, passes in the symbols and saves the result in a 2D matrix
close_matrix = getPriceData.get_price_data(symbols)

sma_window = 20

sma_results = my_cpp_module.calculate_smas(close_matrix, sma_window)

# Creates buy/sell signals in Python using NumPy
# If Price > SMA then buy, else sell
signal_data = np.where(close_matrix > sma_results, 1.0, -1.0)

# The first 20 days of the SMA are 0.0 so we force those signals to 0.0
signal_data[sma_results == 0.0] = 0.0

# Initializes the Portfolio
my_portfolio = Portfolio(symbols, initial_cash=10000.0)

# The backesting loop
rows = close_matrix.shape[0]

for r in range(rows):
    # Loops through each stock
    for i, ticker in enumerate(symbols):
        # Gets their close prices and signal
        current_price = close_matrix[r, i]
        current_signal = signal_data[r, i]
        
        # Passes the price and signal to the portfolio
        my_portfolio.handle_signal(ticker, current_price, current_signal)
    
    # A dictionary to map each ticker to its closing price
    day_prices = {ticker: close_matrix[r, j] for j, ticker in enumerate(symbols)}

    # Calculates the total net worth for the day
    my_portfolio.update_equity(day_prices)

# Backtesting results
print(f"Final Account Balance: ${my_portfolio.cash:.2f}")
print(f"Final Total Equity: ${my_portfolio.equity_curve[-1]:.2f}")

# Assigns the starting cash to be allocated to each stock
capital_per_stock = 10000.0 / len(symbols)

# Dictionary to hold the number of shares bought on day 1
total_shares = {}

for i, ticker in enumerate(symbols):
    # Gets the price of the stock on day 1
    day_1_price = close_matrix[0,i]
    # Adds the final value of the current stocks shares to the total
    total_shares[ticker] = capital_per_stock // day_1_price

final_value = 0

# Calculates the final value of the buy and hold on the last trading day
for i, ticker in enumerate(symbols):
    # Gets the price of the stock on the final day
    last_day_price = close_matrix[-1, i]
    # Adds the final value of the current stocks shares to the total
    final_value += total_shares[ticker] * last_day_price

print(f"Buy and Hold return: {final_value}")

# PLots the equity curve of the algorithm into a chart
plt.plot(my_portfolio.equity_curve)
plt.title("Performance")
plt.xlabel("Days")
plt.ylabel("Account Value")
plt.show()