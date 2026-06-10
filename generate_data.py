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
        
    # Removed global QuantEngine initialization
    
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
