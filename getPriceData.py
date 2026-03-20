import concurrent.futures
import yfinance as yf
import pandas as pd
import numpy as np

# Helper function to fetch historical price data for a stock symbol over a defined period
def fetch_data(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)

    # Attempts to fetch the symbols data
    try:
        data = stock.history(period="1y")
    # If an error occurs the appropriate message is printed
    except Exception as e:
        print(f"Error getting data for {ticker_symbol}: {e}")
        return None
    
    # Checks if the returned dataframe is empty thus invalid
    if data.empty:
        return None
    # If successful the dataframe is returned
    return data

# Takes a list of stock symbols and concurrently iterates over the helper function fetch_data
def get_price_data(symbols):
    # Fetches the price data concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(fetch_data, symbols))

    # Stores the expected number of trading days
    target_length = 0
    for df in results:
        # Upon succesful download
        if df is not None:
            # Sets the target length to the number of rows in this valid dataframe
            target_length = len(df)
            break

    # Cleans and filters the arrays to ensure the dataset is downloaded and matches the baseline length
    all_close_prices = []
    for df in results:
        if df is None or len(df) != target_length:
            continue
        all_close_prices.append(df['Close'].to_numpy())

    # Stacks stock columns into a 2D matrix which creates a contiguous...
    # block of memory that C++ can process at maximum speed.
    master_matrix = np.column_stack(all_close_prices)
    return master_matrix