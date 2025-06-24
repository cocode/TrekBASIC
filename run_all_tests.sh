#!/bin/bash

# Run all tests for TrekBasic - stop at first error
set -e  # Exit on any error

echo "Running TrekBasic Test Suite"
echo "============================"

# Initialize counters
UNIT_TESTS=0
INTERPRETER_TESTS=0
LLVM_TESTS=0

echo ""
echo "1. Running unit tests..."
UNIT_OUTPUT=$(python -m unittest discover -s . -p "test_*.py" -v 2>&1)
echo "$UNIT_OUTPUT"

# Extract number of unit tests (look for "Ran X tests")
UNIT_TESTS=$(echo "$UNIT_OUTPUT" | grep -o "Ran [0-9]* tests" | grep -o "[0-9]*" || echo "0")

# Check if unit tests passed
if echo "$UNIT_OUTPUT" | grep -q "FAILED ("; then
    UNIT_FAILURES=$(echo "$UNIT_OUTPUT" | grep "FAILED (" | tail -1)
    echo "❌ Unit tests FAILED: $UNIT_FAILURES"
    exit 1
elif echo "$UNIT_OUTPUT" | grep -q "OK$"; then
    echo "✅ Unit tests passed: $UNIT_TESTS tests"
else
    echo "❓ Unit test status unclear"
    exit 1
fi

echo ""
echo "2. Running BASIC interpreter test suite..."
python test_suite/run_tests.py

echo ""
echo "3. Running LLVM compiler test suite..."
python test_suite/run_llvm_tests.py

echo ""
echo "=================================="
echo "Test Summary:"
echo "  Unit tests:        $UNIT_TESTS"
echo "  Interpreter tests: $INTERPRETER_TESTS"
echo "  LLVM tests:        $LLVM_TESTS"
echo "  ─────────────────────────────"
echo "  Total tests:       $TOTAL_TESTS"
echo ""
echo "All tests passed! ✅" 