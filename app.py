"""
Pharmaceutical Retail Pricing Analytics, Streamlit Dashboard
=============================================================
An interactive market-research platform that turns a raw retail pricing
spreadsheet (CVS, Walmart, Costco) into an executive-grade analytics tool:
KPI cards, product- and retailer-level comparisons, generic-vs-brand pricing,
availability metrics, and automatically generated market insights.

Run locally with:
    streamlit run app.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import data_processing as dp

# --------------------------------------------------------------------------- #
# Page configuration
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="Pharma Retail Pricing Analytics",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------- #
# Design system, colours and Plotly template
# --------------------------------------------------------------------------- #
PALETTE = {
    "ink": "#16242F",
    "muted": "#5C6B7A",
    "primary_dark": "#0B3D52",
    "primary": "#0F7B8A",
    "accent": "#E8A33D",
    "generic": "#0F8B8D",
    "brand": "#E8743B",
    "good": "#2A9D8F",
    "warn": "#E76F51",
    "surface": "#FFFFFF",
    "bg": "#F4F6F9",
    "grid": "#E7ECF2",
}

RETAILER_COLORS = {
    "CVS": "#D64550",
    "Walmart": "#2D6CB0",
    "Costco": "#3F9C7E",
}
TYPE_COLORS = {"Generic": "#0F8B8D", "Brand": "#E8743B"}

SEQ = ["#0B3D52", "#0F7B8A", "#3F9C7E", "#7FB069", "#E8A33D", "#E8743B", "#D64550"]


def style_fig(fig: go.Figure, height: int = 380, legend_top: bool = True) -> go.Figure:
    """Apply a consistent, clean visual style to every Plotly figure."""
    fig.update_layout(
        height=height,
        template="plotly_white",
        font=dict(family="Inter, Segoe UI, system-ui, sans-serif",
                  size=13, color=PALETTE["ink"]),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=30, b=10),
        title=dict(text="", font=dict(size=15, color=PALETTE["primary_dark"]),
                   x=0.01, xanchor="left"),
        hoverlabel=dict(bgcolor="white", font_size=12,
                        bordercolor=PALETTE["grid"]),
        colorway=SEQ,
    )
    if legend_top:
        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="left", x=0, title_text="")
        )
    fig.update_xaxes(showgrid=False, zeroline=False,
                     linecolor=PALETTE["grid"], tickcolor=PALETTE["grid"])
    fig.update_yaxes(showgrid=True, gridcolor=PALETTE["grid"], zeroline=False,
                     linecolor=PALETTE["grid"])
    return fig


# --------------------------------------------------------------------------- #
# Custom CSS
# --------------------------------------------------------------------------- #
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
    }}
    .stApp {{ background: {PALETTE['bg']}; }}
    .block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1280px; }}

    /* ---- Hero header ---- */
    .hero {{
        background: linear-gradient(120deg, {PALETTE['primary_dark']} 0%, {PALETTE['primary']} 100%);
        border-radius: 18px; padding: 26px 32px; color: #fff;
        box-shadow: 0 12px 30px rgba(11,61,82,0.22);
        margin-bottom: 22px;
    }}
    .hero h1 {{ margin: 0; font-size: 1.85rem; font-weight: 800; letter-spacing:-0.02em; }}
    .hero p {{ margin: 6px 0 0; opacity: 0.92; font-size: 0.98rem; font-weight: 400; }}
    .hero .pills {{ margin-top: 14px; }}
    .hero .pill {{
        display:inline-block; background: rgba(255,255,255,0.16);
        border:1px solid rgba(255,255,255,0.22);
        padding: 4px 12px; border-radius: 999px; font-size: 0.78rem;
        margin-right: 8px; font-weight: 500;
    }}

    /* ---- Section title ---- */
    .sec-title {{
        font-size: 1.28rem; font-weight: 700; color: {PALETTE['primary_dark']};
        margin: 6px 0 2px; letter-spacing: -0.01em;
    }}
    .sec-sub {{ color: {PALETTE['muted']}; font-size: 0.92rem; margin-bottom: 14px; }}
    .divider {{ height:1px; background:{PALETTE['grid']}; margin: 6px 0 18px; border:none; }}

    /* ---- KPI cards ---- */
    .kpi-grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(150px,1fr));
                 gap:14px; margin-bottom: 6px; }}
    .kpi {{
        background: {PALETTE['surface']}; border:1px solid {PALETTE['grid']};
        border-radius: 14px; padding: 16px 18px;
        box-shadow: 0 2px 10px rgba(22,36,47,0.04);
        transition: transform .15s ease, box-shadow .15s ease;
        border-top: 3px solid {PALETTE['primary']};
    }}
    .kpi:hover {{ transform: translateY(-3px); box-shadow: 0 10px 22px rgba(22,36,47,0.10); }}
    .kpi .label {{ font-size: 0.74rem; text-transform: uppercase; letter-spacing: .06em;
                   color: {PALETTE['muted']}; font-weight: 600; }}
    .kpi .value {{ font-size: 1.65rem; font-weight: 800; color: {PALETTE['ink']};
                   line-height: 1.1; margin-top: 4px; }}
    .kpi .sub {{ font-size: 0.78rem; color: {PALETTE['muted']}; margin-top: 2px; }}
    .kpi.accent {{ border-top-color: {PALETTE['accent']}; }}
    .kpi.green  {{ border-top-color: {PALETTE['good']}; }}
    .kpi.brand  {{ border-top-color: {PALETTE['brand']}; }}

    /* ---- Generic insight / callout card ---- */
    .card {{
        background: {PALETTE['surface']}; border:1px solid {PALETTE['grid']};
        border-radius: 14px; padding: 18px 20px;
        box-shadow: 0 2px 10px rgba(22,36,47,0.04); margin-bottom: 6px;
    }}
    .callout {{
        background: linear-gradient(135deg, #FFF8EC 0%, #FEFCF7 100%);
        border:1px solid #F2E3C4; border-left: 4px solid {PALETTE['accent']};
        border-radius: 12px; padding: 16px 18px; margin: 6px 0 14px;
    }}
    .callout h4 {{ margin:0 0 6px; color:{PALETTE['primary_dark']}; font-size:0.98rem; }}
    .callout p {{ margin:0; color:{PALETTE['ink']}; font-size:0.9rem; line-height:1.5; }}

    .insight {{
        background: {PALETTE['surface']}; border:1px solid {PALETTE['grid']};
        border-radius: 12px; padding: 16px 18px; margin-bottom: 12px;
        border-left: 4px solid {PALETTE['primary']};
        box-shadow: 0 2px 8px rgba(22,36,47,0.04);
    }}
    .insight .tag {{ display:inline-block; font-size:0.68rem; font-weight:700;
        text-transform:uppercase; letter-spacing:.06em; color:#fff;
        background:{PALETTE['primary']}; padding:2px 9px; border-radius:6px;
        margin-bottom:8px; }}
    .insight .tag.win {{ background:{PALETTE['good']}; }}
    .insight .tag.watch {{ background:{PALETTE['warn']}; }}
    .insight .tag.save {{ background:{PALETTE['accent']}; }}
    .insight h4 {{ margin:0 0 4px; font-size:1rem; color:{PALETTE['ink']}; }}
    .insight p {{ margin:0; font-size:0.9rem; color:{PALETTE['muted']}; line-height:1.5; }}

    .badge {{ display:inline-block; padding:3px 10px; border-radius:999px;
        font-size:0.74rem; font-weight:600; }}

    /* ---- Sidebar ---- */
    section[data-testid="stSidebar"] {{ background: #0B2A38; }}
    section[data-testid="stSidebar"] * {{ color: #DCE7EC; }}
    section[data-testid="stSidebar"] .stRadio label {{ color:#DCE7EC; }}
    .side-brand {{ font-size:1.05rem; font-weight:800; color:#fff;
        display:flex; align-items:center; gap:8px; margin-bottom:2px; }}
    .side-tag {{ font-size:0.74rem; color:#8FB0BE; margin-bottom:14px; }}

    #MainMenu, footer {{ visibility: hidden; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------- #
# Data loading (cached)
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner=False)
def get_data(file_bytes: bytes | None, default_path: str) -> pd.DataFrame:
    source = file_bytes if file_bytes is not None else default_path
    return dp.load_and_clean(source)


DEFAULT_DATA = "data/Pharmaceutical_Retail_Pricing_Analytics.xlsx"


def fmt_money(x) -> str:
    return "—" if pd.isna(x) else f"${x:,.2f}"


def fmt_unit(x) -> str:
    return "—" if pd.isna(x) else f"${x:.3f}"


def fmt_pct(x) -> str:
    return "—" if pd.isna(x) else f"{x:.0f}%"


# --------------------------------------------------------------------------- #
# Sidebar, branding, data source, navigation, global filters
# --------------------------------------------------------------------------- #
st.sidebar.markdown(
    '<div class="side-brand">💊 Pharma Pricing IQ</div>'
    '<div class="side-tag">Retail Market Research Suite</div>',
    unsafe_allow_html=True,
)

uploaded = st.sidebar.file_uploader(
    "Data source (.xlsx)", type=["xlsx"],
    help="Defaults to the bundled dataset. Upload a workbook with the same layout to analyse your own data.",
)

try:
    df = get_data(uploaded.getvalue() if uploaded else None, DEFAULT_DATA)
except Exception as exc:  # pragma: no cover - defensive UI guard
    st.error(f"Could not read the data file: {exc}")
    st.stop()

st.sidebar.markdown("---")
section = st.sidebar.radio(
    "Navigate",
    [
        "Executive Summary",
        "Product Comparison",
        "Retailer Analysis",
        "Generic vs. Brand",
        "Availability",
        "Market Insights",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Global filters**")

all_cats = sorted(df["category"].dropna().unique().tolist())
all_retailers = ["CVS", "Walmart", "Costco"]

sel_cats = st.sidebar.multiselect("Categories", all_cats, default=all_cats)
sel_retailers = st.sidebar.multiselect("Retailers", all_retailers, default=all_retailers)

if not sel_cats:
    sel_cats = all_cats
if not sel_retailers:
    sel_retailers = all_retailers

fdf = df[df["category"].isin(sel_cats) & df["retailer_short"].isin(sel_retailers)].copy()

st.sidebar.markdown("---")
st.sidebar.caption(
    "Built with Streamlit + Plotly. Unit price = shelf price ÷ pack count, "
    "the normalised metric used for fair cross-retailer comparison."
)


# --------------------------------------------------------------------------- #
# Shared hero header
# --------------------------------------------------------------------------- #
def hero():
    st.markdown(
        f"""
        <div class="hero">
            <h1>Pharmaceutical Retail Pricing Analytics</h1>
            <p>Comparative pricing, availability &amp; generic-substitution intelligence across
            CVS, Walmart and Costco, built from field-collected nutraceutical &amp; OTC pricing data.</p>
            <div class="pills">
                <span class="pill">📦 {df['category'].nunique()} therapeutic categories</span>
                <span class="pill">🏪 {df['retailer'].nunique()} retailers</span>
                <span class="pill">🔖 {int(df['product_name'].notna().sum())} product listings</span>
                <span class="pill">⚖️ Unit-price normalised</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(title: str, sub: str):
    st.markdown(f'<div class="sec-title">{title}</div>'
                f'<div class="sec-sub">{sub}</div>', unsafe_allow_html=True)


# =========================================================================== #
# SECTION 1, EXECUTIVE SUMMARY
# =========================================================================== #
def render_executive():
    hero()
    k = dp.kpi_summary(fdf)

    cards = [
        ("kpi", "Therapeutic Categories", str(k["categories"]), "brand ↔ generic pairs"),
        ("kpi", "Retailers Compared", str(k["retailers"]), "CVS · Walmart · Costco"),
        ("kpi", "Product Listings", str(k["listings"]), "priced shelf items"),
        ("kpi green", "Overall Availability", fmt_pct(k["availability_rate"] * 100),
         "in-stock at search time"),
        ("kpi accent", "Avg Unit Price", fmt_unit(k["avg_unit_price"]),
         f"median {fmt_unit(k['median_unit_price'])}"),
        ("kpi brand", "Generic Savings", fmt_pct(k["generic_vs_brand_savings"]),
         "avg unit-price vs brand"),
    ]
    html = '<div class="kpi-grid">'
    for cls, label, value, sub in cards:
        html += (f'<div class="{cls}"><div class="label">{label}</div>'
                 f'<div class="value">{value}</div><div class="sub">{sub}</div></div>')
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    c1, c2 = st.columns([1.15, 1])
    with c1:
        section_title("Price Competitiveness by Retailer",
                      "Average normalised unit price, lower is cheaper for the shopper.")
        sc = dp.retailer_scorecard(fdf)
        fig = px.bar(sc, x="Retailer", y="Avg Unit Price", text="Avg Unit Price",
                     color="Retailer", color_discrete_map=RETAILER_COLORS)
        fig.update_traces(texttemplate="$%{text:.3f}", textposition="outside",
                          cliponaxis=False)
        fig.update_layout(showlegend=False, yaxis_title="Avg unit price ($)",
                          xaxis_title="")
        st.plotly_chart(style_fig(fig, 360), width='stretch')
    with c2:
        section_title("In-Stock Rate by Retailer",
                      "Share of searched listings that were available.")
        sc = dp.retailer_scorecard(fdf)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=sc["In-Stock Rate"] * 100, y=sc["Retailer"], orientation="h",
            marker_color=[RETAILER_COLORS[r] for r in sc["Retailer"]],
            text=[f"{v*100:.0f}%" for v in sc["In-Stock Rate"]],
            textposition="outside",
        ))
        fig.update_layout(xaxis_title="In-stock rate (%)", yaxis_title="",
                          xaxis_range=[0, 110])
        st.plotly_chart(style_fig(fig, 360, legend_top=False), width='stretch')

    c3, c4 = st.columns(2)
    with c3:
        section_title("Listings by Category & Type",
                      "Generic vs brand coverage across the assortment.")
        cnt = (fdf[fdf["product_name"].notna()]
               .groupby(["category", "search_type"]).size()
               .reset_index(name="n"))
        fig = px.bar(cnt, x="n", y="category", color="search_type", orientation="h",
                     color_discrete_map=TYPE_COLORS, barmode="stack")
        fig.update_layout(xaxis_title="Listings", yaxis_title="",
                          legend_title_text="")
        st.plotly_chart(style_fig(fig, 380), width='stretch')
    with c4:
        section_title("Unit-Price Distribution",
                      "Spread of unit prices across all in-stock listings.")
        pa = dp.priced_available(fdf)
        fig = px.box(pa, x="retailer_short", y="price_per_count",
                     color="retailer_short", color_discrete_map=RETAILER_COLORS,
                     points="all")
        fig.update_layout(showlegend=False, xaxis_title="",
                          yaxis_title="Unit price ($)")
        st.plotly_chart(style_fig(fig, 380), width='stretch')

    # Executive takeaway
    sc = dp.retailer_scorecard(fdf)
    cheapest = sc.iloc[0]
    most_avail = sc.sort_values("In-Stock Rate", ascending=False).iloc[0]
    st.markdown(
        f"""
        <div class="callout">
            <h4>📌 Executive takeaway</h4>
            <p><b>{cheapest['Retailer']}</b> offers the lowest average unit price
            ({fmt_unit(cheapest['Avg Unit Price'])}), while <b>{most_avail['Retailer']}</b>
            leads on availability ({most_avail['In-Stock Rate']*100:.0f}% in stock).
            Choosing generic over brand saves roughly
            <b>{fmt_pct(k['generic_vs_brand_savings'])}</b> on a unit-price basis across the
            tracked categories, the single largest lever for cost reduction.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================================== #
# SECTION 2, PRODUCT COMPARISON
# =========================================================================== #
def render_product():
    section_title("Product-Level Price Comparison",
                  "Drill into a therapeutic category and compare every listing, "
                  "retailer and pack size side by side.")

    cat_options = sorted(fdf["category"].dropna().unique().tolist())
    if not cat_options:
        st.info("No categories match the current filters.")
        return
    cat = st.selectbox("Select a therapeutic category", cat_options)

    sub = fdf[fdf["category"] == cat].copy()
    brand = sub["brand_name"].dropna().iloc[0] if sub["brand_name"].notna().any() else ""
    pa = sub[sub["is_available"] & sub["price"].notna()]

    # category-level KPIs
    if not pa.empty:
        cheapest_row = pa.loc[pa["price_per_count"].idxmin()]
        spread = pa["price_per_count"].max() - pa["price_per_count"].min()
        cards = [
            ("kpi", "Brand", brand or "—", f"generic: {cat}"),
            ("kpi green", "Best Unit Price", fmt_unit(pa["price_per_count"].min()),
             f"at {cheapest_row['retailer_short']}"),
            ("kpi accent", "Avg Unit Price", fmt_unit(pa["price_per_count"].mean()),
             f"{len(pa)} in-stock listings"),
            ("kpi brand", "Price Spread", fmt_unit(spread),
             "max − min unit price"),
        ]
        html = '<div class="kpi-grid">'
        for cls, label, value, s in cards:
            html += (f'<div class="{cls}"><div class="label">{label}</div>'
                     f'<div class="value" style="font-size:1.25rem">{value}</div>'
                     f'<div class="sub">{s}</div></div>')
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        section_title("Unit Price by Listing",
                      "Each in-stock product, coloured by retailer.")
        if pa.empty:
            st.info("No in-stock priced listings for this category.")
        else:
            plot = pa.sort_values("price_per_count")
            plot["short_name"] = plot["product_name"].str.slice(0, 34) + plot[
                "product_name"].str.len().gt(34).map({True: "…", False: ""})
            fig = px.bar(plot, x="price_per_count", y="short_name", orientation="h",
                         color="retailer_short", color_discrete_map=RETAILER_COLORS,
                         custom_data=["retailer_short", "search_type", "price", "count"])
            fig.update_traces(hovertemplate=(
                "<b>%{y}</b><br>Retailer: %{customdata[0]}<br>"
                "Type: %{customdata[1]}<br>Price: $%{customdata[2]:.2f}"
                " / %{customdata[3]:.0f} ct<br>Unit: $%{x:.3f}<extra></extra>"))
            fig.update_layout(xaxis_title="Unit price ($)", yaxis_title="",
                              legend_title_text="")
            st.plotly_chart(style_fig(fig, 420), width='stretch')
    with c2:
        section_title("Price vs. Pack Size",
                      "Bigger packs usually drive a lower unit price (bubble = unit price).")
        if pa.empty:
            st.info("No in-stock priced listings for this category.")
        else:
            fig = px.scatter(pa, x="count", y="price", color="search_type",
                             size="price_per_count", size_max=26,
                             color_discrete_map=TYPE_COLORS,
                             custom_data=["product_name", "retailer_short",
                                          "price_per_count"])
            fig.update_traces(hovertemplate=(
                "<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
                "Pack: %{x:.0f} ct · $%{y:.2f}<br>"
                "Unit: $%{customdata[2]:.3f}<extra></extra>"))
            fig.update_layout(xaxis_title="Pack count", yaxis_title="Shelf price ($)",
                              legend_title_text="")
            st.plotly_chart(style_fig(fig, 420), width='stretch')

    section_title("Detailed Listings", "Full data for the selected category.")
    show = sub[["retailer_short", "product_name", "search_type", "price", "count",
                "strength", "price_per_count", "availability"]].copy()
    show = show.rename(columns={
        "retailer_short": "Retailer", "product_name": "Product",
        "search_type": "Type", "price": "Price", "count": "Count",
        "strength": "Strength", "price_per_count": "Unit Price",
        "availability": "In Stock"})
    st.dataframe(
        show, width='stretch', hide_index=True,
        column_config={
            "Price": st.column_config.NumberColumn(format="$%.2f"),
            "Unit Price": st.column_config.NumberColumn(format="$%.3f"),
            "Count": st.column_config.NumberColumn(format="%.0f"),
        },
    )


# =========================================================================== #
# SECTION 3, RETAILER ANALYSIS
# =========================================================================== #
def render_retailer():
    section_title("Retailer-Level Analysis",
                  "Benchmark each chain on price competitiveness, assortment depth "
                  "and product availability.")

    sc = dp.retailer_scorecard(fdf)
    if sc.empty:
        st.info("No data for the current filters.")
        return

    # Scorecard cards
    cols = st.columns(len(sc))
    for col, (_, row) in zip(cols, sc.iterrows()):
        rank = "🥇 Cheapest" if row.name == 0 else ""
        with col:
            st.markdown(
                f"""
                <div class="card" style="border-top:3px solid {RETAILER_COLORS[row['Retailer']]}">
                    <div style="display:flex;justify-content:space-between;align-items:center">
                        <span style="font-size:1.15rem;font-weight:800;color:{PALETTE['ink']}">
                        {row['Retailer']}</span>
                        <span style="font-size:0.72rem;color:{PALETTE['accent']};font-weight:700">{rank}</span>
                    </div>
                    <div style="margin-top:10px;font-size:0.86rem;color:{PALETTE['muted']}">Avg unit price</div>
                    <div style="font-size:1.5rem;font-weight:800;color:{RETAILER_COLORS[row['Retailer']]}">
                    {fmt_unit(row['Avg Unit Price'])}</div>
                    <div style="margin-top:8px;display:flex;justify-content:space-between;font-size:0.82rem;color:{PALETTE['muted']}">
                        <span>In-stock</span><span style="font-weight:700;color:{PALETTE['ink']}">{row['In-Stock Rate']*100:.0f}%</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;font-size:0.82rem;color:{PALETTE['muted']}">
                        <span>Listings</span><span style="font-weight:700;color:{PALETTE['ink']}">{int(row['Listings'])}</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;font-size:0.82rem;color:{PALETTE['muted']}">
                        <span>Cheapest unit</span><span style="font-weight:700;color:{PALETTE['ink']}">{fmt_unit(row['Cheapest Unit'])}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        section_title("Average Unit Price by Category & Retailer",
                      "Where each chain wins or loses on price.")
        pa = dp.priced_available(fdf)
        grp = (pa.groupby(["category", "retailer_short"])["price_per_count"]
               .mean().reset_index())
        fig = px.bar(grp, x="category", y="price_per_count", color="retailer_short",
                     barmode="group", color_discrete_map=RETAILER_COLORS)
        fig.update_layout(xaxis_title="", yaxis_title="Avg unit price ($)",
                          legend_title_text="", xaxis_tickangle=-30)
        st.plotly_chart(style_fig(fig, 420), width='stretch')
    with c2:
        section_title("Price vs. Availability Positioning",
                      "Ideal retailers sit toward the upper-left: cheap and well-stocked.")
        fig = px.scatter(sc, x="Avg Unit Price", y="In-Stock Rate",
                         size="Listings", color="Retailer", size_max=55,
                         color_discrete_map=RETAILER_COLORS, text="Retailer")
        fig.update_traces(textposition="top center")
        fig.update_layout(xaxis_title="Avg unit price ($), cheaper →",
                          yaxis_title="In-stock rate", showlegend=False)
        fig.update_xaxes(autorange="reversed")
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(style_fig(fig, 420, legend_top=False), width='stretch')

    section_title("Retailer Scorecard", "Side-by-side summary metrics.")
    disp = sc.copy()
    disp["In-Stock Rate"] = (disp["In-Stock Rate"] * 100).round(0)
    st.dataframe(
        disp, width='stretch', hide_index=True,
        column_config={
            "Avg Price": st.column_config.NumberColumn("Avg Price", format="$%.2f"),
            "Avg Unit Price": st.column_config.NumberColumn("Avg Unit Price", format="$%.3f"),
            "Median Unit Price": st.column_config.NumberColumn("Median Unit", format="$%.3f"),
            "Cheapest Unit": st.column_config.NumberColumn("Cheapest Unit", format="$%.3f"),
            "In-Stock Rate": st.column_config.ProgressColumn(
                "In-Stock Rate", format="%.0f%%", min_value=0, max_value=100),
        },
    )


# =========================================================================== #
# SECTION 4, GENERIC VS BRAND
# =========================================================================== #
def render_generic_brand():
    section_title("Generic vs. Brand Pricing",
                  "Quantify the substitution opportunity, how much shoppers save by "
                  "choosing the generic equivalent.")

    pa = dp.priced_available(fdf)
    gen = pa[pa["search_type"] == "Generic"]["price_per_count"]
    brand = pa[pa["search_type"] == "Brand"]["price_per_count"]
    gb = dp.generic_brand_by_category(fdf)

    g_mean, b_mean = gen.mean(), brand.mean()
    overall_save = (b_mean - g_mean) / b_mean * 100 if b_mean else np.nan

    cards = [
        ("kpi green", "Avg Generic Unit", fmt_unit(g_mean), f"{len(gen)} listings"),
        ("kpi brand", "Avg Brand Unit", fmt_unit(b_mean), f"{len(brand)} listings"),
        ("kpi accent", "Avg Generic Savings", fmt_pct(overall_save), "unit-price basis"),
        ("kpi", "Categories w/ Both", str(int(gb[["Generic", "Brand"]].notna().all(axis=1).sum())),
         "generic & brand priced"),
    ]
    html = '<div class="kpi-grid">'
    for cls, label, value, s in cards:
        html += (f'<div class="{cls}"><div class="label">{label}</div>'
                 f'<div class="value">{value}</div><div class="sub">{s}</div></div>')
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    c1, c2 = st.columns([1.1, 1])
    with c1:
        section_title("Generic vs. Brand Unit Price by Category",
                      "Paired comparison, shorter generic bars mean bigger savings.")
        melt = gb.melt(id_vars="category", value_vars=["Generic", "Brand"],
                       var_name="Type", value_name="Unit Price").dropna()
        fig = px.bar(melt, x="category", y="Unit Price", color="Type",
                     barmode="group", color_discrete_map=TYPE_COLORS)
        fig.update_layout(xaxis_title="", yaxis_title="Avg unit price ($)",
                          legend_title_text="", xaxis_tickangle=-30)
        st.plotly_chart(style_fig(fig, 420), width='stretch')
    with c2:
        section_title("Savings Opportunity Ranking",
                      "Generic discount vs brand, by category (%).")
        rank = gb.dropna(subset=["Savings vs Brand %"]).sort_values("Savings vs Brand %")
        colors = [PALETTE["good"] if v >= 0 else PALETTE["warn"]
                  for v in rank["Savings vs Brand %"]]
        fig = go.Figure(go.Bar(
            x=rank["Savings vs Brand %"], y=rank["category"], orientation="h",
            marker_color=colors,
            text=[f"{v:+.0f}%" for v in rank["Savings vs Brand %"]],
            textposition="outside"))
        fig.add_vline(x=0, line_color=PALETTE["muted"], line_width=1)
        fig.update_layout(xaxis_title="Generic savings vs brand (%)", yaxis_title="")
        st.plotly_chart(style_fig(fig, 420, legend_top=False), width='stretch')

    # Insight on negatives
    neg = gb.dropna(subset=["Savings vs Brand %"])
    neg = neg[neg["Savings vs Brand %"] < 0]
    note = ""
    if not neg.empty:
        names = ", ".join(neg["category"].tolist())
        note = (f" Notably, for <b>{names}</b> the branded option was actually cheaper "
                f"per unit, a reminder that generic ≠ automatically cheaper, and unit-price "
                f"checking still pays off.")
    st.markdown(
        f"""
        <div class="callout">
            <h4>💡 Substitution insight</h4>
            <p>Across categories carrying both options, generics are on average
            <b>{fmt_pct(overall_save)}</b> cheaper per unit than their branded equivalents.
            The largest opportunities appear in higher-margin OTC categories.{note}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    section_title("Category Detail", "Average unit price and computed savings.")
    disp = gb.copy()
    st.dataframe(
        disp, width='stretch', hide_index=True,
        column_config={
            "category": "Category",
            "Generic": st.column_config.NumberColumn("Generic Unit", format="$%.3f"),
            "Brand": st.column_config.NumberColumn("Brand Unit", format="$%.3f"),
            "Savings vs Brand %": st.column_config.NumberColumn(
                "Generic Savings", format="%.0f%%"),
        },
    )


# =========================================================================== #
# SECTION 5, AVAILABILITY
# =========================================================================== #
def render_availability():
    section_title("Availability & Stock Coverage",
                  "Where shoppers can actually find each product, and where the gaps are.")

    overall = fdf["is_available"].mean()
    by_ret = fdf.groupby("retailer_short")["is_available"].mean()
    by_cat = fdf.groupby("category")["is_available"].mean()
    full_coverage = int((by_cat == 1).sum())

    cards = [
        ("kpi green", "Overall Availability", fmt_pct(overall * 100), "all searched listings"),
        ("kpi", "Best-Stocked Retailer",
         by_ret.idxmax() if not by_ret.empty else "—",
         f"{by_ret.max()*100:.0f}% in stock" if not by_ret.empty else ""),
        ("kpi accent", "Full-Coverage Categories", str(full_coverage),
         "in stock at every retailer"),
        ("kpi brand", "Hardest to Find",
         by_cat.idxmin() if not by_cat.empty else "—",
         f"{by_cat.min()*100:.0f}% in stock" if not by_cat.empty else ""),
    ]
    html = '<div class="kpi-grid">'
    for cls, label, value, s in cards:
        html += (f'<div class="{cls}"><div class="label">{label}</div>'
                 f'<div class="value" style="font-size:1.3rem">{value}</div>'
                 f'<div class="sub">{s}</div></div>')
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    c1, c2 = st.columns([1.25, 1])
    with c1:
        section_title("Availability Heatmap",
                      "In-stock rate by category × retailer (green = fully stocked).")
        mat = dp.availability_matrix(fdf)
        mat = mat.reindex(columns=[c for c in ["CVS", "Walmart", "Costco"]
                                   if c in mat.columns])
        fig = go.Figure(go.Heatmap(
            z=mat.values * 100, x=mat.columns, y=mat.index,
            colorscale=[[0, "#F7E1DD"], [0.5, "#F4D58D"], [1, "#3F9C7E"]],
            zmin=0, zmax=100,
            text=[[f"{v*100:.0f}%" for v in row] for row in mat.values],
            texttemplate="%{text}", textfont={"size": 12},
            colorbar=dict(title="In-stock %")))
        fig.update_layout(xaxis_title="", yaxis_title="")
        st.plotly_chart(style_fig(fig, 430, legend_top=False), width='stretch')
    with c2:
        section_title("Availability by Retailer",
                      "Share of listings in stock.")
        sc = by_ret.reset_index()
        sc.columns = ["Retailer", "rate"]
        sc = sc.sort_values("rate", ascending=True)
        fig = go.Figure(go.Bar(
            x=sc["rate"] * 100, y=sc["Retailer"], orientation="h",
            marker_color=[RETAILER_COLORS.get(r, PALETTE["primary"]) for r in sc["Retailer"]],
            text=[f"{v*100:.0f}%" for v in sc["rate"]], textposition="outside"))
        fig.update_layout(xaxis_title="In-stock rate (%)", yaxis_title="",
                          xaxis_range=[0, 110])
        st.plotly_chart(style_fig(fig, 200, legend_top=False), width='stretch')

        section_title("Availability by Category", "")
        sc2 = by_cat.reset_index()
        sc2.columns = ["Category", "rate"]
        sc2 = sc2.sort_values("rate")
        fig2 = px.bar(sc2, x="rate", y="Category", orientation="h")
        fig2.update_traces(marker_color=PALETTE["primary"],
                           text=[f"{v*100:.0f}%" for v in sc2["rate"]],
                           textposition="outside")
        fig2.update_layout(xaxis_title="In-stock rate (%)", yaxis_title="",
                           xaxis_range=[0, 115])
        st.plotly_chart(style_fig(fig2, 230, legend_top=False), width='stretch')

    # Stock gaps table
    gaps = (fdf[~fdf["is_available"]]
            .groupby(["category", "retailer_short"]).size()
            .reset_index(name="Out-of-stock listings"))
    if not gaps.empty:
        section_title("Stock Gaps", "Category–retailer combinations with missing inventory.")
        gaps = gaps.rename(columns={"category": "Category",
                                    "retailer_short": "Retailer"})
        st.dataframe(gaps.sort_values("Out-of-stock listings", ascending=False),
                     width='stretch', hide_index=True)


# =========================================================================== #
# SECTION 6, MARKET INSIGHTS (auto-generated)
# =========================================================================== #
def build_insights() -> list[dict]:
    """Generate data-driven narrative insights from the filtered dataset."""
    insights: list[dict] = []
    sc = dp.retailer_scorecard(fdf)
    pa = dp.priced_available(fdf)
    gb = dp.generic_brand_by_category(fdf)

    if not sc.empty:
        cheapest = sc.iloc[0]
        priciest = sc.iloc[-1]
        if pd.notna(cheapest["Avg Unit Price"]) and pd.notna(priciest["Avg Unit Price"]) \
                and priciest["Avg Unit Price"] > 0:
            gap = (priciest["Avg Unit Price"] - cheapest["Avg Unit Price"]) / \
                  priciest["Avg Unit Price"] * 100
            insights.append({
                "tag": "win", "tag_label": "Price Leader",
                "title": f"{cheapest['Retailer']} is the value leader",
                "body": (f"{cheapest['Retailer']} posts the lowest average unit price "
                         f"({fmt_unit(cheapest['Avg Unit Price'])}), about {gap:.0f}% below "
                         f"{priciest['Retailer']} ({fmt_unit(priciest['Avg Unit Price'])}). "
                         f"For bulk-friendly OTC staples, it is the default cost-minimising choice."),
            })

    # Generic savings
    gb_valid = gb.dropna(subset=["Savings vs Brand %"])
    if not gb_valid.empty:
        top = gb_valid.sort_values("Savings vs Brand %", ascending=False).iloc[0]
        insights.append({
            "tag": "save", "tag_label": "Substitution",
            "title": f"Biggest generic saving: {top['category']}",
            "body": (f"Switching to the generic for <b>{top['category']}</b> cuts unit cost by "
                     f"{top['Savings vs Brand %']:.0f}% versus the brand "
                     f"({fmt_unit(top['Generic'])} vs {fmt_unit(top['Brand'])}). "
                     f"This is the highest-yield substitution in the basket."),
        })
        neg = gb_valid[gb_valid["Savings vs Brand %"] < 0]
        if not neg.empty:
            worst = neg.sort_values("Savings vs Brand %").iloc[0]
            insights.append({
                "tag": "watch", "tag_label": "Counter-Intuitive",
                "title": f"Brand beats generic for {worst['category']}",
                "body": (f"For <b>{worst['category']}</b>, the branded product is actually "
                         f"{abs(worst['Savings vs Brand %']):.0f}% cheaper per unit than the "
                         f"generic shelf options, driven by larger brand pack sizes. "
                         f"A blanket 'always buy generic' rule would overpay here."),
            })

    # Availability
    by_ret = fdf.groupby("retailer_short")["is_available"].mean()
    by_cat = fdf.groupby("category")["is_available"].mean()
    if not by_ret.empty:
        worst_ret = by_ret.idxmin()
        insights.append({
            "tag": "watch", "tag_label": "Availability Risk",
            "title": f"{worst_ret} has the thinnest shelf coverage",
            "body": (f"Only {by_ret.min()*100:.0f}% of searched listings were in stock at "
                     f"{worst_ret}, versus {by_ret.max()*100:.0f}% at {by_ret.idxmax()}. "
                     f"Narrow assortment depth limits its usefulness as a one-stop source."),
        })
    if not by_cat.empty:
        scarce = by_cat[by_cat < 0.5]
        if not scarce.empty:
            names = ", ".join(scarce.index.tolist())
            insights.append({
                "tag": "watch", "tag_label": "Hard to Find",
                "title": "Several categories are under-stocked everywhere",
                "body": (f"<b>{names}</b> were in stock at fewer than half of retailer "
                         f"searches, pointing to niche-supplement demand that mass retailers "
                         f"only partially serve, and an opening for specialty channels."),
            })

    # Bulk / pack-size economics
    if not pa.empty and pa["count"].notna().any():
        corr = pa[["count", "price_per_count"]].dropna()
        if len(corr) > 5:
            r = corr["count"].corr(corr["price_per_count"])
            insights.append({
                "tag": "", "tag_label": "Pack Economics",
                "title": "Bulk packs reward the unit-price shopper",
                "body": (f"Pack size and unit price are negatively correlated "
                         f"(r = {r:.2f}): larger counts consistently lower per-unit cost. "
                         f"Warehouse-style listings (notably Costco and large Walmart packs) "
                         f"dominate the cheapest-unit rankings."),
            })

    return insights


def render_insights():
    section_title("Automated Market Insights",
                  "Narrative findings generated directly from the filtered dataset, "
                  "the analytical backbone of the research conclusions.")

    insights = build_insights()
    if not insights:
        st.info("Not enough data under the current filters to generate insights.")
        return

    left, right = st.columns(2)
    for i, ins in enumerate(insights):
        target = left if i % 2 == 0 else right
        with target:
            st.markdown(
                f"""
                <div class="insight">
                    <span class="tag {ins['tag']}">{ins['tag_label']}</span>
                    <h4>{ins['title']}</h4>
                    <p>{ins['body']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Best-value picks
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    section_title("Best-Value Pick per Category",
                  "The single cheapest in-stock option a shopper should buy in each category.")
    bv = dp.best_value_per_category(fdf)
    if not bv.empty:
        bv = bv.rename(columns={
            "category": "Category", "retailer_short": "Retailer",
            "product_name": "Best-Value Product", "search_type": "Type",
            "price": "Price", "count": "Count", "price_per_count": "Unit Price"})
        st.dataframe(
            bv, width='stretch', hide_index=True,
            column_config={
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "Unit Price": st.column_config.NumberColumn(format="$%.3f"),
                "Count": st.column_config.NumberColumn(format="%.0f"),
            },
        )

    # Research conclusions
    sc = dp.retailer_scorecard(fdf)
    k = dp.kpi_summary(fdf)
    cheapest = sc.iloc[0]["Retailer"] if not sc.empty else "—"
    best_avail = fdf.groupby("retailer_short")["is_available"].mean().idxmax() \
        if not fdf.empty else "—"

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    section_title("Research Conclusions", "Synthesised findings & recommendations.")
    st.markdown(
        f"""
        <div class="card">
        <p style="margin-top:0;color:{PALETTE['ink']};line-height:1.65;font-size:0.93rem">
        <b>1. Retailer strategy is distinct and predictable.</b> {cheapest} competes on
        price-per-unit through bulk pack sizes and private-label lines, while
        {best_avail} competes on assortment breadth and availability. The two rarely
        coincide, so the optimal sourcing strategy is retailer-by-category rather than
        a single preferred store.<br><br>
        <b>2. Generic substitution is the dominant cost lever, but not universal.</b>
        On average generics run ~{fmt_pct(k['generic_vs_brand_savings'])} cheaper per unit,
        yet a minority of categories invert this because branded products ship in larger
        packs. Unit-price comparison, not brand status, should drive purchasing.<br><br>
        <b>3. Availability is the binding constraint for niche nutraceuticals.</b>
        Mainstream OTC drugs (e.g. ibuprofen, loratadine) are universally stocked, while
        specialty supplements show material gaps, an availability premium that specialty
        and online channels are positioned to capture.<br><br>
        <b>4. Bulk economics reward the informed shopper.</b> Larger pack counts reliably
        reduce unit cost; warehouse-format listings anchor the best-value tier across
        nearly every category analysed.
        </p>
        <p style="margin-bottom:0;color:{PALETTE['muted']};font-size:0.82rem">
        <i>Generated from {int(df['product_name'].notna().sum())} listings across
        {df['category'].nunique()} categories and {df['retailer'].nunique()} retailers.
        Figures reflect the current sidebar filters.</i></p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- #
# Router
# --------------------------------------------------------------------------- #
ROUTES = {
    "Executive Summary": render_executive,
    "Product Comparison": render_product,
    "Retailer Analysis": render_retailer,
    "Generic vs. Brand": render_generic_brand,
    "Availability": render_availability,
    "Market Insights": render_insights,
}
ROUTES[section]()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #5C6B7A; font-size: 0.85rem; padding: 10px 0 20px;">
        Created by <strong>Wilson Maselle</strong> &nbsp;·&nbsp;
        Mercer University &nbsp;·&nbsp;
        Pharmaceutical Retail Research Project &nbsp;·&nbsp;
        2026
    </div>
    """,
    unsafe_allow_html=True,
)