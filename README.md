# MF-Screener

Indian Mutual Fund Quant Engine - A vectorized financial analytics engine for mutual fund screening and risk-adjusted analysis.

## Project Structure

```
MF-Screener/
├── config.py              # Centralized configuration, baselines, and constants
├── data_loader.py         # Network I/O, AMFI parsing, and Yahoo Finance data streams
├── analytics.py           # Vectorized financial engineering and risk analytics engine
├── ui.py                  # Streamlit web dashboard interface
├── main.py                # Application execution entry point
├── requirements.txt       # Declared Python environment dependencies
├── run_isolated.sh        # Isolated environment setup and launcher
└── README.md              # Project documentation
```

## Overview

MF-Screener provides a comprehensive toolkit for analyzing and screening Indian mutual funds using:
- Real-time market data from Yahoo Finance
- AMFI (Association of Mutual Funds in India) data parsing
- Vectorized financial analytics for efficient computation
- Interactive Streamlit web-based dashboard interface
- Risk-adjusted performance screening and analysis

## Components

### config.py
Centralized configuration file containing:
- Application settings and constants
- Baseline parameters for financial calculations
- Configuration presets

### data_loader.py
Handles all data acquisition:
- Network I/O operations
- AMFI mutual fund data parsing
- Yahoo Finance API integration
- Data stream management

### analytics.py
Core financial analytics engine:
- Vectorized calculations using NumPy
- Risk metrics and performance analytics
- Portfolio analysis tools
- Financial engineering computations

### ui.py
Interactive Streamlit web interface:
- Real-time risk-adjusted screener dashboard
- Data visualization and performance metrics
- Portfolio analysis interface
- User-friendly results presentation

### main.py
Streamlit application entry point for the web dashboard.

## Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd MF-Screener
```

2. Make the script executable:
```bash
chmod +x run_isolated.sh
```

3. Run the project:
```bash
./run_isolated.sh
```

The script will automatically:
- Create an isolated Python virtual environment (`mf_quant_env`)
- Install all dependencies from `requirements.txt`
- Verify Streamlit installation
- Launch the Streamlit web dashboard at `http://localhost:8501`
- Prompt to clean up the environment when finished

That's it! The dashboard will open in your default browser.

## Requirements

Python 3.7+ with dependencies listed in `requirements.txt`, including:
- **streamlit** - Web dashboard framework
- **pandas & numpy** - Data manipulation and vectorized analytics
- Financial analysis libraries for AMFI and Yahoo Finance integration

See `requirements.txt` for complete dependency specifications.

## Features

- 🎯 **Risk-Adjusted Screening** - Filter and rank mutual funds by risk-adjusted returns
- 📊 **Real-Time Dashboard** - Interactive web-based interface with live data
- 🇮🇳 **AMFI Data** - Direct integration with Association of Mutual Funds in India
- 📈 **Performance Analytics** - Comprehensive financial metrics and analytics
- 🚀 **Isolated Environment** - Easy setup with automatic dependency management

## System Requirements

- macOS, Linux, or Windows
- Python 3.7 or higher
- 2GB RAM minimum
- Internet connection for data fetching
