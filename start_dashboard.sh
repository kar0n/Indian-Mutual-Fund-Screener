#!/bin/bash
# Exit on any error
set -e

echo "===================================================="
echo "Starting IMF Screener - Indian Mutual Fund Screener"
echo "===================================================="

# Activate virtual environment
if [ -d "mf_quant_env" ]; then
    echo "Activating virtual environment..."
    source mf_quant_env/bin/activate
else
    echo "Error: Virtual environment 'mf_quant_env' not found. Please create it first."
    exit 1
fi

# Run data compiler
echo "Running data compiler (fetching fresh universe & calculating metrics)..."
python3 generate_data.py

# Check if JSON database was generated
if [ ! -f "mf_universe_data.json" ]; then
    echo "Error: Failed to generate mf_universe_data.json. Dashboard launch aborted."
    exit 1
fi

# Start local server and store PID
echo "Starting local workstation server on port 8000..."
python3 -m http.server 8000 > /dev/null 2>&1 &
SERVER_PID=$!

# Define cleanup function
cleanup() {
    echo ""
    echo "Shutting down local workstation server (PID: $SERVER_PID)..."
    kill $SERVER_PID 2>/dev/null || true
    echo "Shutdown complete."
    exit 0
}

# Trap INT and TERM signals to cleanup server
trap cleanup INT TERM

# Launch browser
echo "Launching default web browser to http://localhost:8000..."
# Determine OS
case "$OSTYPE" in
  darwin*)  open "http://localhost:8000" ;;
  linux*)   xdg-open "http://localhost:8000" ;;
  msys*)    start "http://localhost:8000" ;;
  *)        echo "Please open http://localhost:8000 in your browser manually." ;;
esac

echo "===================================================="
echo "Workstation is active. Press Ctrl+C to terminate."
echo "===================================================="

# Keep script running to allow Ctrl+C cleanup
while true; do
    sleep 1
done
