"""Presentation layer implementing an institutional mutual fund evaluation workstation."""

import streamlit as st
import numpy as np
import config
from data_loader import AmfiRegistry, DataLoader
from analytics import QuantEngine


class StreamlitDashboard:
    """Constructs a professional, minimalist workstation dashboard for equity schemes."""

    @st.cache_data(ttl=3600)
    def _get_cached_universe():
        return AmfiRegistry.fetch_active_universe()

    @st.cache_data(show_spinner=False)
    def _compute_metrics_cached(category_funds, rfr_value):
        engine = QuantEngine(risk_free_rate=rfr_value)
        return engine.process_category_concurrently(category_funds)

    @classmethod
    def render(cls):
        """Renders the institutional analytical interface layout."""
        st.set_page_config(
            page_title="MF Quant Core",
            layout="wide",
            initial_sidebar_state="collapsed"
        )

        # Advanced Typography Framework & Core Style Elements
        st.markdown("""
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
                
                html, body, [class*="css"], h1, h2, h3, div, span, p, label, select, button, small, .stCaption {
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
                }
                
                .block-container { padding-top: 2.5rem; max-width: 95%; }
                
                .stat-card {
                    background-color: #0b0f19;
                    border: 1px solid #1e293b;
                    border-radius: 8px;
                    padding: 24px;
                    margin-bottom: 15px;
                    min-height: 155px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                }
                .stat-label {
                    font-size: 0.72rem;
                    text-transform: uppercase;
                    letter-spacing: 0.08em;
                    color: #64748b;
                    font-weight: 600;
                    margin-bottom: 8px;
                    white-space: nowrap;
                }
                .stat-value {
                    font-size: 1.25rem;
                    font-weight: 600;
                    color: #f8fafc;
                    line-height: 1.4;
                    word-wrap: break-word;
                }
                .stat-delta {
                    font-size: 0.85rem;
                    color: #10b981;
                    font-weight: 600;
                    margin-top: 10px;
                }
                .methodology-comparison-box {
                    background-color: #0b1329;
                    border: 1px solid #1e293b;
                    border-left: 4px solid #6366f1;
                    border-radius: 6px;
                    padding: 14px 18px;
                    margin-bottom: 20px;
                }
                .methodology-comparison-box h4 {
                    color: #e2e8f0;
                    margin: 0 0 8px 0;
                    font-size: 0.9rem;
                    font-weight: 600;
                }
                .methodology-comparison-box p {
                    color: #94a3b8;
                    font-size: 0.8rem;
                    line-height: 1.5;
                    margin: 0 0 8px 0;
                }
                .methodology-comparison-box p:last-child {
                    margin-bottom: 0;
                }
                .methodology-desc-block {
                    margin-top: 6px;
                    font-size: 0.8rem;
                    color: #94a3b8;
                }
                .methodology-desc-block p {
                    margin: 0 0 6px 0;
                    line-height: 1.45;
                }
                .methodology-desc-block code {
                    background-color: rgba(148, 163, 184, 0.15);
                    color: #f1f5f9;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: monospace;
                    font-size: 0.75rem;
                }
                
                .methodology-box {
                    background-color: #0f172a;
                    border: 1px solid #1e293b;
                    border-radius: 6px;
                    padding: 18px 24px;
                    margin-bottom: 30px;
                }
                .methodology-title {
                    font-size: 0.85rem;
                    font-weight: 600;
                    color: #94a3b8;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    margin-bottom: 6px;
                }
                .methodology-text {
                    font-size: 0.85rem;
                    color: #64748b;
                    line-height: 1.6;
                }
                
                .metadata-line {
                    text-align: right; 
                    font-size: 0.85rem; 
                    color: #475569; 
                    font-weight: 600;
                    margin-top: 32px;
                }
            </style>
        """, unsafe_allow_html=True)

        # Top-most Master Header row with Reset Cache pushed to absolute upper-right corner
        col_head_title, col_head_btn = st.columns([4, 0.8])
        with col_head_title:
            st.title("MF Quant Core")
        with col_head_btn:
            st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
            if st.button("Reset Cache", type="secondary", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

        st.markdown(
            "<div style='margin-top: -15px;'><span style='color: #475569; font-size: 0.85rem; font-weight: 600; letter-spacing: 0.03em;'>"
            "SECURITY PROTOCOL: SELECTION CONSTRAINED TO DIRECT CONFIGURATION PLANS / GROWTH OPTIONS ONLY"
            "</span></div>", 
            unsafe_allow_html=True
        )
        st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

        # Ingest universe data vectors
        universe = cls._get_cached_universe()
        rfr_value, rfr_status = DataLoader.fetch_live_risk_free_rate()
        
        if not universe:
            st.error("System Error: Unable to extract data models from AMFI registry.")
            return

        categories = sorted(list(universe.keys()))

        # Clean Main Filtering Layout Row
        col_ctrl1, col_ctrl2 = st.columns([2, 2])
        with col_ctrl1:
            default_target = "Equity Scheme - Flexi Cap Fund"
            default_idx = categories.index(default_target) if default_target in categories else 0
            selected_category = st.selectbox(
                "Category", 
                categories, 
                index=default_idx
            )
        with col_ctrl2:
            st.markdown(
                f'<div class="metadata-line">'
                f'Benchmark Index: {config.DEFAULT_BENCHMARK_LABEL} &nbsp;|&nbsp; '
                f'Risk-Free Rate: {rfr_value * 100:.2f}% ({rfr_status} India 91D T-Bill)'
                f'</div>',
                unsafe_allow_html=True
            )

        with st.spinner("Processing multi-threaded time-series arrays directly from AMFI registries..."):
            metrics_df = cls._compute_metrics_cached(universe[selected_category], rfr_value)

        if metrics_df.empty:
            st.warning("No portfolios in this segment passed current operational data validation parameters.")
            return

        metrics_df = metrics_df.sort_values(by="Rating_Score", ascending=False)

        top_skill_fund = metrics_df.iloc[0]
        avg_1y = metrics_df["1Y Return (%)"].mean()
        avg_3y = metrics_df["3Y Return (%)"].dropna().mean()

        st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
        
        # Summary Matrix Cards Layout
        card_col1, card_col2, card_col3 = st.columns(3)
        with card_col1:
            rating_str = top_skill_fund['Rating']
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">Category Quant Leader</div>
                    <div class="stat-value" style="font-size: 1.05rem;">{top_skill_fund['Fund Name']}</div>
                    <div class="stat-delta">Rating: {rating_str}</div>
                </div>
            """, unsafe_allow_html=True)
            
        with card_col2:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">Category Mean 1Y Performance</div>
                    <div class="stat-value">{avg_1y:.2f}%</div>
                    <div></div>
                </div>
            """, unsafe_allow_html=True)
            
        with card_col3:
            avg_3y_str = f"{avg_3y:.2f}%" if not np.isnan(avg_3y) else "N/A"
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">Category Mean 3Y Performance</div>
                    <div class="stat-value">{avg_3y_str}</div>
                    <div></div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        st.markdown("""
            <div class="methodology-box">
                <div class="methodology-title">Screener Guide & Key Definitions</div>
                <div class="methodology-text" style="color: #94a3b8; font-size: 0.85rem;">
                    Welcome to the <strong>MF Quant Core Workstation</strong>. We rank mutual funds using strict mathematical benchmarks to separate genuine manager skill from lucky market runs. This guide explains how to use these indicators in simple terms.
                </div>
                
                <div style="margin-top: 15px;"></div>
                
                <div class="methodology-comparison-box">
                    <h4>📊 Why Rolling Returns beat Absolute (Point-to-Point) Returns</h4>
                    <p>
                        <strong>Absolute Returns</strong> only look at a single start date and end date (e.g., standard trailing 1Y/3Y returns). If the market had a massive crash or a massive rally exactly on that date, it heavily distorts the percentage (called <strong>endpoint bias</strong>).
                    </p>
                    <p>
                        <strong>Rolling Returns</strong> calculate trailing returns for <em>every possible day</em> in history and average them. This simulates the experience of a real investor who could have invested on any random day in the past. It tests the fund across all market conditions (bull markets, bear markets, and stagnant markets) to measure true performance consistency.
                    </p>
                </div>
                
                <div style="margin-top: 15px;"></div>
                
                <div class="methodology-desc-block">
                    <p><strong>⭐ Overall Rating (Max 5★):</strong> 
                    <br>• <em>Meaning:</em> The overall grade of the fund. <code>&ge; 4★</code> is top-tier; <code>&lt; 3★</code> indicates high risk or poor consistency.
                    <br>• <em>Details:</em> Combines Rolling Returns (25%), Information Ratio (25%), CAPM Alpha (25%), and Downside Capture (25%).
                    <br>• <em>Penalties:</em> Small-cap funds >15,000 Cr and Mid-cap funds >25,000 Cr lose 0.5★ (bloated size is hard to manage). Top 10 concentration outside 20%-45% loses 0.25★.</p>
                    
                    <p style="margin-top: 10px;"><strong>📈 Rolling Returns (1Y, 3Y, 5Y):</strong> 
                    <br>• <em>Meaning:</em> The average of compounded annual returns across all historical periods.
                    <br>• <em>Baseline:</em> Double-digit returns (<code>&gt; 12% to 15%</code>) are considered strong. Compare against the benchmark index.</p>
                    
                    <p style="margin-top: 10px;"><strong>⚡ CAPM Alpha (3Y):</strong> 
                    <br>• <em>Meaning:</em> The extra return the manager makes purely through smart stock-picking skill.
                    <br>• <em>Baseline:</em> <code>&gt; 0%</code> means beat the market; <code>&ge; 3.0%</code> is outstanding; <code>&lt; 0%</code> means failed to beat the index.</p>
                    
                    <p style="margin-top: 10px;"><strong>🛡️ Downside Capture (3Y):</strong> 
                    <br>• <em>Meaning:</em> Capital shield. Measures how much of the market's losses the fund suffers when the market drops.
                    <br>• <em>Baseline:</em> <code>100%</code> means fell exactly like the market; <code>&lt; 100% (e.g. 70-80%)</code> is ideal; <code>&gt; 100%</code> is aggressive/risky.</p>
                    
                    <p style="margin-top: 10px;"><strong>🎯 Information Ratio (3Y):</strong> 
                    <br>• <em>Meaning:</em> Skill-to-risk ratio. Proves if outperformance is due to consistent skill or a few risky, lucky bets.
                    <br>• <em>Baseline:</em> <code>&ge; 0.5</code> is good; <code>&ge; 1.0</code> is exceptional; <code>&lt; 0</code> is inefficient risk taking.</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        display_df = metrics_df[[
            "Rating",
            "Fund Name", 
            "1Y Return (%)", 
            "3Y Return (%)", 
            "1Y Rolling Return (%)",
            "3Y Rolling Return (%)",
            "5Y Rolling Return (%)",
            "Alpha (3Y)",
            "Beta (3Y)",
            "Downside Capture (3Y)",
            "Information Ratio (3Y)",
            "Sharpe (3Y)"
        ]].copy()

        display_df.insert(0, "Sr. No.", range(1, len(display_df) + 1))

        st.markdown("<h3 style='font-size: 1rem; margin-bottom: 12px; color: #f8fafc; font-weight: 600;'>Fund Performance & Risk Ranking Profile</h3>", unsafe_allow_html=True)

        st.dataframe(
            display_df,
            width="content",
            height=570,
            hide_index=True,
            column_config={
                "Sr. No.": st.column_config.NumberColumn("Rank", format="%d", width=60),
                "Rating": st.column_config.TextColumn("Rating", width=100, help="Dynamic 5-Star Quant Rating based on Performance Consistency, IR, CAPM Alpha, and Downside Capture."),
                "Fund Name": st.column_config.TextColumn("Scheme Name", width=380),
                "1Y Return (%)": st.column_config.NumberColumn("1Y Return", format="%.2f%%", help="Trailing 1-Year Annualized Compounded Return", width=95),
                "3Y Return (%)": st.column_config.NumberColumn("3Y Return", format="%.2f%%", help="Trailing 3-Year Annualized Compounded Return", width=95),
                "1Y Rolling Return (%)": st.column_config.NumberColumn("1Y Rolling Return", format="%.2f%%", help="Historical Average 1-Year Rolling Compounded Return", width=125),
                "3Y Rolling Return (%)": st.column_config.NumberColumn("3Y Rolling Return", format="%.2f%%", help="Historical Average 3-Year Rolling Compounded Return", width=125),
                "5Y Rolling Return (%)": st.column_config.NumberColumn("5Y Rolling Return", format="%.2f%%", help="Historical Average 5-Year Rolling Compounded Return", width=125),
                "Alpha (3Y)": st.column_config.NumberColumn("Alpha (3Y)", format="%.2f%%", help="CAPM Alpha: Risk-adjusted excess return vs benchmark index", width=90),
                "Beta (3Y)": st.column_config.NumberColumn("Beta (3Y)", format="%.2f", help="CAPM Beta: Systematic market risk sensitivity", width=80),
                "Downside Capture (3Y)": st.column_config.NumberColumn("Downside Capture", format="%.1f", help="Downside Capture Ratio: lower is better (protects capital during market drops)", width=120),
                "Information Ratio (3Y)": st.column_config.NumberColumn("Info Ratio (3Y)", format="%.2f", help="Consistency of beating the benchmark relative to risk.", width=105),
                "Sharpe (3Y)": st.column_config.NumberColumn("Sharpe (3Y)", format="%.2f", help="Asset returns achieved per unit of total structural risk.", width=95),
            }
        )