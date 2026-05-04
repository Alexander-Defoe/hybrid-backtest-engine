from setuptools import setup, Extension
import pybind11

ext_modules = [
    Extension(
        'my_cpp_module', 
        # Point explicitly to the C++ files in your engine folder
        sources=['engine/main.cpp', 'engine/indicators.cpp'], 
        include_dirs=[pybind11.get_include(), 'engine'], # Added 'engine' to include dirs for your .hpp file
        language='c++',
        extra_compile_args=['-std=c++11', '-O3']
    ),
]

setup(
    name='my_cpp_module',
    ext_modules=ext_modules,
)