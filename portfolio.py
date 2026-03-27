class Portfolio:
    def __init__(self, ticker_list, initial_cash=10000.0):
        self.cash = initial_cash
        # Dictionary to track the shares for each ticker
        self.positions = {ticker: 0 for ticker in ticker_list}
        # List to track the total account value over time
        self.equity_curve = []
        # Dictionary to track the prices paid for each stock
        self.buy_prices = {ticker: 0.0 for ticker in ticker_list}

    def handle_signal(self, ticker, current_price, signal):
        commission_rate = 0.001
        # Maximum loss percentage permitted
        stop_loss_percentage = 0.05

        # If a stock is owned it checks if a stop-loss needs to be triggered
        if self.positions[ticker] > 0:
            loss = self.buy_prices[ticker] * (1.0 - stop_loss_percentage)
            # If the price drops below the stop_loss_percentage a sell signal is forced
            if current_price <= loss:
                signal = -1.0
                print(f"Stop Loss triggered for {ticker} at {current_price}")
        # Buys as many shares as the total cash can afford
        if signal == 1.0 and self.cash >= current_price:
            shares_to_buy = self.cash // current_price
            cost = shares_to_buy * current_price
            real_cost = cost + (cost * commission_rate)

            # Checks if we can afford the shares and the fee
            if self.cash >= real_cost:
                self.positions[ticker] += shares_to_buy
                self.cash -= real_cost
                # Sets the new buy price
                self.buy_prices[ticker] = current_price

        # Sells all shares for this stock
        elif signal == -1.0 and self.positions[ticker] > 0:
            money_received = self.positions[ticker] * current_price
            # Subtracts the fee from the money received
            real_payout = money_received - (money_received * commission_rate)
            
            self.positions[ticker] = 0
            self.cash += real_payout
            self.buy_prices[ticker] = 0.0

# Calculates the total account value for the current day
    def update_equity(self, current_prices):
        share_value = 0
        for ticker in self.positions:
            share_value += self.positions[ticker] * current_prices[ticker]
        
        total_value = self.cash + share_value
        self.equity_curve.append(total_value)