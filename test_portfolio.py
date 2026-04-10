import pytest
from portfolio import Portfolio

def test_long_position():
    # Setup
    symbols = ['AAPL'] # SYmbols to test
    initial_capital = 10000.0 # Start capital
    bot = Portfolio(symbols, initial_capital)

    current_price = 100.0 # Current stock price
    signal = 1.0 # Buy signal
    volatility = 0.04 # Volatility percentage of 4 percent

    # Feeds the data into the engine
    bot.handle_signal('AAPL', current_price, signal, volatility)

    # Checks the engine made the correct calculations
    assert bot.positions['AAPL'] == 50, f"Expected 50 shares, but got {bot.positions['AAPL']}"
    assert bot.cash == 4995.0, f"Expected capital 4995.0, but got {bot.cash}"
    assert bot.buy_prices['AAPL'] == 100.0, "The buy price was not recorded properly"

def test_short_position():
    # Setup
    symbols = ['AAPL'] # SYmbols to test
    initial_capital = 10000.0 # Start capital
    bot = Portfolio(symbols, initial_capital)

    current_price = 100.0 # Current stock price
    signal = -1.0 # Sell signal
    volatility = 0.04 # Volatility percentage of 4 percent

    # Feeds the data into the engine
    bot.handle_signal('AAPL', current_price, signal, volatility)

    # Checks the engine made the correct calculations
    assert bot.positions['AAPL'] == -50, f"Expected 50 shares, but got {bot.positions['AAPL']}"
    assert bot.cash == 14995.0, f"Expected capital 14995.0, but got {bot.cash}"
    assert bot.buy_prices['AAPL'] == 100.0, "The short price was not recorded properly"
