from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
import plotly.express as px
import streamlit as st

from train import build_daily_sales, clean_data, load_data


DATA_PATH = Path("data/raw/train.csv")
MODEL_PATH = Path("models/sales_forecast_sarimax.joblib")


@st.cache_data
def get_clean_data(path: Path) -> pd.DataFrame:
    return clean_data(load_data(path))


def apply_filters(df: pd.DataFrame, regions: list[str], categories: list[str], segments: list[str], date_range):
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    filtered = df[
        (df["Region"].isin(regions))
        & (df["Category"].isin(categories))
        & (df["Segment"].isin(segments))
        & (df["Order Date"].between(start_date, end_date))
    ]
    return filtered


def forecast_next_days(horizon: int) -> pd.DataFrame:
    if not MODEL_PATH.exists():
        return pd.DataFrame()

    artifact = joblib.load(MODEL_PATH)
    model = artifact["model"]
    forecast = model.forecast(steps=horizon)
    return pd.DataFrame({"Date": forecast.index, "Forecast Sales": forecast.values})


st.set_page_config(page_title="Superstore Sales Dashboard", layout="wide")
st.title("Superstore Sales Analytics Dashboard")

if not DATA_PATH.exists():
    st.error("Raw dataset not found. Expected data/raw/train.csv.")
    st.stop()

df = get_clean_data(DATA_PATH)

with st.sidebar:
    st.header("Filters")
    regions = st.multiselect("Region", sorted(df["Region"].unique()), default=sorted(df["Region"].unique()))
    categories = st.multiselect("Category", sorted(df["Category"].unique()), default=sorted(df["Category"].unique()))
    segments = st.multiselect("Segment", sorted(df["Segment"].unique()), default=sorted(df["Segment"].unique()))
    date_range = st.date_input(
        "Order date range",
        value=(df["Order Date"].min().date(), df["Order Date"].max().date()),
        min_value=df["Order Date"].min().date(),
        max_value=df["Order Date"].max().date(),
    )
    horizon = st.slider("Forecast horizon", min_value=7, max_value=60, value=14, step=7)

if len(date_range) != 2:
    st.warning("Pick a start and end date to update the dashboard.")
    st.stop()

filtered = apply_filters(df, regions, categories, segments, date_range)

total_sales = filtered["Sales"].sum()
orders = filtered["Order ID"].nunique()
customers = filtered["Customer ID"].nunique()
avg_order_value = total_sales / orders if orders else 0

kpi_1, kpi_2, kpi_3, kpi_4 = st.columns(4)
kpi_1.metric("Total Sales", f"${total_sales:,.0f}")
kpi_2.metric("Orders", f"{orders:,}")
kpi_3.metric("Customers", f"{customers:,}")
kpi_4.metric("Avg Order Value", f"${avg_order_value:,.0f}")

if filtered.empty:
    st.info("No rows match the selected filters.")
    st.stop()

daily = build_daily_sales(filtered)
monthly = filtered.assign(Month=filtered["Order Date"].dt.to_period("M").dt.to_timestamp())
monthly = monthly.groupby("Month", as_index=False)["Sales"].sum()

left, right = st.columns(2)
with left:
    st.plotly_chart(
        px.line(monthly, x="Month", y="Sales", markers=True, title="Monthly Sales Trend"),
        use_container_width=True,
    )
with right:
    by_region = filtered.groupby("Region", as_index=False)["Sales"].sum().sort_values("Sales", ascending=False)
    st.plotly_chart(px.bar(by_region, x="Region", y="Sales", title="Sales by Region"), use_container_width=True)

left, right = st.columns(2)
with left:
    by_category = filtered.groupby("Category", as_index=False)["Sales"].sum().sort_values("Sales", ascending=False)
    st.plotly_chart(px.bar(by_category, x="Category", y="Sales", color="Category", title="Sales by Category"), use_container_width=True)
with right:
    by_segment = filtered.groupby("Segment", as_index=False)["Sales"].sum().sort_values("Sales", ascending=False)
    st.plotly_chart(px.pie(by_segment, names="Segment", values="Sales", title="Sales Mix by Segment"), use_container_width=True)

top_products = (
    filtered.groupby("Product Name", as_index=False)["Sales"]
    .sum()
    .sort_values("Sales", ascending=False)
    .head(10)
)
st.plotly_chart(
    px.bar(top_products, x="Sales", y="Product Name", orientation="h", title="Top 10 Products by Sales"),
    use_container_width=True,
)

forecast_df = forecast_next_days(horizon)
if forecast_df.empty:
    st.warning("Forecast model not found yet. Run `python train.py` first.")
else:
    st.plotly_chart(
        px.line(forecast_df, x="Date", y="Forecast Sales", markers=True, title=f"Next {horizon} Days Sales Forecast"),
        use_container_width=True,
    )

csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button("Download filtered data", data=csv, file_name="filtered_superstore_sales.csv", mime="text/csv")
