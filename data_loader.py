"""Data Ingestion layer for fetching raw financial data streams with caching."""

import datetime
import logging
import re
import time
from typing import Dict, List, Optional, Tuple
import pandas as pd
import requests
import yfinance as yf
import config

# Optional Streamlit support with dummy cache fallback when run outside Streamlit or without it installed
try:
    import streamlit as st
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    if get_script_run_ctx() is None:
        def cache_data_dummy(*args, **kwargs):
            return lambda func: func
        st_cache = cache_data_dummy
    else:
        st_cache = st.cache_data
except ImportError:
    st = None
    def cache_data_dummy(*args, **kwargs):
        return lambda func: func
    st_cache = cache_data_dummy

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class AmfiRegistry:
    """Manages parsing of the statutory real-time AMFI scheme registry."""

    @classmethod
    def fetch_active_universe(cls) -> Dict[str, List[Dict[str, str]]]:
        """Downloads the active AMFI master record and classifies funds into dynamic categories."""
        logging.info("Querying AMFI statutory endpoint for active fund classifications...")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Connection": "keep-alive"
        }

        try:
            response = requests.get(config.AMFI_MASTER_URL, headers=headers, timeout=15)
            response.raise_for_status()
        except Exception as e:
            logging.error(f"Failed to fetch AMFI universe master file: {e}")
            return {}

        lines = response.text.split("\n")
        category_map: Dict[str, List[Dict[str, str]]] = {}
        current_category: Optional[str] = None
        
        category_regex = re.compile(r"Open Ended Schemes\s*\(\s*([\w\s]+?Scheme)\s*-\s*(.+?)\s*\)")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            cat_match = category_regex.search(line)
            if cat_match:
                scheme_type = cat_match.group(1).strip()
                category_name = cat_match.group(2).strip()
                current_category = f"{scheme_type} - {category_name}"
                if current_category not in category_map:
                    category_map[current_category] = []
                continue

            if ";" in line and current_category:
                parts = line.split(";")
                if len(parts) >= 4:
                    scheme_code = parts[0].strip()
                    scheme_name = parts[3].strip()

                    name_lower = scheme_name.lower()
                    if "direct" in name_lower and "growth" in name_lower and "bonus" not in name_lower:
                        category_map[current_category].append({
                            "code": scheme_code,
                            "name": scheme_name
                        })

        return category_map


class DataLoader:
    """Retrieves and normalizes baseline pricing data from external endpoints with caching protocols."""

    @staticmethod
    @st_cache(ttl=86400)  # Cache index calculations for 24 hours
    def fetch_benchmark_returns(ticker: str, years: int) -> pd.DataFrame:
        """Downloads benchmark time-series and evaluates daily percentage variance with index fund fallback."""
        # If the ticker is a numeric scheme code, route to the Mutual Fund Proxy API instead of Yahoo Finance
        if ticker.isdigit():
            logging.info(f"Using Mutual Fund Proxy (Scheme {ticker}) as benchmark.")
            proxy_df = DataLoader.fetch_fund_returns(ticker)
            if proxy_df is not None and not proxy_df.empty:
                proxy_df = proxy_df.copy()
                proxy_df.columns = ["nav", "Bench_Return"]
                return proxy_df[["Bench_Return"]]
            else:
                logging.error(f"Failed to fetch proxy benchmark {ticker}.")
                return pd.DataFrame(columns=["Bench_Return"])
                
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=years * 365)
        
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        except Exception as e:
            logging.error(f"Failed to download benchmark return data for {ticker}: {e}")
            df = None
            
        if df is not None and not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] for col in df.columns]
            
            if "Close" in df.columns:
                df = df[["Close"]].copy()
                df.columns = ["Benchmark_Close"]
                df["Bench_Return"] = df["Benchmark_Close"].pct_change()
                return df[["Bench_Return"]]
        
        # Fallback to UTI Nifty 50 Index Fund NAV returns via api.mfapi.in mirror
        logging.warning(f"Yahoo Finance failed for {ticker}. falling back to UTI Nifty 50 Index Fund (120716) NAV returns...")
        try:
            fallback_df = DataLoader.fetch_fund_returns("120716")
            if fallback_df is not None and not fallback_df.empty:
                fallback_df = fallback_df.copy()
                fallback_df.columns = ["nav", "Bench_Return"]
                return fallback_df[["Bench_Return"]]
        except Exception as fe:
            logging.error(f"Index fund fallback failed: {fe}")
            
        return pd.DataFrame(columns=["Bench_Return"])

    @staticmethod
    @st_cache(ttl=43200)  # Cache raw scheme NAV files for 12 hours
    def fetch_fund_returns(scheme_code: str) -> Optional[pd.DataFrame]:
        """Pulls clean historical NAV time-series arrays from open api layers with backoff retries."""
        url = f"{config.MF_API_BASE_URL}{scheme_code}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        retries = 3
        for attempt in range(retries):
            try:
                res = requests.get(url, headers=headers, timeout=15)
                if res.status_code == 200:
                    data = res.json()
                    if "data" not in data or not data["data"]:
                        return None
                    df = pd.DataFrame(data["data"])
                    df["nav"] = pd.to_numeric(df["nav"])
                    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
                    df = df.sort_values("date").set_index("date")
                    df["Fund_Return"] = df["nav"].pct_change()
                    return df[["nav", "Fund_Return"]]
            except Exception as e:
                logging.warning(f"NAV fetch attempt {attempt+1} failed for scheme {scheme_code}: {e}")
            if attempt < retries - 1:
                time.sleep(0.5 * (attempt + 1))
        return None

    @staticmethod
    @st_cache(ttl=86400)  # Cache sovereign interest logs for 24 hours
    def fetch_live_risk_free_rate() -> Tuple[float, str]:
        """Dynamically pulls the latest 91-Day Sovereign India T-Bill rate from live market logs."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        try:
            res = requests.get(config.RISK_FREE_RATE_API, headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    for item in data:
                        sec_name = item.get("GovernmentSecurityName", "")
                        if sec_name.strip().lower() == "91 day t-bills":
                            rate = float(item["Percent"]) / 100
                            return rate, "Live"
        except Exception as e:
            logging.error(f"Error fetching live risk free rate: {e}")
        return config.FALLBACK_RISK_FREE_RATE, "Baseline"

    @staticmethod
    @st_cache(ttl=86400)  # Cache qualitative data for 24 hours
    def fetch_fund_details(scheme_code: str) -> Optional[Dict]:
        """Pulls comprehensive holdings, AUM, expense ratio, and manager info from FinAPI Upvaly with backoff retries."""
        url = f"https://finapi.upvaly.com/api/mf/scheme-code/{scheme_code}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        retries = 3
        for attempt in range(retries):
            try:
                res = requests.get(url, headers=headers, timeout=12)
                if res.status_code == 200:
                    body = res.json()
                    if body.get("status") == "success" or body.get("statusCode") == 200:
                        return body.get("data")
            except Exception as e:
                logging.warning(f"Factsheet fetch attempt {attempt+1} failed for scheme {scheme_code}: {e}")
            if attempt < retries - 1:
                time.sleep(0.5 * (attempt + 1))
        return None