// Stops the compiler accidentally reading the file twice
#pragma once
// Calculates the Simple Moving Average of the price data
void sma(double * input_ptr, double* output_ptr, int rows, int columns, int column_index, int window);

// Generates buy/sell signals
void generate_signals(double* price_ptr, double* sma_ptr, double* signal_ptr, int rows, int columns, int index);

// Calculates the RSI - to be implemented in main.py later
void rsi(double* in_ptr, double* out_ptr, int rows, int cols, int col_idx, int window);

// Calculates the MACD
void macd(double* in_ptr, double* out_ptr, int rows, int cols, int col_idx);