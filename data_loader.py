"""Data Ingestion layer for fetching raw financial data streams with caching."""

import datetime
import logging
import re
from typing import Dict, List, Optional, Tuple
import pandas as pd
import requests
import streamlit as st
import yfinance as yf
import config

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
                    if "direct" in name_lower and "growth" in name_lower:
                        category_map[current_category].append({
                            "code": scheme_code,
                            "name": scheme_name
                        })

        return category_map


class DataLoader:
    """Retrieves and normalizes baseline pricing data from external endpoints with caching protocols."""

    @staticmethod
    @st.cache_data(ttl=86400)  # Cache index calculations for 24 hours
    def fetch_benchmark_returns(ticker: str, years: int) -> pd.DataFrame:
        """Downloads benchmark time-series and evaluates daily percentage variance."""
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=years * 365)
        
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        except Exception as e:
            logging.error(f"Failed to download benchmark return data for {ticker}: {e}")
            return pd.DataFrame(columns=["Bench_Return"])
            
        if df is None or df.empty:
            logging.error(f"No benchmark return data retrieved for {ticker}")
            return pd.DataFrame(columns=["Bench_Return"])
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]
            
        if "Close" not in df.columns:
            logging.error(f"Close price column missing in downloaded data for {ticker}")
            return pd.DataFrame(columns=["Bench_Return"])
            
        df = df[["Close"]].copy()
        df.columns = ["Benchmark_Close"]
        df["Bench_Return"] = df["Benchmark_Close"].pct_change()
        return df[["Bench_Return"]]

    @staticmethod
    @st.cache_data(ttl=43200)  # Cache raw scheme NAV files for 12 hours
    def fetch_fund_returns(scheme_code: str) -> Optional[pd.DataFrame]:
        """Pulls clean historical NAV time-series arrays from open api layers."""
        url = f"{config.MF_API_BASE_URL}{scheme_code}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        try:
            res = requests.get(url, headers=headers, timeout=10)
            data = res.json()
            if "data" not in data or not data["data"]:
                return None

            df = pd.DataFrame(data["data"])
            df["nav"] = pd.to_numeric(df["nav"])
            df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
            df = df.sort_values("date").set_index("date")
            df["Fund_Return"] = df["nav"].pct_change()
            return df[["Fund_Return"]]
        except Exception:
            return None

    @staticmethod
    @st.cache_data(ttl=86400)  # Cache sovereign interest logs for 24 hours
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