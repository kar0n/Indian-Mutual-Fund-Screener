#!/bin/bash

# Configuration
ENV_DIR="./mf_quant_env"
PROJECT_NAME="Indian Mutual Fund Quant Engine"

echo "========================================================="
echo "       $PROJECT_NAME - RUNTIME INTERFACE "
echo "========================================================="

# Validate requirements file existence before booting environment
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found in the current directory."
    echo "Please ensure you are running this script from the root of the project."
    exit 1
fi

# Initialize or verify environment setup
if [ -d "$ENV_DIR" ]; then
    echo "🔄 Existing quantitative virtual environment detected. Booting..."
    source $ENV_DIR/bin/activate
    echo "📦 Verifying state configuration / syncing incremental dependencies..."
    # Running pip here checks for missing packages without downloading existing ones again
    pip install -r requirements.txt > /dev/null 2>&1
else
    echo "🚀 Spinning up isolated quantitative environment at $ENV_DIR..."
    python3 -m venv $ENV_DIR
    source $ENV_DIR/bin/activate
    
    echo "📦 Upgrading pip and loading vectorized analytical packages..."
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt > /dev/null 2>&1
fi

# Fail-safe guardrail check to ensure environment pathing linked properly
if ! command -v streamlit &> /dev/null; then
    echo "❌ Error: Streamlit core engine binary could not be resolved."
    echo "Attempting force-reinstallation of package layer..."
    pip install streamlit
fi

echo "📊 Launching Risk-Adjusted Screener Web Dashboard UI..."
echo "---------------------------------------------------------"
streamlit run main.py
echo "---------------------------------------------------------"

# Clean disconnect from virtual environment upon main app exit
deactivate

# Interactive Prompt for workspace storage maintenance
echo ""
read -p "❓ Do you want to purge the virtual environment from disk? (y/n): " choice
if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
    echo "🧹 Cleaning up... Removing local virtual environment libraries."
    rm -rf $ENV_DIR
    echo "✨ Done! Workspace storage has been cleared."
else
    echo "💾 Keeping virtual environment intact for subsequent analytical runs."
fi