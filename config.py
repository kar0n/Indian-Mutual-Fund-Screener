"""Centralized configuration profiles for the Mutual Fund Screener."""

# Systemic Endpoint Configurations
AMFI_MASTER_URL = "https://portal.amfiindia.com/spages/NAVAll.txt"
MF_API_BASE_URL = "https://api.mfapi.in/mf/"
RISK_FREE_RATE_API = "https://techfanetechnologies.github.io/risk_free_interest_rate/RiskFreeInterestRate.json"

# Quantitative Analytics Benchmarks
DEFAULT_BENCHMARK_TICKER = "^NSEI"      # Nifty 50 Total Return Ticker
DEFAULT_BENCHMARK_LABEL = "Nifty 50 Index"
FALLBACK_RISK_FREE_RATE = 0.0675        # Backup Yield (~6.75%)
TRADING_DAYS_PER_YEAR = 252
LOOKBACK_WINDOW_YEARS = 3

# Execution Constraints
MAX_CONCURRENT_WORKERS = 10

# Dynamic Benchmark Mappings
CATEGORY_BENCHMARK_MAP = {
    "Equity Scheme - Small Cap Fund": {"id": "148519", "label": "Nippon Smallcap 250 Proxy"},
    "Equity Scheme - Mid Cap Fund": {"id": "148520", "label": "Nippon Midcap 150 Proxy"}
}