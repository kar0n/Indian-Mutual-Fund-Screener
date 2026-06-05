# MF-Screener - Institutional Quant Workstation

Indian Mutual Fund Quant Engine - A vectorized financial analytics engine for mutual fund screening, risk-adjusted analysis, and qualitative tracking.

Now migrated from Streamlit to a standalone, premium client-side dark-theme HTML/JS workstation powered by a Python command-line compiler.

## Workstation Architecture

```
MF-Screener/
├── config.py              # Centralized configuration, baselines, and constants
├── data_loader.py         # Network I/O, AMFI parsing, and Yahoo Finance / Upvaly APIs
├── analytics.py           # Vectorized financial engineering and risk analytics engine
├── generate_data.py       # Python compilation script (builds local database)
├── index.html             # Institutional dark-theme workstation interface
├── index.css              # Premium Glassmorphism styled CSS
├── app.js                 # Workstation client controller (sorting, filtering, detail drawer)
├── requirements-local.txt # Minimum dependencies list for compiling database
├── start_dashboard.sh     # Single-command launcher (compiles data, starts HTTP server, launches UI)
├── deploy.sh              # Commits and deploys latest revisions to Git
└── README.md              # Workstation documentation
```

## Features

- 💎 **Premium Glassmorphic Dark UI** - Curated slate-dark color palette with smooth hover effects, micro-animations, and fluid transitions.
- 🎯 **5-Star Scoring Engine** - Dynamic, multi-factor scoring model combining:
  1. Performance Consistency vs Category average (3Y Rolling Returns) - 1.25★
  2. Portfolio Manager Skill vs Luck (Information Ratio) - 1.25★
  3. CAPM Risk-Adjusted Alpha net of expense ratio - 1.25★
  4. Capital Downside Protection (Downside Capture Ratio) - 1.25★
- ⚠️ **Qualitative Constraints & Penalties** - Automatically triggers penalties on Small/Mid-cap schemes for bloated AUM (Mid > 25,000 Cr, Small > 15,000 Cr) or off-limits top-10 stock concentration (outside optimal 20%-45% range).
- 📈 **Active Details Panel** - Slide-in interactive side panel representing a transparent scorecard breakdown, risk profiles, fund management tenure details, and top 15 underlying asset allocations.
- 🚀 **Interactive Data Grid** - Real-time client-side sorting, column-level toggles, and regex-capable searching.
- 💻 **100% Local Run** - Runs directly on your machine. Avoids shared cloud IP bans on API calls and fetches clean.

## Quick Start

1. Clone or navigate to the repository directory:
```bash
cd MF-Screener
```

2. Launch the workstation:
```bash
./start_dashboard.sh
```

The script will automatically:
- Activate the Python virtual environment (`mf_quant_env`)
- Fetch fresh AMFI schemes, NAV streams, benchmark indices, and qualitative data sheets
- Compile everything into a local database `mf_universe_data.json`
- Boot a secure local HTTP server on port 8000
- Launch the workstation interface in your default web browser

To stop the workstation, simply return to the terminal and press `Ctrl+C`.

## System Requirements

- Python 3.7 or higher
- Modern web browser supporting CSS Grid, HSL colors, and Flexbox (Chrome, Safari, Firefox, Edge)
- Internet connection for compiling new data snapshots (uses cached data locally when serving)
