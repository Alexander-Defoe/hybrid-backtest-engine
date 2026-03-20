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

PYBIND11_MODULE(my_cpp_module, m) {
    m.doc() = "C++ Multithreaded SMA Calculator";
    m.def("calculate_smas", &calculate_smas, "Calculates SMA matrix"); 
}