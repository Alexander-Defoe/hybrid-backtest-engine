#include "indicators.hpp"

void sma(double * input_ptr, double* output_ptr, int rows, int columns, int column_index, int window) {
    double current_sum = 0.0;

    for (int r = 0; r < window; ++r) {
        current_sum += input_ptr[(r * columns) + column_index];

        // Pads the earlier days with 0.0
        if (r < window -1) {
            output_ptr[(r*columns) + column_index] = 0.0;
        }
    }

    // Saves the SMA at the end of the first window
    output_ptr[((window-1) * columns) + column_index] = current_sum / window;

    // Slides the window
    for (int r = window; r < rows; ++r) {
        // Adds the next price
        current_sum += input_ptr[(r * columns) + column_index];
        // Subtracts the oldest price that is no longer in the window
        current_sum -= input_ptr[((r - window) * columns) + column_index];
        //Saves the new average into the matrix
        output_ptr[(r * columns) + column_index] = current_sum / window;
    }
}