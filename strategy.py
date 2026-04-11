import numpy as np
import my_cpp_module

class Strategy:
    def __init__(self, strategy_config):
        # Loads the strategy parameters from the config file
        self.macro_window = strategy_config['sma_macro_window']
        self.rsi_window = strategy_config['rsi_window']
        self.overbought_level = strategy_config['rsi_overbought']

    def generate_signals(self, close_matrix):
        # Calculates the indicators
        macd_results = my_cpp_module.calculate_macd(close_matrix) 
        sma_200_results = my_cpp_module.calculate_smas(close_matrix, self.macro_window) 
        rsi_results = my_cpp_module.calculate_rsi(close_matrix, self.rsi_window)       

        # Creates an empty matrix for the buy sell signals
        signal_data = np.zeros_like(close_matrix)

        # Clloses shorts if the MACD turns positive
        signal_data[macd_results > 0] = 0.5  
        # CLoses the longs if the MACD turns negative
        signal_data[macd_results < 0] = -0.5 

        # When the MACD is greater than 0 it buys
        long_condition = (macd_results > 0) & (close_matrix > sma_200_results)
        signal_data[long_condition] = 1.0

        # When the MACD is less than 0 it sells
        short_condition = (macd_results < 0) & (close_matrix < sma_200_results) & (rsi_results > self.overbought_level)
        signal_data[short_condition] = -1.0

        return signal_data