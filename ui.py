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
                    font-size: 0.75rem;
                    text-transform: uppercase;
                    letter-spacing: 0.08em;
                    color: #64748b;
                    font-weight: 600;
                    margin-bottom: 8px;
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
                    <div class="stat-value">{top_skill_fund['Fund Name']}</div>
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
                <div class="methodology-title">Quantitative Workstation Framework Methodology</div>
                <div class="methodology-text">
                    <strong>⭐ Rating (Out of 5):</strong> Dynamic scoring combining Rolling Return Consistency (1.25★), Information Ratio (1.25★), CAPM Alpha (1.25★), and Downside Capital Protection (1.25★).<br>
                    <strong>3Y Rolling Return:</strong> Evaluates performance consistency by averaging all trailing 3-year compound returns across the historical life of the scheme.<br>
                    <strong>Downside Capture:</strong> Capital protection indicator. Measures the percentage of the benchmark's losses captured by the fund on negative days. Values below 100 indicate capital protection (i.e. fund fell less than market).<br>
                    <strong>CAPM Alpha (3Y):</strong> Risk-adjusted excess return. Isolates manager's stock picking outperformance relative to the benchmark index.
                </div>
            </div>
        """, unsafe_allow_html=True)

        display_df = metrics_df[[
            "Rating",
            "Fund Name", 
            "1Y Return (%)", 
            "3Y Return (%)", 
            "3Y Rolling Return (%)",
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
                "3Y Rolling Return (%)": st.column_config.NumberColumn("3Y Rolling Return", format="%.2f%%", help="Historical Average 3-Year Rolling Compounded Return", width=125),
                "Alpha (3Y)": st.column_config.NumberColumn("Alpha (3Y)", format="%.2f%%", help="CAPM Alpha: Risk-adjusted excess return vs benchmark index", width=90),
                "Beta (3Y)": st.column_config.NumberColumn("Beta (3Y)", format="%.2f", help="CAPM Beta: Systematic market risk sensitivity", width=80),
                "Downside Capture (3Y)": st.column_config.NumberColumn("Downside Capture", format="%.1f", help="Downside Capture Ratio: lower is better (protects capital during market drops)", width=120),
                "Information Ratio (3Y)": st.column_config.NumberColumn("Info Ratio (3Y)", format="%.2f", help="Consistency of beating the benchmark relative to risk.", width=105),
                "Sharpe (3Y)": st.column_config.NumberColumn("Sharpe (3Y)", format="%.2f", help="Asset returns achieved per unit of total structural risk.", width=95),
            }
        )