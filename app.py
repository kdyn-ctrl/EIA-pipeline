import os
import sqlite3
import pandas as pd
import streamlit as st

# 1. Page Configuration & Theme
st.set_page_config(
    page_title="EIA Weekly Petroleum Fundamentals",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = "inventory.db"
CSV_PATH = "data/latest_inventory.csv"


@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    """Load inventory data from SQLite database or fallback CSV."""
    if os.path.exists(DB_PATH):
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql_query(
                """
                SELECT period, product_name, area_name, inventory_barrels, ingested_at
                FROM petroleum_inventory
                ORDER BY period DESC, product_name ASC, area_name ASC
                """,
                conn,
            )
            return df
    elif os.path.exists(CSV_PATH):
        return pd.read_csv(CSV_PATH)
    else:
        return pd.DataFrame(
            columns=["period", "product_name", "area_name", "inventory_barrels", "ingested_at"]
        )


df = load_data()

# 2. Sidebar Controls & Metadata
with st.sidebar:
    st.header("⚙️ Pipeline Controls")
    st.caption("Live Fundamental Data from U.S. EIA API v2")

    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.subheader("📚 Energy Domain Glossary")
    st.markdown(
        """
        - **MBBL:** Thousand Barrels (*1 MBBL = 1,000 Barrels*).
        - **PADD 1:** East Coast (Major demand center).
        - **PADD 2:** Midwest (Refining & storage hub).
        - **PADD 3:** Gulf Coast (Primary US refining & export hub).
        - **PADD 4:** Rocky Mountains.
        - **PADD 5:** West Coast (Isolated market).
        """
    )
    st.markdown("---")
    st.subheader("👨‍💻 Developer")
    st.markdown(
        """
        **Kdyn Cunningham**  
        *University of Florida / FSCJ*  
        [GitHub Repository](https://github.com/kdyn-ctrl/EIA-pipeline)
        """
    )

# 3. Main Dashboard Header
st.title("🛢️ U.S. Weekly Petroleum Inventory Dashboard")
st.markdown(
    "Automated fundamental supply/demand tracking for Crude Oil, RBOB Gasoline, and Distillate Fuel Oil."
)

if df.empty:
    st.warning("⚠️ No data available in `inventory.db`. Run `python pipeline.py` to ingest weekly data.")
    st.stop()

# 4. Top-level Summary Metrics (National Totals for latest period)
latest_period = df["period"].max()
latest_us = df[(df["period"] == latest_period) & (df["area_name"] == "U.S.")]

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="📅 Reporting Period",
        value=str(latest_period),
    )

with col2:
    crude_row = latest_us[latest_us["product_name"].str.contains("Crude", case=False, na=False)]
    crude_val = crude_row["inventory_barrels"].values[0] if not crude_row.empty else 0
    st.metric(
        label="Total U.S. Crude Oil",
        value=f"{crude_val:,.0f} MBBL",
    )

with col3:
    gas_row = latest_us[latest_us["product_name"].str.contains("Gasoline", case=False, na=False)]
    gas_val = gas_row["inventory_barrels"].values[0] if not gas_row.empty else 0
    st.metric(
        label="Total U.S. Gasoline Blending",
        value=f"{gas_val:,.0f} MBBL",
    )

with col4:
    dist_row = latest_us[latest_us["product_name"].str.contains("Distillate", case=False, na=False)]
    dist_val = dist_row["inventory_barrels"].values[0] if not dist_row.empty else 0
    st.metric(
        label="Total U.S. Distillate Oil",
        value=f"{dist_val:,.0f} MBBL",
    )

st.markdown("---")

# 5. Interactive Visualizations & Analytics
st.subheader("📊 Regional Inventory Breakdown (PADD Comparison)")

col_filter1, col_filter2 = st.columns(2)
with col_filter1:
    products = sorted(df["product_name"].unique())
    selected_product = st.selectbox("Select Commodity Product:", products)

with col_filter2:
    periods = sorted(df["period"].unique(), reverse=True)
    selected_period = st.selectbox("Select Report Period:", periods)

# Filter dataframe for charts
padd_df = df[
    (df["product_name"] == selected_product)
    & (df["period"] == selected_period)
    & (df["area_name"] != "U.S.")
].sort_values(by="inventory_barrels", ascending=False)

if not padd_df.empty:
    st.bar_chart(
        data=padd_df,
        x="area_name",
        y="inventory_barrels",
        color="area_name",
        use_container_width=True,
    )
else:
    st.info("No regional PADD breakdown for this selection.")

st.markdown("---")

# 6. Full Data Table & CSV Download
st.subheader("📋 Searchable Inventory Table")

filter_area = st.multiselect(
    "Filter by Geographic Area:",
    options=sorted(df["area_name"].unique()),
    default=sorted(df["area_name"].unique()),
)

filtered_df = df[
    (df["product_name"] == selected_product)
    & (df["area_name"].isin(filter_area))
]

st.dataframe(
    filtered_df,
    column_config={
        "period": "Period (Date)",
        "product_name": "Product Series",
        "area_name": "Region / PADD",
        "inventory_barrels": st.column_config.NumberColumn(
            "Volume (MBBL)",
            format="%d MBBL",
        ),
        "ingested_at": "Ingestion Timestamp",
    },
    use_container_width=True,
    hide_index=True,
)

csv_data = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Download Filtered Data as CSV",
    data=csv_data,
    file_name=f"eia_inventory_{selected_product.replace(' ', '_')}.csv",
    mime="text/csv",
)
