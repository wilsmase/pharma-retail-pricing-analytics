"""
data_processing.py
==================
Data loading, cleaning, and feature-engineering utilities for the
Pharmaceutical Retail Pricing Analytics dashboard.

The source spreadsheet uses an Excel "merged cell" layout: Brand Name,
Generic Name and Retailer are only written on the first row of each group
and left blank for the rows beneath them. Search Type ("Generic"/"Brand")
behaves the same way within each retailer block. This module reconstructs a
fully-populated tidy (one-row-per-observation) dataframe from that layout so
the rest of the application can rely on clean, analysis-ready data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Canonical column order produced by ``load_and_clean``.
COLUMNS = [
    "brand_name",
    "generic_name",
    "retailer",
    "product_name",
    "search_type",
    "price",
    "count",
    "strength",
    "price_per_count",
    "availability",
]

# Map the long retailer names in the file to short display labels.
RETAILER_SHORT = {
    "CVS Pharmacy": "CVS",
    "Walmart": "Walmart",
    "Costco Wholesale": "Costco",
}


def load_and_clean(source) -> pd.DataFrame:
    """Read the raw workbook and return a tidy, fully-populated dataframe.

    Parameters
    ----------
    source : str | path-like | file-like
        Path to (or an uploaded buffer of) the pricing workbook.

    Returns
    -------
    pandas.DataFrame
        One row per product observation with hierarchical fields
        forward-filled, ``"N/A"`` converted to proper missing values, and
        numeric columns coerced to floats.
    """
    # The real header sits on the second row of the sheet; row 0 is a title.
    df = pd.read_excel(source, sheet_name="Raw Data Sheet", header=1)

    # Drop the empty spacer columns that sit between the merged-cell fields.
    df = df.drop(columns=[c for c in df.columns if str(c).startswith("Unnamed")])
    df.columns = COLUMNS

    # Reconstruct the merged-cell hierarchy.
    for col in ("brand_name", "generic_name", "retailer"):
        df[col] = df[col].ffill()

    # Search Type is filled per retailer block: "Generic" until "Brand" appears.
    df["search_type"] = df.groupby(
        ["brand_name", "generic_name", "retailer"], dropna=False
    )["search_type"].ffill()

    # Normalise textual placeholders to genuine missing values.
    for col in ("product_name", "strength"):
        df[col] = df[col].replace("N/A", np.nan)

    df["availability"] = (
        df["availability"].astype(str).str.strip().str.upper()
    )
    df["is_available"] = df["availability"].eq("YES")

    # Coerce numeric measures (any stray "N/A" becomes NaN).
    for col in ("price", "count", "price_per_count"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Friendly, consistent display fields used throughout the UI.
    df["retailer_short"] = df["retailer"].map(RETAILER_SHORT).fillna(df["retailer"])
    df["category"] = df["generic_name"]  # the generic compound is the category
    df["brand_generic_label"] = df["brand_name"].astype(str) + " (" + df[
        "generic_name"
    ].astype(str) + ")"

    return df


def priced_available(df: pd.DataFrame) -> pd.DataFrame:
    """Subset used for price analytics: in stock *and* carrying a price.

    Some in-stock items (e.g. prescription-only listings) have no published
    shelf price; those are excluded from price math but still counted for
    availability metrics elsewhere.
    """
    return df[df["is_available"] & df["price"].notna()].copy()


def kpi_summary(df: pd.DataFrame) -> dict:
    """Compute the headline KPIs shown on the executive summary."""
    pa = priced_available(df)
    n_listings = int(df["product_name"].notna().sum())
    avail_rate = float(df["is_available"].mean()) if len(df) else 0.0

    gen = pa[pa["search_type"] == "Generic"]["price_per_count"]
    brand = pa[pa["search_type"] == "Brand"]["price_per_count"]
    gen_brand_gap = (
        (brand.mean() - gen.mean()) / brand.mean() * 100
        if brand.mean() and not np.isnan(brand.mean())
        else np.nan
    )

    return {
        "categories": int(df["category"].nunique()),
        "retailers": int(df["retailer"].nunique()),
        "listings": n_listings,
        "availability_rate": avail_rate,
        "avg_unit_price": float(pa["price_per_count"].mean()) if len(pa) else np.nan,
        "median_unit_price": float(pa["price_per_count"].median()) if len(pa) else np.nan,
        "generic_count": int((df["search_type"] == "Generic").sum()),
        "brand_count": int((df["search_type"] == "Brand").sum()),
        "generic_vs_brand_savings": gen_brand_gap,
    }


def retailer_scorecard(df: pd.DataFrame) -> pd.DataFrame:
    """Per-retailer summary table (price competitiveness + availability)."""
    rows = []
    for retailer, grp in df.groupby("retailer_short"):
        pa = priced_available(grp)
        rows.append(
            {
                "Retailer": retailer,
                "Listings": int(grp["product_name"].notna().sum()),
                "In-Stock Rate": float(grp["is_available"].mean()),
                "Avg Price": float(pa["price"].mean()) if len(pa) else np.nan,
                "Avg Unit Price": float(pa["price_per_count"].mean())
                if len(pa)
                else np.nan,
                "Median Unit Price": float(pa["price_per_count"].median())
                if len(pa)
                else np.nan,
                "Cheapest Unit": float(pa["price_per_count"].min())
                if len(pa)
                else np.nan,
            }
        )
    out = pd.DataFrame(rows).sort_values("Avg Unit Price").reset_index(drop=True)
    return out


def generic_brand_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Average unit price split by Generic vs Brand for each category."""
    pa = priced_available(df)
    piv = (
        pa.groupby(["category", "search_type"])["price_per_count"]
        .mean()
        .unstack("search_type")
    )
    for col in ("Generic", "Brand"):
        if col not in piv.columns:
            piv[col] = np.nan
    piv = piv[["Generic", "Brand"]]
    piv["Savings vs Brand %"] = (piv["Brand"] - piv["Generic"]) / piv["Brand"] * 100
    return piv.reset_index()


def availability_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Category x Retailer matrix of in-stock rates (0-1)."""
    mat = (
        df.groupby(["category", "retailer_short"])["is_available"]
        .mean()
        .unstack("retailer_short")
    )
    return mat


def best_value_per_category(df: pd.DataFrame) -> pd.DataFrame:
    """For each category, the single cheapest in-stock unit-price listing."""
    pa = priced_available(df)
    if pa.empty:
        return pa
    idx = pa.groupby("category")["price_per_count"].idxmin()
    cols = [
        "category",
        "retailer_short",
        "product_name",
        "search_type",
        "price",
        "count",
        "price_per_count",
    ]
    return pa.loc[idx, cols].sort_values("price_per_count").reset_index(drop=True)
