#!/bin/bash

# Run all tests for TrekBasic - stop at first error
set -e  # Exit on any error

echo "Running TrekBasic Test Suite"
echo "============================"

echo ""
echo "1. Running unit tests..."
python -m unittest discover -s . -p "test_*.py" -v

echo ""
echo "2. Running BASIC interpreter test suite..."
python test_suite/run_tests.py

echo ""
echo "3. Running LLVM compiler test suite..."
python test_suite/run_llvm_tests.py

echo ""
echo "All tests passed! ✅" 