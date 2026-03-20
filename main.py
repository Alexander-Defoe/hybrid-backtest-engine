import getPriceData
import my_cpp_module 

# The list of stocks to be iterated over
symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']

# Calls the modular function, passes in the symbols and saves the result in a 2D matrix
close_matrix = getPriceData.get_price_data(symbols)

sma_window = 20

sma_results = my_cpp_module.calculate_smas(close_matrix, sma_window)

print("SMA Matrix Shape:", sma_results.shape)

print("\nResults:")
print(sma_results)