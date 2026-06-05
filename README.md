# MF Quant Core - Institutional Workstation & Rating Methodology

MF Quant Core is an institutional-grade, vectorized financial analytics workstation for screening and ranking Indian Mutual Funds. The system separates genuine manager skill from lucky market cycles using advanced risk-adjusted performance modeling, dynamic weighting parameters, and qualitative overlays (AUM scale checks and manager tenure stability).

The workstation is built as a standalone, zero-server-dependency dark-theme client served directly in the web browser, powered by a Python command-line compiler and automated cloud data synchronization.

---

## 🏗️ High-Level System Architecture

```
MF-Screener/
├── .github/workflows/
│   └── data_compiler.yml    # Daily cloud execution workflow (GitHub Actions)
├── config.py                # Global parameters, benchmark constants, and API endpoints
├── data_loader.py           # AMFI parsing registry, yFinance & qualitative API streams
├── analytics.py             # Vectorized financial engineering & dynamic rating engine
├── generate_data.py         # Batch data compilation script (creates JSON database)
├── vercel.json              # Explicit Vercel static hosting configuration
├── index.html               # Premium glassmorphic workstation dashboard interface
├── index.css                # Dark-theme layout stylesheet (fluid transitions)
├── app.js                   # Client-side workstation controller (sorting, drawer modal)
├── start_dashboard.sh       # Local launcher (compiles database and boots server)
└── README.md                # Quantitative methodology guide & manual
```

1. **Static Frontend (Vercel Host):** Serves `index.html`, `index.css`, and `app.js` instantly from a global Edge CDN. Bypasses backend database delays by fetching the static `mf_universe_data.json` directly.
2. **Batch Compilation Engine (Python):** Fetching NAV files and benchmark prices over historical timelines, parsing portfolios, and executing vectorized matrix math in parallel worker threads.
3. **Data Automation (GitHub Actions):** Runs the Python compiler daily at **7:30 AM IST**, commits the updated `mf_universe_data.json` database back to GitHub, and triggers Vercel to redeploy the live workstation automatically.

---

## 🎯 Scoring Parameters & Baseline Inputs

* **Live Risk-Free Rate ($R_f$):** Dynamically pulled from the live 91-Day Sovereign India Treasury Bill yield (fallback rate: $6.50\%$).
* **System Benchmark Index ($R_m$):** Nifty 50 Index (symbol: `^NSEI`), serving as the standardized benchmark for return variance.
* **Historical Timeline Window:** Fetches **8 years** of daily historical returns. This provides a minimum buffer of 2,016 daily NAV prices, ensuring shifts have sufficient historical context.

---

## 📊 In-Depth Rating Methodology

The Overall rating is calculated out of **5.0 Stars (★)**. It evaluates a fund across four mathematical quantitative pillars (scored 0 to 5, then scaled by category-specific weights) and applies qualitative adjustments.

```
Final Score = (Consistency × W_roll) + (Information Ratio × W_ir) + (CAPM Alpha × W_alpha) + (Downside Capture × W_dc) 
              + AUM Adjustment + Manager Tenure Adjustment
```

### Pillar 1: Performance Consistency (Rolling Returns)
* **What it is:** The average of trailing compounded annual returns calculated across all overlapping daily windows (1-year, 3-year, and 5-year periods).
* **Why it is preferable to Absolute Returns:** Absolute returns (point-to-point trailing returns) are highly sensitive to market highs and lows on the start/end dates (called **endpoint bias**). Rolling returns eliminate endpoint bias by simulating an investor who could have bought on any random day in the past, measuring performance across entire market cycles.
* **Calculation:** 
  $$\text{Rolling } 3\text{Y CAGR} = \left( \frac{\text{NAV}_t}{\text{NAV}_{t-756}} \right)^{\frac{252}{756}} - 1$$
* **Scoring Baseline:** Evaluated relative to the category average:
  * $\text{Scheme Return} - \text{Category Mean} \ge +3.0\% \rightarrow \mathbf{5.0\text{★}}$ (Excellent)
  * $\text{Scheme Return} - \text{Category Mean} \ge 0.0\% \rightarrow \mathbf{3.75\text{★}}$ (Outperforming)
  * $\text{Scheme Return} - \text{Category Mean} \ge -3.0\% \rightarrow \mathbf{2.5\text{★}}$ (Stable/Average)
  * $\text{Scheme Return} - \text{Category Mean} \ge -6.0\% \rightarrow \mathbf{1.25\text{★}}$ (Lagging)
  * $\text{Scheme Return} - \text{Category Mean} < -6.0\% \rightarrow \mathbf{0.0\text{★}}$ (Poor)

### Pillar 2: Manager Skill vs. Luck (Information Ratio)
* **What it is:** Measures the consistency of the fund's excess returns relative to active risk taken against the Nifty 50 benchmark.
* **Why it Matters:** A high ratio proves the manager beats the index via disciplined, structured execution rather than taking reckless, concentrated bets or hitting a lucky streak.
* **Calculation:** 
  $$\text{Information Ratio} = \frac{\text{Mean of Active Returns}}{\text{Standard Deviation of Active Returns (Tracking Error)}} \times \sqrt{252}$$
* **Scoring Baseline:**
  * $\text{IR} \ge 1.0 \rightarrow \mathbf{5.0\text{★}}$ (Exceptional: highly consistent, low active risk)
  * $\text{IR} \ge 0.75 \rightarrow \mathbf{3.75\text{★}}$ (Very Good)
  * $\text{IR} \ge 0.50 \rightarrow \mathbf{2.5\text{★}}$ (Good: standard risk-reward active management)
  * $\text{IR} \ge 0.0 \rightarrow \mathbf{1.25\text{★}}$ (Mediocre)
  * $\text{IR} < 0.0 \rightarrow \mathbf{0.0\text{★}}$ (Inefficient: active risk detracted value)

### Pillar 3: CAPM Risk-Adjusted Net Alpha
* **What it is:** The annualized excess return generated by the manager's active stock selection, after removing general market movements (Beta) and fees.
* **Why it Matters:** It isolates the manager's true value-add, proving whether you are paying active management fees for actual stock-picking skill or just buying a passive index clone.
* **Calculation:** 
  $$\text{CAPM Alpha} = \text{Annualized Return} - \left[ R_f + \beta \times (\text{Benchmark Return} - R_f) \right]$$
  $$\text{Net Alpha} = \text{CAPM Alpha} - \text{Expense Ratio}$$
* **Scoring Baseline:**
  * $\text{Net Alpha} \ge 5.0\% \rightarrow \mathbf{5.0\text{★}}$ (Outstanding: added 5%+ extra return yearly through stock-picking)
  * $\text{Net Alpha} \ge 2.5\% \rightarrow \mathbf{3.75\text{★}}$ (Strong)
  * $\text{Net Alpha} \ge 0.0\% \rightarrow \mathbf{2.5\text{★}}$ (Positive active return)
  * $\text{Net Alpha} \ge -2.0\% \rightarrow \mathbf{1.25\text{★}}$ (Underperforming)
  * $\text{Net Alpha} < -2.0\% \rightarrow \mathbf{0.0\text{★}}$ (Substantial drag)

### Pillar 4: Capital Protection (Downside Capture)
* **What it is:** Measures the percentage of the benchmark index's losses the fund suffers on negative trading days.
* **Why it Matters:** Restricting drawdowns during market corrections is crucial. A fund that falls less than the market has a much shorter path to recovery and builds massive compounding advantages.
* **Calculation:** 
  $$\text{Downside Capture} = \frac{\text{Cumulative Return of Fund on Negative Days}}{\text{Cumulative Return of Benchmark on Negative Days}} \times 100$$
* **Scoring Baseline:**
  * $\text{Downside Capture} \le 80\% \rightarrow \mathbf{5.0\text{★}}$ (Excellent Capital Shield: only captured 80% or less of losses)
  * $\text{Downside Capture} \le 95\% \rightarrow \mathbf{3.75\text{★}}$ (Good Protection)
  * $\text{Downside Capture} \le 100\% \rightarrow \mathbf{3.125\text{★}}$ (Average market protection)
  * $\text{Downside Capture} \le 110\% \rightarrow \mathbf{1.875\text{★}}$ (Aggressive: captures more losses than index)
  * $\text{Downside Capture} > 110\% \rightarrow \mathbf{0.0\text{★}}$ (High risk capital erosion)

---

## 🎛️ Dynamic Category Weighting Profiles

We apply category-specific weighting profiles to match the different mandates of mutual fund schemes:

| Category Mandate | Rolling Returns | Information Ratio | CAPM Net Alpha | Downside Capture | Quantitative Goal |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Aggressive Growth**<br>*(Small & Mid Cap Equity)* | **20%** | **25%** | **35%** | **20%** | Prioritizes **Alpha** (stock-picking skill) since investors pay active fees specifically to find inefficient opportunities in smaller companies. |
| **Conservative Asset Allocation**<br>*(Hybrid & Balanced Advantage)* | **25%** | **25%** | **15%** | **35%** | Prioritizes **Downside Capture** because hybrid mandates are designed to protect capital and allocate assets defensively during corrections. |
| **Capital Safety**<br>*(Debt, Liquid, Arbitrage)* | **35%** | **20%** | **5%** | **40%** | Alpha is largely irrelevant. We prioritize **Downside Protection** and **Rolling Returns** (day-to-day liquidity consistency). |
| **Core Active Equity**<br>*(Large, Flexi, Multi Cap, ELSS, Value)* | **25%** | **25%** | **25%** | **25%** | Maintained at **Equal Weights (25% each)** for a balanced evaluation of risk and return. |

---

## ⚖️ Qualitative Score Adjustments

We apply automated adjustments to the final score to account for structural capacity (AUM) and manager transitions:

### 1. Dynamic AUM Adjustments
AUM (Assets Under Management) is evaluated dynamically according to the category liquidity profile:
* **Small & Mid Cap Bloat Penalty (`-0.5★`):**
  * *Condition:* Small Cap AUM $> 15,000$ Cr, or Mid Cap AUM $> 25,000$ Cr.
  * *Rationale:* Massive size in illiquid segments prevents the manager from entering and exiting smaller companies without creating high impact costs. This forces style drift (buying larger stocks) and degrades returns.
* **Flexi & Multi Cap Scale Drag Penalty (`-0.25★`):**
  * *Condition:* Flexi/Multi Cap AUM $> 35,000$ Cr.
  * *Rationale:* Extremely large size prevents the manager from allocating meaningful capital into mid/small cap companies because a tiny $1\%$ position would exceed the company's daily trading volumes. This forces the fund to hold large caps exclusively, stripping away its defining "flexibility."
* **Large Cap & Hybrid Scale Efficiency Bonus (`+0.25★`):**
  * *Condition:* Large/Hybrid AUM $> 20,000$ Cr.
  * *Rationale:* Operating in highly liquid, blue-chip segments where size is a benefit. Allows the fund house to negotiate lower transaction costs and reduce expense ratios.
* **Liquid & Debt Safety Bonus (`+0.25★`):**
  * *Condition:* Liquid/Debt AUM $> 30,000$ Cr.
  * *Rationale:* Serves as a cushion during redemption runs. Large scale prevents sudden redemptions from corporate treasuries from forcing the fund to liquidate assets prematurely.

### 2. Fund Manager Tenure Stability Overlay
A fund manager's tenure dictates the reliability of historical performance:
* **Manager Transition Penalty (`-0.5★`):**
  * *Condition:* Lead manager tenure is **less than 1.0 year**.
  * *Rationale:* The stellar 3Y and 5Y rolling returns in the database belong to the *previous* manager's skill. A new manager introduces transition risk, making historical numbers unrepresentative of future performance.
* **Veteran Manager Stability Bonus (`+0.25★`):**
  * *Condition:* Lead manager tenure is **greater than 5.0 years**.
  * *Rationale:* High tenure proves the long-term rolling returns, excess alpha, and downside capture are directly and reliably attributable to the current manager's active execution.

---

## 🔧 System Commands

* **Local Verification Test:** Runs the unit tests to check calculations:
  ```bash
  python3 test_screener.py
  ```
* **Database Compilation:** Re-compiles all categories, fetches fresh data, and updates the JSON file:
  ```bash
  python3 generate_data.py
  ```
* **Local Run:** Runs the data compiler and starts the local server on `http://localhost:8000`:
  ```bash
  ./start_dashboard.sh
  ```
