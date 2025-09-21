#!/bin/bash

# OpenDrone Server and Binding Test Runner
# This script starts the drone server and runs the binding test

set -e  # Exit on any error

echo "=================================================="
echo "OpenDrone Server and Binding Test"
echo "=================================================="

# Function to cleanup background processes
cleanup() {
    echo -e "\nCleaning up..."
    if [ ! -z "$SERVER_PID" ]; then
        echo "Stopping server (PID: $SERVER_PID)..."
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
    fi
    echo "Cleanup complete."
}

# Set trap to cleanup on script exit
trap cleanup EXIT INT TERM

# Start the server in background
echo "Starting drone server..."
python3 server.py &
SERVER_PID=$!
echo "Server started with PID: $SERVER_PID"

# Wait a moment for server to initialize
echo "Waiting for server to initialize..."
sleep 3

# Check if server is still running
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "ERROR: Server failed to start or crashed"
    exit 1
fi

echo "Server is running, starting binding test..."
echo "--------------------------------------------------"

# Run the binding test
python3 test_bind.py

# Capture test exit code
TEST_EXIT_CODE=$?

echo "--------------------------------------------------"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✓ BINDING TEST PASSED"
else
    echo "✗ BINDING TEST FAILED"
fi

echo "=================================================="

# Exit with test result
exit $TEST_EXIT_CODE