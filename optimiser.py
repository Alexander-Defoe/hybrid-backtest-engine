import numpy as np
import itertools
import json

from src.data_manager import DataManager
from src.backtester import run_backtest, calculate_volatility
from src.metrics import summarise, buy_and_hold
from src.strategy import Strategy

# Fraction of the price history used to choose the settings. The remainder is held back
# and never looked at until a single winner has been picked.
TRAIN_FRACTION = 0.7

# Loads the base config and data
with open('config.json', 'r') as file:
    base_config = json.load(file)

symbols = base_config['portfolio']['symbols']
initial_cash = base_config['portfolio']['initial_cash']
volatility_window = base_config['strategy'].get('volatility_window', 20)

print("Loading data...")
db_manager = DataManager()
price_df = db_manager.load_close_prices(symbols)
db_manager.close()

close_matrix = price_df.to_numpy(dtype=np.float64)
rows = close_matrix.shape[0]

# Every indicator only ever looks backwards in time, so they are calculated once over the
# whole history and then sliced. Doing it this way gives the held-back period the same
# warm-up history a live system would have had, without letting it see the future.
volatility_matrix = calculate_volatility(close_matrix, volatility_window)

# The point where the history is cut in two
split = int(rows * TRAIN_FRACTION)

train_close = close_matrix[:split]
train_volatility = volatility_matrix[:split]

test_close = close_matrix[split:]
test_volatility = volatility_matrix[split:]

train_dates = price_df.index[:split]
test_dates = price_df.index[split:]

print(f"Training period: {train_dates[0].date()} to {train_dates[-1].date()} ({split} days)")
print(f"Held-back period: {test_dates[0].date()} to {test_dates[-1].date()} ({rows - split} days)")

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

# The stop-loss and profit-target settings do not affect the indicators at all, so the same
# signals get reused across every combination that shares the indicator settings.
signal_cache = {}


def signals_for(fast, slow, rsi_w, rsi_ob):
    key = (fast, slow, rsi_w, rsi_ob)
    if key not in signal_cache:
        strat_config = base_config['strategy'].copy()
        strat_config['macd_fast'] = fast
        strat_config['macd_slow'] = slow
        strat_config['rsi_window'] = rsi_w
        strat_config['rsi_overbought'] = rsi_ob
        signal_cache[key] = Strategy(strat_config).generate_signals(close_matrix)
    return signal_cache[key]


results = []

# The grid search loop, run only on the training period
for params in param_combinations:
    fast, slow, rsi_w, rsi_ob, target, stop = params

    # Skips illogical MACD settings
    if fast >= slow:
        continue

    risk_config = base_config['risk_management'].copy()
    risk_config['target_percentage'] = target
    risk_config['stop_loss_percentage'] = stop

    signal_data = signals_for(fast, slow, rsi_w, rsi_ob)

    portfolio = run_backtest(
        train_close, signal_data[:split], train_volatility,
        symbols, initial_cash, risk_config
    )

    stats = summarise(portfolio.equity_curve)

    results.append({
        'params': {'Fast': fast, 'Slow': slow, 'RSI_W': rsi_w, 'RSI_OB': rsi_ob,
                   'Target': target, 'Stop': stop},
        'risk_config': risk_config,
        'signal_key': (fast, slow, rsi_w, rsi_ob),
        'train': stats,
    })

# Sorts the results by the training-period equity
results.sort(key=lambda x: x['train']['final_equity'], reverse=True)


def evaluate_on_test(result):
    """Runs one settings combination over the held-back period it has never seen."""
    portfolio = run_backtest(
        test_close, signal_cache[result['signal_key']][split:], test_volatility,
        symbols, initial_cash, result['risk_config']
    )
    return summarise(portfolio.equity_curve)


print("\n" + "=" * 78)
print("TOP 5 BY TRAINING PERIOD, CHECKED AGAINST THE HELD-BACK PERIOD")
print("=" * 78)
print("The 'Trained' column is what the search optimised for. The 'Unseen' column is the")
print("only one that means anything, because those days played no part in the choice.\n")

for i in range(min(5, len(results))):
    res = results[i]
    p = res['params']
    test_stats = evaluate_on_test(res)

    print(f"Rank {i + 1}:  MACD({p['Fast']}, {p['Slow']}) | RSI {p['RSI_W']}d >{p['RSI_OB']} | "
          f"Target {p['Target'] * 100:.0f}% | Stop {p['Stop'] * 100:.0f}%")
    print(f"{'':>10}{'Trained':>14}{'Unseen':>14}")
    print(f"{'Return':>10}{res['train']['total_return'] * 100:>13.1f}%{test_stats['total_return'] * 100:>13.1f}%")
    print(f"{'Sharpe':>10}{res['train']['sharpe']:>14.2f}{test_stats['sharpe']:>14.2f}")
    print(f"{'Drawdown':>10}{res['train']['max_drawdown'] * 100:>13.1f}%{test_stats['max_drawdown'] * 100:>13.1f}%")
    print("-" * 78)

# The honest headline: the single best training combination, judged only on unseen days
best = results[0]
best_test = evaluate_on_test(best)
benchmark = buy_and_hold(test_close, symbols, initial_cash)

print("\nVERDICT ON THE HELD-BACK PERIOD")
print("-" * 78)
print(f"Best settings found in training : ${best_test['final_equity']:>12,.2f}  "
      f"({best_test['total_return'] * 100:+.1f}%)")
print(f"Buying and holding instead      : ${benchmark:>12,.2f}  "
      f"({(benchmark - initial_cash) / initial_cash * 100:+.1f}%)")

if best_test['final_equity'] > benchmark:
    print("\nThe strategy beat buy-and-hold on days it had never seen.")
else:
    print("\nThe strategy did NOT beat buy-and-hold on days it had never seen.")

# How much of the training performance was real, measured across the whole search
train_returns = np.array([r['train']['total_return'] for r in results])
test_returns = np.array([evaluate_on_test(r)['total_return'] for r in results])

print("\nOVERFITTING CHECK (all {} combinations)".format(len(results)))
print("-" * 78)
print(f"Average return while training : {np.mean(train_returns) * 100:+.1f}%")
print(f"Average return when unseen    : {np.mean(test_returns) * 100:+.1f}%")
print(f"Best return while training    : {np.max(train_returns) * 100:+.1f}%")
print(f"That same setting when unseen : {test_returns[np.argmax(train_returns)] * 100:+.1f}%")

# Whether a good training score tells you anything at all about future performance
if np.std(train_returns) > 0 and np.std(test_returns) > 0:
    correlation = np.corrcoef(train_returns, test_returns)[0, 1]
    print(f"\nCorrelation between the two   : {correlation:+.2f}")
    print("A number near zero means the training scores carried no information about the")
    print("held-back period, so picking the top of the list was no better than guessing.")
