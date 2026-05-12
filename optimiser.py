import numpy as np
import itertools
from src.data_manager import DataManager
import my_cpp_module 
from src.portfolio import Portfolio
from src.strategy import Strategy
import json

# Loads the base config and data
with open('config.json', 'r') as file:
    base_config = json.load(file)

symbols = base_config['portfolio']['symbols']
initial_cash = base_config['portfolio']['initial_cash']

print("Loading data...")
db_manager = DataManager()
price_df = db_manager.load_close_prices(symbols)
db_manager.close()
close_matrix = price_df.to_numpy(dtype=np.float64)
rows = close_matrix.shape[0]

# Calculates volatility once
volatility_matrix = my_cpp_module.calculate_volatility(close_matrix, 20)

# Defines the ranges of parameters to be tested
macd_fast_options = [8, 10, 12, 14]
macd_slow_options = [21, 26, 30, 35]
rsi_window_options = [10, 14, 21]
rsi_overbought_options = [70, 75, 80]
target_percentage_options = [0.10, 0.15, 0.20, 0.25]
stop_loss_options = [0.05, 0.08, 0.10]

# Creates a list of all possible combinations
param_combinations = list(itertools.product(
    macd_fast_options, macd_slow_options, rsi_window_options, 
    rsi_overbought_options, target_percentage_options, stop_loss_options
))

print(f"Total combinations to test: {len(param_combinations)}")
print("Running simulations... this might take a minute...")

results = []

# The grid search loop
for params in param_combinations:
    fast, slow, rsi_w, rsi_ob, target, stop = params
    
    # Skips illogical MACD settings
    if fast >= slow:
        continue

    # Updates the config dictionaries for that specific run
    strat_config = base_config['strategy'].copy()
    strat_config['macd_fast'] = fast
    strat_config['macd_slow'] = slow
    strat_config['rsi_window'] = rsi_w
    strat_config['rsi_overbought'] = rsi_ob

    risk_config = base_config['risk_management'].copy()
    risk_config['target_percentage'] = target
    risk_config['stop_loss_percentage'] = stop

    # Generates signals
    my_strategy = Strategy(strat_config)
    signal_data = my_strategy.generate_signals(close_matrix)

    # Initialises the portfolio
    my_portfolio = Portfolio(symbols, initial_cash, risk_config)

    # Runs the backtest
    for r in range(rows):
        for i, ticker in enumerate(symbols):
            current_price = close_matrix[r, i]
            
            # Shifts signal to prevent lookahead bias
            if r == 0:
                current_signal = 0.0
                current_volatility = 0.001
            else:
                current_signal = signal_data[r - 1, i]
                current_volatility = volatility_matrix[r - 1, i]

            my_portfolio.handle_signal(ticker, current_price, current_signal, current_volatility)
        
        day_prices = {ticker: close_matrix[r, j] for j, ticker in enumerate(symbols)}
        my_portfolio.update_equity(day_prices)

    # Calculates stats
    final_equity = my_portfolio.equity_curve[-1]
    returns = np.diff(my_portfolio.equity_curve) / my_portfolio.equity_curve[:-1]
    std_return = np.std(returns)
    avg_return = np.mean(returns)
    sharpe = (avg_return / std_return) * np.sqrt(252) if std_return != 0 else 0

    # Saves the result
    results.append({
        'params': {'Fast': fast, 'Slow': slow, 'RSI_W': rsi_w, 'RSI_OB': rsi_ob, 'Target': target, 'Stop': stop},
        'equity': final_equity,
        'sharpe': sharpe
    })

# Sorts and displays the results by highest equity
results.sort(key=lambda x: x['equity'], reverse=True)

print("\nTOP 5 STRATEGIES:")
for i in range(min(5, len(results))):
    res = results[i]
    p = res['params']
    print(f"Rank {i+1}:")
    print(f"  Equity: ${res['equity']:.2f} | Sharpe: {res['sharpe']:.2f}")
    print(f"  MACD: ({p['Fast']}, {p['Slow']}) | RSI: {p['RSI_W']} days, >{p['RSI_OB']} | Target: {p['Target']*100}% | Stop: {p['Stop']*100}%")
    print("-" * 25)