class Portfolio:
    def __init__(self, ticker_list, initial_cash=10000.0):
        self.cash = initial_cash
        # Dictionary to track the shares for each ticker
        self.positions = {ticker: 0 for ticker in ticker_list}
        # List to track the total account value over time
        self.equity_curve = []

    def handle_signal(self, ticker, current_price, signal):
        # Buys as many shares as the total cash can afford
        if signal == 1.0 and self.cash >= current_price:
            shares_to_buy = self.cash // current_price
            self.positions[ticker] += shares_to_buy
            self.cash -= (shares_to_buy * current_price)

        # Sells all shares for this stock
        elif signal == -1.0 and self.positions[ticker] > 0:
            money_received = self.positions[ticker] * current_price
            self.positions[ticker] = 0
            self.cash += money_received

# Calculates the total account value for the current day
    def update_equity(self, current_prices):
        share_value = 0
        for ticker in self.positions:
            share_value += self.positions[ticker] * current_prices[ticker]
        
        total_value = self.cash + share_value
        self.equity_curve.append(total_value)