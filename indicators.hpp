// Stops the compiler accidentally reading the file twice
#pragma once
// Calculates the Simple Moving Average of the price data
void sma(double * input_ptr, double* output_ptr, int rows, int columns, int column_index, int window);