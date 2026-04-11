#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <vector>
#include <thread>
#include "indicators.hpp"

namespace py = pybind11;

// Takes the numpy array and window size from python
py::array_t<double> calculate_smas(py::array_t<double> input_matrix, int window) {
    // Creates a buffer to securely access the memory location of the numpy array without making a copy
    auto buf = input_matrix.request();
    // Creates a pointer to the first number in that data
    double* in_ptr = (double*) buf.ptr;
    
    // Gets the dimensions of the grid
    int rows = buf.shape[0];
    int cols = buf.shape[1];

    // Creates a new numpy array the same size as the grid
    py::array_t<double> output_matrix({rows, cols});
    double* out_ptr = (double*) output_matrix.request().ptr;

    // Vector holding all active threads
    std::vector<std::thread> threads;

    // Loops through every stock and creates a thread for it
    for (int i = 0; i < cols; ++i) {
        threads.push_back(std::thread(sma, in_ptr, out_ptr, rows, cols, i, window));
    }

    // Waits for all threads to finish before allowing main to continue
    for (auto& t : threads) {
        t.join();
    }

    // Returns the full 2D array back to Pythons memory
    return output_matrix;
}

// Python wrapper for the RSI
py::array_t<double> calculate_rsi(py::array_t<double> input_matrix, int window) {
    // Requests raw memory buffers from the Python numpy array
    auto buf = input_matrix.request();
    // Casts the 2D Python array into a flat 1D C++ pointer for processing speed
    double* in_ptr = (double*) buf.ptr;
    int rows = buf.shape[0];
    int cols = buf.shape[1];

    // Creates a new empty numpy array of the same size to hold the results
    py::array_t<double> output_matrix({rows, cols});
    double* out_ptr = (double*) output_matrix.request().ptr;

    // Creates a list to keep track of the active threads
    std::vector<std::thread> threads;
    
    // Loops through each stock and assigns it to its own thread
    for (int i = 0; i < cols; ++i) {
        // Passes the raw memory pointers and the specific column index to the function
        threads.push_back(std::thread(rsi, in_ptr, out_ptr, rows, cols, i, window));
    }

    // Waits for every single thread to finish its calculation
    for (auto& t : threads) {
        t.join();
    }
    
    // Returns the populated numpy array back to python
    return output_matrix;
}

// Python wrapper for the MACD
py::array_t<double> calculate_macd(py::array_t<double> input_matrix) {
    // Extracts the raw memory pointers from the numpy array
    auto buf = input_matrix.request();
    double* in_ptr = (double*) buf.ptr;
    int rows = buf.shape[0];
    int cols = buf.shape[1];

    // Allocates memory for the numpy array
    py::array_t<double> output_matrix({rows, cols});
    double* out_ptr = (double*) output_matrix.request().ptr;

    // Creates a thread for each stock to calculate the MACD concurrently
    std::vector<std::thread> threads;
    for (int i = 0; i < cols; ++i) {
        threads.push_back(std::thread(macd, in_ptr, out_ptr, rows, cols, i));
    }

    // Blocks python from continuing until all C++ threads have completed
    for (auto& t : threads) {
        t.join();
    }
    return output_matrix;
}

PYBIND11_MODULE(my_cpp_module, m) {
    m.doc() = "C++ Multithreaded Trading Indicators"; // Optional module docstring
    
    // Bind the C++ wrapper functions to Python-callable names
    m.def("calculate_smas", &calculate_smas, "Calculates SMA matrix"); 
    m.def("calculate_rsi", &calculate_rsi, "Calculates RSI matrix"); 
    m.def("calculate_macd", &calculate_macd, "Calculates MACD matrix"); 
}