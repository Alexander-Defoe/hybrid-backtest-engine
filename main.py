from src.data_manager import DataManager
from src.backtester import run_backtest, calculate_volatility
from src.metrics import summarise, buy_and_hold
from src.portfolio import Portfolio
from src.strategy import Strategy
import numpy as np
import matplotlib.pyplot as plt
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/trader.log"),
        logging.StreamHandler()
    ]
)

# Loads from the config file
with open('config.json', 'r') as file:
    config = json.load(file)

symbols = config['portfolio']['symbols']
initial_cash = config['portfolio']['initial_cash']
volatility_window = config['strategy'].get('volatility_window', 20)

# Local Database integration
logging.info("Connecting to local market database...")
db_manager = DataManager()

# Loads the pivot table of the close prices directly from SQLite
price_df = db_manager.load_close_prices(symbols)
db_manager.close()

# Failsafe if the database is empty
if price_df.empty:
    logging.error("Database is empty. Please run update_data.py first.")
    exit(1)

# Converts the Pandas dataframe into a contiguous 2D numpy array for C++
close_matrix = price_df.to_numpy(dtype=np.float64)

# Initiates the strategy and generates signals
my_strategy = Strategy(config['strategy'])
signal_data = my_strategy.generate_signals(close_matrix)

volatility_matrix = calculate_volatility(close_matrix, volatility_window)

# Runs the simulation day by day
my_portfolio = run_backtest(
    close_matrix, signal_data, volatility_matrix,
    symbols, initial_cash, config['risk_management']
)

# Backtesting results
stats = summarise(my_portfolio.equity_curve)

print(f"Final Account Balance: ${my_portfolio.cash:.2f}")
print(f"Final Total Equity: ${stats['final_equity']:.2f}")
print(f"Buy and Hold return: {buy_and_hold(close_matrix, symbols, initial_cash)}")
print(f"Sharpe Ratio: {stats['sharpe']:.2f}")
print(f"Max Drawdown: {stats['max_drawdown'] * 100:.2f}%")

# Plots the equity curve of the algorithm into a chart
plt.plot(my_portfolio.equity_curve)
plt.title("Performance")
plt.xlabel("Days")
plt.ylabel("Account Value")
plt.show()
