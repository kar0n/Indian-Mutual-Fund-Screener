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
            default_idx = categories.index("Flexi Cap Fund") if "Flexi Cap Fund" in categories else 0
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

        metrics_df = metrics_df.sort_values(by="Information Ratio (3Y)", ascending=False)

        top_skill_fund = metrics_df.iloc[0]
        avg_1y = metrics_df["1Y Return (%)"].mean()
        avg_3y = metrics_df["3Y Return (%)"].dropna().mean()

        st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
        
        # Summary Matrix Cards Layout
        card_col1, card_col2, card_col3 = st.columns(3)
        with card_col1:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">Category Alpha Leader</div>
                    <div class="stat-value">{top_skill_fund['Fund Name']}</div>
                    <div class="stat-delta">Information Ratio: {top_skill_fund['Information Ratio (3Y)']:.2f}</div>
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
                <div class="methodology-title">Risk-Adjusted Parameters Reference</div>
                <div class="methodology-text">
                    <strong>Information Ratio (3Y):</strong> Evaluates a manager's consistency in generating excess returns relative to the tracking error of the benchmark index. Higher readings isolate persistent, repeatable portfolio management skill over luck.<br>
                    <strong>Sharpe Ratio (3Y):</strong> Reflects risk efficiency by showing the asset returns achieved per unit of total structural volatility. Higher numbers confirm clean capital allocation efficiency.
                </div>
            </div>
        """, unsafe_allow_html=True)

        display_df = metrics_df[[
            "Fund Name", 
            "1Y Return (%)", 
            "3Y Return (%)", 
            "5Y Return (%)", 
            "Sharpe (3Y)", 
            "Information Ratio (3Y)"
        ]].copy()

        display_df.insert(0, "Sr. No.", range(1, len(display_df) + 1))

        st.markdown("<h3 style='font-size: 1rem; margin-bottom: 12px; color: #f8fafc; font-weight: 600;'>Fund Performance & Risk Ranking Profile</h3>", unsafe_allow_html=True)

        # Configured with width="content" and updated the label parameter to "Scheme Name"
        st.dataframe(
            display_df,
            width="content",
            height=570,
            hide_index=True,
            column_config={
                "Sr. No.": st.column_config.NumberColumn("Rank", format="%d", width=60),
                "Fund Name": st.column_config.TextColumn("Scheme Name", width=550),
                "1Y Return (%)": st.column_config.NumberColumn("1Y Return", format="%.2f%%", help="Trailing 1-Year Annualized Compounded Return", width=110),
                "3Y Return (%)": st.column_config.NumberColumn("3Y Return", format="%.2f%%", help="Trailing 3-Year Annualized Compounded Return", width=110),
                "5Y Return (%)": st.column_config.NumberColumn("5Y Return", format="%.2f%%", help="Trailing 5-Year Annualized Compounded Return", width=110),
                "Sharpe (3Y)": st.column_config.NumberColumn("Sharpe (3Y)", format="%.2f", help="Higher is Better. Measures asset returns achieved per unit of total structural risk.", width=110),
                "Information Ratio (3Y)": st.column_config.NumberColumn("Info Ratio (3Y)", format="%.2f", help="Higher is Better. Isolates systemic risk-adjusted stock picking skill over basic luck.", width=130)
            }
        )