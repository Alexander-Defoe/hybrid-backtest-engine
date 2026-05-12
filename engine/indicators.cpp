#include "indicators.hpp"
#include <cmath>

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

// Calculates the Relative Strength Index for a single stock
void rsi(double* in_ptr, double* out_ptr, int rows, int cols, int col_idx, int window) {
    double gain_sum = 0.0, loss_sum = 0.0;
    
    // Initializes day 0 with an RSI of 50
    out_ptr[0 * cols + col_idx] = 50.0; 

    // Calculates the initial average gain and loss over the first window
    for (int r = 1; r <= window && r < rows; ++r) {
        // Calculates the daily price change
        double diff = in_ptr[r * cols + col_idx] - in_ptr[(r - 1) * cols + col_idx];
        
        if (diff > 0) gain_sum += diff;
        else loss_sum -= diff;
        
        // Keeps the RSI neutral until enough data is gathered
        out_ptr[r * cols + col_idx] = 50.0; 
    }

    // Establishes the averages
    double avg_gain = gain_sum / window;
    double avg_loss = loss_sum / window;

    // Calculates the smoothed RSI for all remaining days
    for (int r = window + 1; r < rows; ++r) {
        double diff = in_ptr[r * cols + col_idx] - in_ptr[(r - 1) * cols + col_idx];
        
        // Separates the positive and negative movements
        double gain = (diff > 0) ? diff : 0.0;
        double loss = (diff < 0) ? -diff : 0.0;

        // Applies Wilder's Smoothing Method
        avg_gain = ((avg_gain * (window - 1)) + gain) / window;
        avg_loss = ((avg_loss * (window - 1)) + loss) / window;

        // Prevents division by zero if the stock never went down
        if (avg_loss == 0) {
            out_ptr[r * cols + col_idx] = 100.0;
        } else {
            // Standard RSI Formula
            out_ptr[r * cols + col_idx] = 100.0 - (100.0 / (1.0 + (avg_gain / avg_loss)));
        }
    }
}

// Calculates the Moving Average Convergence Divergence
void macd(double* in_ptr, double* out_ptr, int rows, int cols, int col_idx, int fast_window, int slow_window) {
    // Calculates the weighting multipliers dynamically
    double k_fast = 2.0 / (fast_window + 1.0);
    double k_slow = 2.0 / (slow_window + 1.0);

    // Initializes both EMAs with the stock's day 1 closing price
    double ema_fast = in_ptr[col_idx];
    double ema_slow = in_ptr[col_idx];
    
    // Day 0 MACD is 0.0 because the fast and slow EMAs are identical
    out_ptr[col_idx] = 0.0;

    // Loops through the rest of the days to build the MACD line
    for (int r = 1; r < rows; ++r) {
        double price = in_ptr[r * cols + col_idx];
        
        ema_fast = (price - ema_fast) * k_fast + ema_fast;
        ema_slow = (price - ema_slow) * k_slow + ema_slow;
        
        out_ptr[r * cols + col_idx] = ema_fast - ema_slow; 
    }
}
void generate_signals(double* price_ptr, double* sma_ptr, double* signal_ptr, int rows, int columns, int index) {
    for (int r = 0; r < rows; ++r) {
        int memory_index = (r * columns) + index;

        double todays_price = price_ptr[memory_index];
        double todays_sma = sma_ptr[memory_index];

        // If price is greater than sma then BUY
        if (todays_price > todays_sma) {
            signal_ptr[memory_index] = 1.0;
        }
        // If price is less than sma then SELL
        else if (todays_price < todays_sma) {
            signal_ptr[memory_index] = -1.0;
        }
        // If price is equal to sma then do nothing
        else {
            signal_ptr[memory_index] = 0.0;
        }
    }
}

// Calculates the rolling volatility (standard deviation of daily returns) for a specific column
void rolling_volatility(double* in_ptr, double* out_ptr, int rows, int cols, int col_idx, int window) {
    for (int r = 0; r < rows; ++r) {
        
        // Day 0 has no previous day to calculate a return so is set a safe non-zero default
        if (r < 1) {
            out_ptr[r * cols + col_idx] = 0.001;
            continue;
        }

        // Determines the start index of the lookback window to prevent out-of-bounds memory access
        int start_idx = (r - window > 0) ? (r - window) : 0;
        int count = r - start_idx;

        // Calculates the mean daily return over the lookback window
        double sum_returns = 0.0;
        for (int i = start_idx + 1; i <= r; ++i) {
            double prev_price = in_ptr[(i - 1) * cols + col_idx];
            double curr_price = in_ptr[i * cols + col_idx];
            double daily_return = (curr_price - prev_price) / prev_price;
            sum_returns += daily_return;
        }
        double mean_return = sum_returns / count;

        // Calculates the variance (sum of squared deviations from the mean)
        double sum_variance = 0.0;
        for (int i = start_idx + 1; i <= r; ++i) {
            double prev_price = in_ptr[(i - 1) * cols + col_idx];
            double curr_price = in_ptr[i * cols + col_idx];
            double daily_return = (curr_price - prev_price) / prev_price;
            
            sum_variance += (daily_return - mean_return) * (daily_return - mean_return);
        }

        // Calculates the standard deviation
        double variance = sum_variance / count;
        double volatility = std::sqrt(variance);

        // Stores the result and applies a 0.001 floor to prevent downstream division-by-zero errors
        out_ptr[r * cols + col_idx] = (volatility > 0.001) ? volatility : 0.001;
    }
}