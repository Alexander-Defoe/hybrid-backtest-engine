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
macd_results = my_cpp_module.calculate_macd(close_matrix) # MACD has no window parameter

sma_200_results = my_cpp_module.calculate_smas(close_matrix, 200)
rsi_results = my_cpp_module.calculate_rsi(close_matrix, 14)       

# Creates buy/sell signals using the MACD
signal_data = np.zeros_like(close_matrix)

# Tries to close shorts if the MACD turns positive
signal_data[macd_results > 0] = 0.5  
# Tries to close longs if the MACD turns negative
signal_data[macd_results < 0] = -0.5 

# When the MACD is greater than 0 it buys
long_condition = (macd_results > 0) & (close_matrix > sma_200_results)
signal_data[long_condition] = 1.0

# When the MACD is less than 0 it sells
short_condition = (macd_results < 0) & (close_matrix < sma_200_results) & (rsi_results > 70)
signal_data[short_condition] = -1.0

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
        
        start_idx = max(0, r - 20)
        recent_prices = close_matrix[start_idx:r+1, i]
        
        if len(recent_prices) > 1:
            recent_returns = np.diff(recent_prices) / recent_prices[:-1]
            current_volatility = np.std(recent_returns)
        else:
            current_volatility = 0.001

        # Passes the price, signal, and volatility to the portfolio
        my_portfolio.handle_signal(ticker, current_price, current_signal, current_volatility)
    
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

# Calculates the daily percentage return
returns = np.diff(my_portfolio.equity_curve) / my_portfolio.equity_curve[:-1]

# Calculates the average daily profit
avg_return = np.mean(returns)
# Calculates the standard deviation
std_return = np.std(returns)
# Calculates the sharpe ratio
sharpe_ratio = (avg_return / std_return) * np.sqrt(252) if std_return != 0 else 0

# Gets the highest peak the account value reached
peak = np.maximum.accumulate(my_portfolio.equity_curve)
# Calculates the percentage drop from the peak for each day
drawdown = (my_portfolio.equity_curve - peak) / peak
# Worst percentage drop
max_drawdown = np.min(drawdown)

print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
print(f"Max Drawdown: {max_drawdown * 100:.2f}%")

# PLots the equity curve of the algorithm into a chart
plt.plot(my_portfolio.equity_curve)
plt.title("Performance")
plt.xlabel("Days")
plt.ylabel("Account Value")
plt.show()