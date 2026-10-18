# Hybrid Backtest Engine

A tool for testing stock trading strategies against years of real market data, so an idea can be checked before any money is put behind it.

It is built in two halves. Python handles the everyday work like fetching prices, reading settings, and keeping track of the simulated account, while a C++ component takes over for the calculations, working out the trading indicators for every stock at the same time across multiple CPU cores. The engine simulates a trend-following strategy, one that aims to buy stocks already moving upwards and sell those heading down, and reports how it would have performed with realistic trading fees, automatic stop-losses, and a comparison against buying the same stocks and holding them.

## Why it's built this way

Testing a strategy means replaying every trading day for every stock in turn, and the indicator calculations sitting in the middle of that loop are where Python becomes slow. Rewriting the whole project in C++ would have solved the speed problem but made everything else harder, including downloading data, handling settings, and drawing charts. The work is split by what each language is better at: Python for the data handling and reporting, C++ for the repetitive arithmetic.

Because each stock's indicators can be worked out independently of the others, the C++ side gives every stock its own thread, calculates them all at once, and hands the finished results back to Python.

One detail is worth mentioning. The simulation always acts on the previous day's signals, never the current day's. It is easy to write a backtest that accidentally uses information it would not have had at the time, a mistake known as lookahead bias, and it makes a weak strategy look far better than it really is.

## How it works

Everything begins with `update_data.py`, which downloads two years of daily prices for each stock listed in the configuration file and stores them in a local database, so later runs do not need to go back to the internet. When a backtest starts, those prices are loaded into a single table of closing values, one row per trading day and one column per stock, then handed to the C++ module. It calculates the moving averages, momentum, and volatility figures for every stock in parallel. The results come back to Python, where the strategy turns them into buy and sell decisions. It buys when momentum turns positive and the price is trading above its long-term average, since together these point to an uptrend, and bets against a stock when the opposite holds and the stock also looks overbought.

The simulated portfolio then walks through the data one day at a time. How much it commits to each trade depends on how erratically that stock has been moving recently, so steadier stocks receive more capital and more volatile ones receive less. Every trade pays commission and loses a little to slippage, and positions close automatically once they hit a stop-loss or a profit target. At the end the engine prints the final account value, the risk-adjusted return, the largest fall from a peak, and a chart of the balance over time, alongside what would have happened had you bought the same stocks on day one and left them alone.

## Features

- **Parallel calculations.** The moving average, momentum, and volatility code is written in C++ and runs on a separate CPU thread for each stock, with the data shared directly between the two languages rather than copied between them.
- **Position sizing based on volatility.** Instead of putting an identical amount into every trade, the engine commits less capital to stocks that have been moving unpredictably and more to calmer ones.
- **Trading costs included.** Every trade pays a commission and loses a little to slippage, the small gap between the price you see and the price you get. Results are shown next to a buy-and-hold benchmark rather than on their own.
- **No use of future information.** Decisions are made from the previous day's figures, so the simulation cannot trade on anything it would not have known at the time.
- **Local price storage.** Prices are cached on disk and refreshed without creating duplicate entries, which keeps repeat tests fast and lets them run offline.
- **Parameter search with a held-back period.** `optimiser.py` works through thousands of combinations of strategy settings, but chooses between them using only the first 70% of the history. The winner is then scored on the remaining 30%, which played no part in the choice. Reporting only the first number is how a backtest ends up claiming returns it could never repeat.
- **An honesty check on the search itself.** The optimiser reports the average return across every combination during training against the same average on the unseen days, and the correlation between the two. A correlation near zero means a good training score told you nothing about what came next.
- **Web dashboard.** `dashboard.py` serves the whole thing in a browser, with the settings editable and the trained and unseen periods always shown side by side.
- **Tests.** The account logic for buying and for short-selling, and the performance maths, are covered by automated tests.

## Tech stack

| Area | Tools |
|---|---|
| Calculation engine | C++11, [pybind11](https://github.com/pybind/pybind11), multithreading |
| Main application | Python 3, NumPy, Pandas |
| Data storage | `yfinance`, SQLite |
| Charts | Matplotlib |
| Testing | pytest |

## Getting started

**You will need:** Python 3.10 or newer, a C++ compiler (g++ or clang), and pip.

```bash
# 1. Install the Python dependencies
pip install -r requirements.txt

# 2. Build the C++ component
python setup.py build_ext --inplace

# 3. Download and store the price history for the stocks in config.json
python update_data.py

# 4. Run the backtest
python main.py

# 5. (optional) Search for better strategy settings
python optimiser.py

# 6. (optional) Open the dashboard at http://127.0.0.1:5000
python dashboard.py

# 7. Run the tests (from the main project folder)
pytest
```

Running `main.py` prints the final account balance, the buy-and-hold comparison, the risk-adjusted return, and the largest drop from a peak, then displays a chart of the account balance over time.

## Configuration

Every setting lives in [config.json](config.json), so a different set of stocks or a more cautious risk profile can be tried without touching any code:

```json
{
  "portfolio": { "symbols": ["AAPL", "MSFT", "GOOGL", "AMZN"], "initial_cash": 10000.0 },
  "strategy": { "sma_macro_window": 200, "macd_fast": 12, "macd_slow": 26, "rsi_window": 14, "rsi_overbought": 70 },
  "risk_management": {
    "commission_rate": 0.001,
    "slippage_rate": 0.0005,
    "stop_loss_percentage": 0.05,
    "target_percentage": 0.15,
    "target_risk": 0.02
  }
}
```

The `strategy` block controls how quickly the engine reacts to price movements, and the `risk_management` block sets trading costs, how much loss to tolerate before selling, and how large each position should be.

## Project structure

```
hybrid-backtest-engine/
├── engine/                 # The C++ calculation code
│   ├── indicators.cpp/hpp  #   The indicator maths itself
│   └── main.cpp            #   Connects the C++ code to Python
├── src/
│   ├── data_manager.py     # Downloads and stores the price history
│   ├── strategy.py         # Turns indicators into buy and sell decisions
│   ├── portfolio.py        # Tracks the account, trades, and trading costs
│   ├── backtester.py       # The day-by-day simulation loop, used by everything
│   ├── metrics.py          # Sharpe, drawdown, and the buy-and-hold benchmark
│   └── experiment.py       # Loads prices once and splits them into trained/unseen
├── templates/
│   └── dashboard.html      # The dashboard page, charts included
├── tests/
│   ├── test_portfolio.py   # Tests for the buying and short-selling logic
│   └── test_metrics.py     # Tests for the performance maths
├── update_data.py          # Refreshes the stored price data
├── main.py                 # Runs a single backtest and reports the results
├── optimiser.py            # Tries thousands of setting combinations
├── dashboard.py            # Serves the web dashboard
├── config.json             # Stocks, strategy, and risk settings
└── setup.py                # Builds the C++ component
```

The simulation loop lives in one place, `src/backtester.py`. Everything that runs a
backtest calls it, so the command line tools and the dashboard can never drift apart and
quietly start testing different things.

## What the results currently say

Run against AAPL, MSFT, GOOGL and AMZN over two years, the honest answer is that this
strategy does not work. The search finds settings returning +81% over the period it was
allowed to see, and those same settings lose 9.6% over the months that follow. Across all
1,728 combinations the average return falls from +30% while training to -8% on unseen
days, and the correlation between the two scores is -0.04. A good training score carried
no information whatsoever about what happened next.

That is the expected result for a simple trend-following rule on four large, heavily
traded stocks, and it is worth more than a flattering number would be. The engine is
built to find that out cheaply.

## Roadmap

- **Account for the collateral required to short a stock**, which the simulation does not currently set aside. Opening a short also adds its proceeds to the cash balance, which inflates the position size of anything bought afterwards on the same day.
- **Fix the moving-average warm-up.** The C++ `sma` fills its first `window - 1` days with zeros, so with a 200 day average the strategy spends its first 199 days believing every price is above its long-term trend. Those days should be excluded from trading instead.
- **Test on more than four stocks and more than two years.** Four correlated mega-cap technology stocks over one bull run is not enough history to conclude anything.
- **Roll the split forward** rather than cutting the history once, so the strategy is retested repeatedly on successive unseen windows.
- **Measure the C++ speedup.** Time it against an equivalent version written in Python, so the performance claim is backed by numbers.
- **Save results and account histories to a file** so separate runs can be compared.