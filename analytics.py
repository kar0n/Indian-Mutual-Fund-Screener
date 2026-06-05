"""Quantitative processing core for multi-timeframe risk-adjusted analysis."""

import concurrent.futures
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import config
from data_loader import DataLoader


class QuantEngine:
    """Computes trailing 1Y, 3Y, and 5Y horizons using vectorized matrix math."""

    def __init__(self, benchmark_ticker: str = config.DEFAULT_BENCHMARK_TICKER, risk_free_rate: float = config.FALLBACK_RISK_FREE_RATE):
        self.benchmark_df = DataLoader.fetch_benchmark_returns(benchmark_ticker, years=8)
        self.risk_free_rate = risk_free_rate

    def _slice_and_compute(self, df: pd.DataFrame, days: int) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float], Optional[float], Optional[float]]:
        """Slices a specific trailing trading day window and computes CAGR, risk, and CAPM metrics."""
        slice_df = df.tail(days)
        if len(slice_df) < (days * 0.85):
            return None, None, None, None, None, None

        # Calculate true compounded annualized returns (CAGR)
        compounded_return = (1 + slice_df["Fund_Return"]).prod() - 1
        compounded_bench_return = (1 + slice_df["Bench_Return"]).prod() - 1
        years = len(slice_df) / config.TRADING_DAYS_PER_YEAR

        ann_return = (1 + compounded_return) ** (1 / years) - 1 if compounded_return > -1.0 else -1.0
        bench_return = (1 + compounded_bench_return) ** (1 / years) - 1 if compounded_bench_return > -1.0 else -1.0

        # Annualized Volatility and Sharpe
        vol = slice_df["Fund_Return"].std() * np.sqrt(config.TRADING_DAYS_PER_YEAR)
        sharpe = (ann_return - self.risk_free_rate) / vol if vol > 0 else 0

        # Tracking Error and Information Ratio
        slice_df = slice_df.copy()
        slice_df["Active_Return"] = slice_df["Fund_Return"] - slice_df["Bench_Return"]
        tracking_error = slice_df["Active_Return"].std() * np.sqrt(config.TRADING_DAYS_PER_YEAR)
        info_ratio = (ann_return - bench_return) / tracking_error if tracking_error > 0 else 0

        # CAPM Beta and Alpha
        covariance = slice_df["Fund_Return"].cov(slice_df["Bench_Return"])
        bench_variance = slice_df["Bench_Return"].var()
        beta = covariance / bench_variance if bench_variance > 0 else 1.0
        alpha = ann_return - (self.risk_free_rate + beta * (bench_return - self.risk_free_rate))

        # Downside Capture Ratio
        negative_bench = slice_df[slice_df["Bench_Return"] < 0]
        if not negative_bench.empty:
            fund_neg_cum = (1 + negative_bench["Fund_Return"]).prod() - 1
            bench_neg_cum = (1 + negative_bench["Bench_Return"]).prod() - 1
            downside_capture = (fund_neg_cum / bench_neg_cum) * 100 if bench_neg_cum != 0 else 100.0
        else:
            downside_capture = 100.0

        return (
            round(ann_return * 100, 2),
            round(sharpe, 2),
            round(info_ratio, 2),
            round(beta, 2),
            round(alpha * 100, 2),
            round(downside_capture, 2)
        )

    def calculate_scheme_metrics(self, fund: Dict[str, str]) -> Optional[Dict]:
        """Maps out multi-horizon performance profiles for an individual asset blueprint."""
        fund_df = DataLoader.fetch_fund_returns(fund["code"])
        if fund_df is None:
            return None

        merged = fund_df.join(self.benchmark_df, how="inner").dropna()
        if merged.empty:
            return None

        # Compute Rolling Returns over whole history
        if len(merged) >= 252:
            merged["Rolling_1Y"] = (merged["nav"] / merged["nav"].shift(252)) - 1
            r1y_rolling = round(merged["Rolling_1Y"].mean() * 100, 2)
        else:
            r1y_rolling = np.nan

        if len(merged) >= 756:
            merged["Rolling_3Y"] = (merged["nav"] / merged["nav"].shift(756)) ** (252 / 756) - 1
            r3y_rolling = round(merged["Rolling_3Y"].mean() * 100, 2)
        else:
            r3y_rolling = np.nan

        if len(merged) >= 1260:
            merged["Rolling_5Y"] = (merged["nav"] / merged["nav"].shift(1260)) ** (252 / 1260) - 1
            r5y_rolling = round(merged["Rolling_5Y"].mean() * 100, 2)
        else:
            r5y_rolling = np.nan

        # Slice-based metrics
        res_1y = self._slice_and_compute(merged, 252)
        res_3y = self._slice_and_compute(merged, 756)
        res_5y = self._slice_and_compute(merged, 1260)

        if res_1y[0] is None:
            return None

        r1y, s1y, i1y, b1y, a1y, dc1y = res_1y
        r3y, s3y, i3y, b3y, a3y, dc3y = res_3y if res_3y[0] is not None else (np.nan, np.nan, np.nan, np.nan, np.nan, np.nan)
        r5y, s5y, i5y, b5y, a5y, dc5y = res_5y if res_5y[0] is not None else (np.nan, np.nan, np.nan, np.nan, np.nan, np.nan)

        # Fetch qualitative details
        details = DataLoader.fetch_fund_details(fund["code"])
        aum = np.nan
        expense_ratio = np.nan
        top10_weight = np.nan
        large_cap = np.nan
        mid_cap = np.nan
        small_cap = np.nan
        managers = "N/A"
        holdings_list = []
        
        if details:
            aum_str = details.get("aum")
            if aum_str:
                try:
                    aum = float(aum_str.replace(",", "").strip())
                except:
                    pass
            try:
                expense_ratio = float(details.get("expenseRatio", np.nan))
            except:
                pass
            portfolio = details.get("portfolio", {})
            concentration = portfolio.get("concentration", {})
            try:
                top10_weight = float(concentration.get("top10StocksWeight", np.nan))
            except:
                pass
            mcap = portfolio.get("marketCapWeightage", {})
            try:
                large_cap = float(mcap.get("largeCap", np.nan))
                mid_cap = float(mcap.get("midCap", np.nan))
                small_cap = float(mcap.get("smallCap", np.nan))
            except:
                pass
            mgr_val = details.get("schemeFundManagers")
            if isinstance(mgr_val, list):
                managers = ", ".join(mgr_val)
            elif isinstance(mgr_val, str):
                managers = mgr_val
                
            raw_holdings = details.get("holdings", [])
            for h in raw_holdings[:15]:
                holdings_list.append({
                    "name": h.get("name", ""),
                    "sector": h.get("sector", ""),
                    "weightage": h.get("weightage", "")
                })

        return {
            "code": fund["code"],
            "Fund Name": fund["name"],
            "1Y Return (%)": r1y,
            "3Y Return (%)": r3y,
            "5Y Return (%)": r5y,
            "Sharpe (3Y)": s3y,
            "Information Ratio (3Y)": i3y,
            "Beta (3Y)": b3y,
            "Alpha (3Y)": a3y,
            "Downside Capture (3Y)": dc3y,
            "1Y Rolling Return (%)": r1y_rolling,
            "3Y Rolling Return (%)": r3y_rolling,
            "5Y Rolling Return (%)": r5y_rolling,
            "AUM (Cr)": aum,
            "Expense Ratio (%)": expense_ratio,
            "Top 10 Stocks Weight (%)": top10_weight,
            "Large Cap (%)": large_cap,
            "Mid Cap (%)": mid_cap,
            "Small Cap (%)": small_cap,
            "Managers": managers,
            "Holdings": holdings_list
        }

    def process_category_concurrently(self, funds_list: List[Dict[str, str]], category_name: str = "") -> pd.DataFrame:
        """Dispatches calculations across parallel workers and computes dynamic ratings."""
        compiled_metrics = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=config.MAX_CONCURRENT_WORKERS) as executor:
            future_to_fund = {
                executor.submit(self.calculate_scheme_metrics, fund): fund for fund in funds_list
            }
            for future in concurrent.futures.as_completed(future_to_fund):
                result = future.result()
                if result:
                    compiled_metrics.append(result)

        df = pd.DataFrame(compiled_metrics)
        if df.empty:
            return df

        # Dynamic Scoring and Ratings
        category_avg_rolling_3y = df["3Y Rolling Return (%)"].mean()
        if np.isnan(category_avg_rolling_3y):
            category_avg_rolling_3y = 0.0

        # Calculate Net Alpha
        df["Net Alpha (%)"] = df["Alpha (3Y)"] - df["Expense Ratio (%)"].fillna(0)

        ratings = []
        for idx, row in df.iterrows():
            # 1. Performance Consistency (Rolling 3Y vs Category Average) - max 1.25
            r3y_roll = row["3Y Rolling Return (%)"]
            if pd.notna(r3y_roll) and not np.isnan(r3y_roll):
                diff = r3y_roll - category_avg_rolling_3y
                if diff >= 3.0:
                    roll_score = 1.25
                elif diff >= 0.0:
                    roll_score = 0.9375
                elif diff >= -3.0:
                    roll_score = 0.625
                elif diff >= -6.0:
                    roll_score = 0.3125
                else:
                    roll_score = 0.0
            else:
                roll_score = 0.625

            # 2. Information Ratio (Skill vs Luck) - max 1.25
            ir3y = row["Information Ratio (3Y)"]
            if pd.notna(ir3y) and not np.isnan(ir3y):
                if ir3y >= 1.0:
                    ir_score = 1.25
                elif ir3y >= 0.75:
                    ir_score = 0.9375
                elif ir3y >= 0.5:
                    ir_score = 0.625
                elif ir3y >= 0.0:
                    ir_score = 0.3125
                else:
                    ir_score = 0.0
            else:
                ir_score = 0.625

            # 3. Net Alpha (Risk-adjusted excess return net of expense ratio) - max 1.25
            net_alpha = row["Net Alpha (%)"]
            if pd.notna(net_alpha) and not np.isnan(net_alpha):
                if net_alpha >= 5.0:
                    alpha_score = 1.25
                elif net_alpha >= 2.5:
                    alpha_score = 0.9375
                elif net_alpha >= 0.0:
                    alpha_score = 0.625
                elif net_alpha >= -2.0:
                    alpha_score = 0.3125
                else:
                    alpha_score = 0.0
            else:
                alpha_score = 0.625

            # 4. Downside Capture Ratio (Capital protection) - max 1.25
            dc3y = row["Downside Capture (3Y)"]
            if pd.notna(dc3y) and not np.isnan(dc3y):
                if dc3y <= 80.0:
                    dc_score = 1.25
                elif dc3y <= 95.0:
                    dc_score = 0.9375
                elif dc3y <= 100.0:
                    dc_score = 0.78125
                elif dc3y <= 110.0:
                    dc_score = 0.46875
                else:
                    dc_score = 0.0
            else:
                dc_score = 0.625

            total_score = roll_score + ir_score + alpha_score + dc_score
            
            # Apply Qualitative Penalties (AUM and Concentration)
            cat_name_lower = category_name.lower()
            is_mid_or_small = "mid cap" in cat_name_lower or "small cap" in cat_name_lower
            
            if is_mid_or_small:
                # Penalty A: Bloated AUM check
                aum_val = row["AUM (Cr)"]
                if pd.notna(aum_val) and not np.isnan(aum_val):
                    if "small cap" in cat_name_lower and aum_val > 15000:
                        total_score = max(0.0, total_score - 0.5)
                    elif "mid cap" in cat_name_lower and aum_val > 25000:
                        total_score = max(0.0, total_score - 0.5)
                        
                # Penalty B: Concentration outside optimal 20%-45% check
                top10_val = row["Top 10 Stocks Weight (%)"]
                if pd.notna(top10_val) and not np.isnan(top10_val):
                    if top10_val < 20.0 or top10_val > 45.0:
                        total_score = max(0.0, total_score - 0.25)
                        
            ratings.append(total_score)

        df["Rating_Score"] = ratings

        def to_stars(score):
            if np.isnan(score):
                return "N/A"
            full_stars = int(score)
            half_star = "½" if (score - full_stars) >= 0.25 else ""
            if full_stars == 0 and not half_star:
                return "½" # minimum score representation
            return "⭐" * full_stars + half_star

        df["Rating"] = df["Rating_Score"].apply(to_stars)
        return df