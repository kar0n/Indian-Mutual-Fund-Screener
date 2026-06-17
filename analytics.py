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

        # Calculate Net Alpha (Note: raw Alpha calculated from NAV is already net of expenses.
        # Subtracting Expense Ratio again would be a double deduction.)
        df["Net Alpha (%)"] = df["Alpha (3Y)"]

        # 1. Define Category Weightings Map (Dynamic Weighting by Mandate)
        cat_name_lower = category_name.lower()
        if "hybrid" in cat_name_lower or "balanced advantage" in cat_name_lower or "dynamic asset" in cat_name_lower:
            w = {"roll": 0.25, "ir": 0.25, "alpha": 0.15, "dc": 0.35}
        elif "debt" in cat_name_lower or "liquid" in cat_name_lower or "arbitrage" in cat_name_lower:
            w = {"roll": 0.35, "ir": 0.20, "alpha": 0.05, "dc": 0.40}
        elif "small cap" in cat_name_lower or "mid cap" in cat_name_lower:
            w = {"roll": 0.20, "ir": 0.25, "alpha": 0.35, "dc": 0.20}
        else:
            w = {"roll": 0.25, "ir": 0.25, "alpha": 0.25, "dc": 0.25}

        # 2. Manager Tenure Lookup Map (Top Indian Mutual Funds)
        MANAGER_TENURE_MAP = {
            "122639": 13.0,  # Parag Parikh Flexi Cap Fund
            "118955": 4.0,   # HDFC Flexi Cap Fund
            "118968": 4.0,   # HDFC Balanced Advantage Fund
            "118989": 19.0,  # HDFC Mid-Cap Opportunities Fund
            "119609": 14.0,  # SBI Equity Hybrid Fund
            "120586": 8.0,   # ICICI Prudential Large Cap (Bluechip)
            "118778": 9.0,   # Nippon India Small Cap (Growth)
            "118777": 9.0,   # Nippon India Small Cap (Bonus)
            "120377": 16.0,  # ICICI Prudential Balanced Advantage
            "119771": 12.0,  # Kotak Arbitrage Fund
            "120323": 14.0,  # ICICI Prudential Value Discovery
            "119775": 14.0,  # Kotak Midcap Fund
            "119598": 2.0,   # SBI Large Cap Fund
            "118650": 19.0,  # Nippon India Multi Cap (Growth)
            "118651": 19.0,  # Nippon India Multi Cap (Bonus)
            "118632": 19.0,  # Nippon India Large Cap (Growth)
            "118633": 19.0,  # Nippon India Large Cap (Bonus)
            "120251": 14.0,  # ICICI Prudential Equity & Debt
            "120166": 14.0,  # Kotak Flexicap Fund
            "119835": 8.0,   # SBI Contra Fund
            "119779": 0.8,   # SBI Small Cap Fund (Transition Penalty)
        }

        ratings = []
        sub_roll_list = []
        sub_ir_list = []
        sub_alpha_list = []
        sub_dc_list = []
        tenure_list = []
        tenure_adjustment_list = []
        aum_adjustment_list = []

        for idx, row in df.iterrows():
            # 1. Performance Consistency
            r3y_roll = row["3Y Rolling Return (%)"]
            if pd.notna(r3y_roll) and not np.isnan(r3y_roll):
                diff = r3y_roll - category_avg_rolling_3y
                # Continuous interpolation: -10.0% -> 0.0, -5.0% -> 1.25, 0.0% -> 2.5, 5.0% -> 3.75, 10.0% -> 5.0
                # Widen bounds to avoid compression at the top, allowing true outperformers to stand out.
                raw_roll = float(np.interp(diff, [-10.0, -5.0, 0.0, 5.0, 10.0], [0.0, 1.25, 2.5, 3.75, 5.0]))
            else:
                raw_roll = 2.5

            # 2. Information Ratio
            ir3y = row["Information Ratio (3Y)"]
            if pd.notna(ir3y) and not np.isnan(ir3y):
                # Continuous interpolation: -0.5 -> 0.0, 0.0 -> 1.25, 0.5 -> 2.5, 1.0 -> 3.75, 2.0 -> 5.0
                # Widen bounds to 2.0 to reward exceptional risk-adjusted active managers.
                raw_ir = float(np.interp(ir3y, [-0.5, 0.0, 0.5, 1.0, 2.0], [0.0, 1.25, 2.5, 3.75, 5.0]))
            else:
                raw_ir = 2.5

            # 3. Net Alpha
            net_alpha = row["Net Alpha (%)"]
            if pd.notna(net_alpha) and not np.isnan(net_alpha):
                # Continuous interpolation: -5.0% -> 0.0, 0.0% -> 1.25, 4.0% -> 2.5, 8.0% -> 3.75, 15.0% -> 5.0
                # Widen bounds to 15% to accommodate high active alpha segments in Small/Mid cap spaces.
                raw_alpha = float(np.interp(net_alpha, [-5.0, 0.0, 4.0, 8.0, 15.0], [0.0, 1.25, 2.5, 3.75, 5.0]))
            else:
                raw_alpha = 2.5

            # 4. Downside Capture
            dc3y = row["Downside Capture (3Y)"]
            if pd.notna(dc3y) and not np.isnan(dc3y):
                # Continuous interpolation (smaller is better): 80% -> 5.0, 95% -> 3.75, 100% -> 3.125, 110% -> 1.875, 120% -> 0.0
                raw_dc = float(np.interp(dc3y, [80.0, 95.0, 100.0, 110.0, 120.0], [5.0, 3.75, 3.125, 1.875, 0.0]))
            else:
                raw_dc = 2.5

            # Compute weighted contributions out of 5 stars
            roll_contrib = raw_roll * w["roll"]
            ir_contrib = raw_ir * w["ir"]
            alpha_contrib = raw_alpha * w["alpha"]
            dc_contrib = raw_dc * w["dc"]

            sub_roll_list.append(round(roll_contrib, 4))
            sub_ir_list.append(round(ir_contrib, 4))
            sub_alpha_list.append(round(alpha_contrib, 4))
            sub_dc_list.append(round(dc_contrib, 4))

            total_score = roll_contrib + ir_contrib + alpha_contrib + dc_contrib

            # Apply Progressive AUM Adjustments
            aum_val = row["AUM (Cr)"]
            aum_adj = 0.0
            
            is_mid_or_small = "mid cap" in cat_name_lower or "small cap" in cat_name_lower
            is_liquid_or_debt = "debt" in cat_name_lower or "liquid" in cat_name_lower or "arbitrage" in cat_name_lower
            is_flexi_or_multi = "flexi cap" in cat_name_lower or "multi cap" in cat_name_lower
            is_large_or_hybrid = "large cap" in cat_name_lower or "hybrid" in cat_name_lower or "balanced advantage" in cat_name_lower
            
            if pd.notna(aum_val) and not np.isnan(aum_val):
                if is_mid_or_small:
                    if "small cap" in cat_name_lower and aum_val > 15000:
                        # Starts at 15k Cr, increases linearly to max -0.75 penalty at 30k Cr
                        aum_adj = max(-0.75, -((aum_val - 15000) / 15000) * 0.75)
                    elif "mid cap" in cat_name_lower and aum_val > 25000:
                        # Starts at 25k Cr, increases linearly to max -0.75 penalty at 50k Cr
                        aum_adj = max(-0.75, -((aum_val - 25000) / 25000) * 0.75)
                elif is_flexi_or_multi:
                    if aum_val > 35000:
                        # Starts at 35k Cr, increases linearly to max -0.50 penalty at 70k Cr
                        aum_adj = max(-0.50, -((aum_val - 35000) / 35000) * 0.50)
                elif is_liquid_or_debt:
                    if aum_val > 30000:
                        # Starts at 30k Cr, increases linearly to max +0.25 bonus at 60k Cr
                        aum_adj = min(0.25, ((aum_val - 30000) / 30000) * 0.25)
                elif is_large_or_hybrid:
                    if aum_val > 20000:
                        # Starts at 20k Cr, increases linearly to max +0.25 bonus at 40k Cr
                        aum_adj = min(0.25, ((aum_val - 20000) / 20000) * 0.25)
            
            total_score += aum_adj
            aum_adjustment_list.append(round(aum_adj, 4))

            # Apply Manager Tenure Details (Isolated from the actual rating score calculation)
            scheme_code = str(row["code"])
            tenure = MANAGER_TENURE_MAP.get(scheme_code, 3.5)  # Default to neutral 3.5 years
            tenure_list.append(tenure)
            
            # Calculate what the tenure adjustment would have been for frontend compatibility
            tenure_adj = 0.0
            if tenure < 3.0:
                # Continuous scale from -0.5 at 0.0 years to 0.0 at 3.0 years
                tenure_adj = -0.5 * (1.0 - (tenure / 3.0))
            elif tenure > 3.0:
                # Continuous scale from 0.0 at 3.0 years to +0.25 at 8.0+ years
                tenure_adj = min(0.25, 0.25 * ((tenure - 3.0) / 5.0))
                
            # Note: We append to the list for UI display, but we DO NOT add it to total_score
            tenure_adjustment_list.append(round(tenure_adj, 4))

            # Cap the final score between 0.5 and 5.0 stars
            final_rating_score = min(5.0, max(0.5, total_score))
            ratings.append(final_rating_score)

        df["Rating_Score"] = ratings
        df["Sub_Rating_Performance"] = sub_roll_list
        df["Sub_Rating_IR"] = sub_ir_list
        df["Sub_Rating_Alpha"] = sub_alpha_list
        df["Sub_Rating_Protection"] = sub_dc_list
        df["Manager_Tenure_Years"] = tenure_list
        df["Manager_Tenure_Adj"] = tenure_adjustment_list
        df["AUM_Adj"] = aum_adjustment_list

        def to_stars(score):
            if np.isnan(score):
                return "N/A"
            full_stars = int(score)
            half_star = "½" if (score - full_stars) >= 0.25 else ""
            if full_stars == 0 and not half_star:
                return "½"  # minimum score representation
            return "★" * full_stars + half_star

        df["Rating"] = df["Rating_Score"].apply(to_stars)
        return df