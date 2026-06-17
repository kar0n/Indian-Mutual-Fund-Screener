import json
import logging
import os
import pandas as pd
import numpy as np
import datetime

import config
from data_loader import AmfiRegistry, DataLoader
from analytics import QuantEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Target categories to compile (Curated list of top 12 key investment categories)
CATEGORIES_TO_COMPILE = [
    "Equity Scheme - Flexi Cap Fund",
    "Equity Scheme - Multi Cap Fund",
    "Equity Scheme - Large Cap Fund",
    "Equity Scheme - Mid Cap Fund",
    "Equity Scheme - Small Cap Fund",
    "Equity Scheme - Large & Mid Cap Fund",
    "Equity Scheme - ELSS",
    "Equity Scheme - Value Fund",
    "Equity Scheme - Contra Fund",
    "Hybrid Scheme - Aggressive Hybrid Fund",
    "Hybrid Scheme - Dynamic Asset Allocation or Balanced Advantage",
    "Hybrid Scheme - Arbitrage Fund",
    "Debt Scheme - Liquid Fund"
]

def main():
    logging.info("Starting Mutual Fund Quant Data Compiler...")
    
    # 1. Fetch live risk-free rate
    rfr_value, rfr_status = DataLoader.fetch_live_risk_free_rate()
    logging.info(f"Using Risk-Free Rate: {rfr_value*100:.2f}% ({rfr_status})")
    
    # 2. Fetch active universe
    universe = AmfiRegistry.fetch_active_universe()
    if not universe:
        logging.error("Failed to load AMFI universe. Aborting.")
        return
        
    # Load existing database for diffing manager changes
    old_db_lookup = {}
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mf_universe_data.json")
    if os.path.exists(output_path):
        try:
            with open(output_path, "r") as f:
                old_data = json.load(f)
                for old_cat, old_funds in old_data.get("categories", {}).items():
                    for f_rec in old_funds:
                        sc_code = str(f_rec.get("code"))
                        if sc_code:
                            old_db_lookup[sc_code] = {
                                "Managers": f_rec.get("Managers"),
                                "Manager_Changed_Recently": f_rec.get("Manager_Changed_Recently", False),
                                "Manager_Change_Date": f_rec.get("Manager_Change_Date")
                            }
            logging.info(f"Loaded {len(old_db_lookup)} existing schemes from old database for manager change tracking.")
        except Exception as e:
            logging.warning(f"Could not load old database for diffing: {e}")

    output_data = {
        "metadata": {
            "risk_free_rate": round(rfr_value * 100, 2),
            "rfr_status": rfr_status,
            "compile_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "benchmark_mapping": {}
        },
        "categories": {}
    }
    
    for cat in CATEGORIES_TO_COMPILE:
        if cat not in universe:
            logging.warning(f"Category {cat} not found in AMFI universe. Skipping.")
            continue
            
        funds = universe[cat]
        logging.info(f"Processing category: {cat} (Funds count: {len(funds)})")
        
        # Identify dynamic benchmark for this category
        bench_info = config.CATEGORY_BENCHMARK_MAP.get(cat, {"id": config.DEFAULT_BENCHMARK_TICKER, "label": config.DEFAULT_BENCHMARK_LABEL})
        
        # Log metadata for UI transparency
        output_data["metadata"]["benchmark_mapping"][cat] = bench_info["label"]
        
        # Instantiate engine specifically for this benchmark
        engine = QuantEngine(benchmark_ticker=bench_info["id"], risk_free_rate=rfr_value)
        
        # We run the calculations concurrently
        df = engine.process_category_concurrently(funds, category_name=cat)
        
        if df.empty:
            logging.warning(f"No valid metrics computed for {cat}. Skipping.")
            continue
            
        # Add manager change tracking fields
        changed_flags = []
        change_dates = []
        today_str = datetime.date.today().strftime("%Y-%m-%d")

        for idx, row in df.iterrows():
            sc_code = str(row["code"])
            new_mgrs = str(row.get("Managers") or "").strip()
            
            manager_changed_recently = False
            manager_change_date = None
            
            if sc_code in old_db_lookup:
                old_rec = old_db_lookup[sc_code]
                old_mgrs = str(old_rec.get("Managers") or "").strip()
                
                has_old_mgrs = old_mgrs and old_mgrs.lower() not in ["", "n/a", "none", "null"]
                has_new_mgrs = new_mgrs and new_mgrs.lower() not in ["", "n/a", "none", "null"]
                
                if has_old_mgrs and has_new_mgrs and old_mgrs != new_mgrs:
                    manager_changed_recently = True
                    manager_change_date = today_str
                    logging.info(f"MANAGER CHANGE DETECTED for {row['Fund Name']} ({sc_code}): '{old_mgrs}' -> '{new_mgrs}'")
                else:
                    old_changed = old_rec.get("Manager_Changed_Recently", False)
                    old_date_str = old_rec.get("Manager_Change_Date")
                    
                    if old_changed and old_date_str:
                        try:
                            old_date = datetime.datetime.strptime(old_date_str, "%Y-%m-%d").date()
                            days_elapsed = (datetime.date.today() - old_date).days
                            if days_elapsed < 180:  # Alert stays active for 180 days (6 months)
                                manager_changed_recently = True
                                manager_change_date = old_date_str
                        except:
                            pass
            
            changed_flags.append(manager_changed_recently)
            change_dates.append(manager_change_date)

        df["Manager_Changed_Recently"] = changed_flags
        df["Manager_Change_Date"] = change_dates
            
        # Sort by Rating_Score descending
        df = df.sort_values(by="Rating_Score", ascending=False)
        
        # Replace NaN values with None / null for JSON serialization
        df = df.replace({np.nan: None})
        
        # Convert df to dictionary records
        records = df.to_dict(orient="records")
        output_data["categories"][cat] = records
        logging.info(f"Successfully compiled {len(records)} funds for {cat}")
        
    # Write to mf_universe_data.json
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mf_universe_data.json")
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)
        
    logging.info(f"Compilation complete! Static database written to {output_path}")

if __name__ == "__main__":
    main()
