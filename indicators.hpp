// Stops the compiler accidentally reading the file twice
#pragma once
// Calculates the Simple Moving Average of the price data
void sma(double * input_ptr, double* output_ptr, int rows, int columns, int column_index, int window);

void generate_signals(double* price_ptr, double* sma_ptr, double* signal_ptr, int rows, int columns, int index);