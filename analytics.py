"""Quantitative processing core for multi-timeframe risk-adjusted analysis."""

import concurrent.futures
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
import config
from data_loader import DataLoader


class QuantEngine:
    """Computes trailing 1Y, 3Y, and 5Y horizons using vectorized matrix math."""

    def __init__(self, benchmark_ticker: str = config.DEFAULT_BENCHMARK_TICKER, risk_free_rate: float = config.FALLBACK_RISK_FREE_RATE):
        self.benchmark_df = DataLoader.fetch_benchmark_returns(benchmark_ticker, years=5)
        self.risk_free_rate = risk_free_rate

    def _slice_and_compute(self, df: pd.DataFrame, days: int) -> tuple:
        """Slices a specific trailing trading day window to compute localized metrics."""
        slice_df = df.tail(days)
        if len(slice_df) < (days * 0.85):
            return None, None, None

        ann_return = slice_df["Fund_Return"].mean() * config.TRADING_DAYS_PER_YEAR
        bench_return = slice_df["Bench_Return"].mean() * config.TRADING_DAYS_PER_YEAR
        vol = slice_df["Fund_Return"].std() * np.sqrt(config.TRADING_DAYS_PER_YEAR)

        sharpe = (ann_return - self.risk_free_rate) / vol if vol > 0 else 0

        slice_df = slice_df.copy()
        slice_df["Active_Return"] = slice_df["Fund_Return"] - slice_df["Bench_Return"]
        tracking_error = slice_df["Active_Return"].std() * np.sqrt(config.TRADING_DAYS_PER_YEAR)
        info_ratio = (ann_return - bench_return) / tracking_error if tracking_error > 0 else 0

        return round(ann_return * 100, 2), round(sharpe, 2), round(info_ratio, 2)

    def calculate_scheme_metrics(self, fund: Dict[str, str]) -> Optional[Dict]:
        """Maps out multi-horizon performance profiles for an individual asset blueprint."""
        fund_df = DataLoader.fetch_fund_returns(fund["code"])
        if fund_df is None:
            return None

        merged = fund_df.join(self.benchmark_df, how="inner").dropna()
        if merged.empty:
            return None

        r1y, s1y, i1y = self._slice_and_compute(merged, 252)
        r3y, s3y, i3y = self._slice_and_compute(merged, 756)
        r5y, s5y, i5y = self._slice_and_compute(merged, 1260)

        if r1y is None:
            return None

        return {
            "Fund Name": fund["name"],
            "1Y Return (%)": r1y,
            "3Y Return (%)": r3y if r3y is not None else np.nan,
            "5Y Return (%)": r5y if r5y is not None else np.nan,
            "Sharpe (3Y)": s3y if s3y is not None else np.nan,
            "Information Ratio (3Y)": i1y if i3y is None else i3y,
        }

    def process_category_concurrently(self, funds_list: List[Dict[str, str]]) -> pd.DataFrame:
        """Dispatches calculations across parallel workers securely."""
        compiled_metrics = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=config.MAX_CONCURRENT_WORKERS) as executor:
            future_to_fund = {
                executor.submit(self.calculate_scheme_metrics, fund): fund for fund in funds_list
            }
            for future in concurrent.futures.as_completed(future_to_fund):
                result = future.result()
                if result:
                    compiled_metrics.append(result)

        return pd.DataFrame(compiled_metrics)