import getPriceData
import my_cpp_module 

# The list of stocks to be iterated over
symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']

# Calls the modular function, passes in the symbols and saves the result in a 2D matrix
close_matrix = getPriceData.get_price_data(symbols)

# Hands the matrix to C++ for multithreaded processing
averages = my_cpp_module.calculate_averages(close_matrix)
print("Averages calculated by C++:", averages)