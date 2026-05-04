import os
import psycopg2
import polars as pl
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# --- Config ---
st.set_page_config(
    page_title="NYC vs SF Dashboard",
    page_icon="🌆",
    layout="wide"
)

CITY_LABELS = {
    "nyc": "New York City",
    "sf": "San Francisco"
}

# --- Database ---
@st.cache_resource
def get_connection():
    return psycopg2.connect(os.getenv("SUPABASE_DB_URL"))

@st.cache_data(ttl=3600)
def query(sql):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql)
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    return pl.DataFrame(rows, schema=columns, orient="row")

# --- Header ---
st.title("🌆 NYC vs SF — Cost & Quality of Life")
st.caption("A live ELT pipeline comparing New York City and San Francisco across weather, housing, and cost of living.")

st.divider()

# --- Section 1: Today's Weather ---
st.header("🌤️ Today's Weather")

weather = query("""
    SELECT city, date, temp_max_f, temp_min_f, precipitation_mm
    FROM raw_weather
    WHERE date = (SELECT MAX(date) FROM raw_weather)
    ORDER BY city
""")

col1, col2 = st.columns(2)

for i, city in enumerate(["nyc", "sf"]):
    row = weather.filter(pl.col("city") == city)
    if not row.is_empty():
        r = row.row(0, named=True)
        col = col1 if i == 0 else col2
        with col:
            st.subheader(CITY_LABELS[city])
            m1, m2, m3 = st.columns(3)
            m1.metric("High", f"{r['temp_max_f']}°F")
            m2.metric("Low", f"{r['temp_min_f']}°F")
            m3.metric("Precipitation", f"{r['precipitation_mm']}mm")

st.divider()

# --- Section 2: Rent Trends ---
st.header("🏠 Median Rent Over Time")

housing = query("""
    SELECT city, date::text, median_rent
    FROM raw_housing
    ORDER BY date
""")

housing = housing.with_columns(
    pl.col("city").replace(CITY_LABELS),
    pl.col("median_rent").cast(pl.Float64)
)
housing_pivot = housing.pivot(index="date", on="city", values="median_rent")

st.line_chart(housing_pivot, x="date", y=["New York City", "San Francisco"])

st.divider()

# --- Section 3: CPI Trends ---
st.header("📈 Cost of Living (CPI) Over Time")

cpi = query("""
    SELECT city, TO_CHAR(date, 'YYYY-MM') as date, cpi
    FROM raw_cpi
    ORDER BY date
""")

cpi = cpi.with_columns(
    pl.col("city").replace(CITY_LABELS),
    pl.col("cpi").cast(pl.Float64)
)
cpi_pivot = cpi.pivot(
    index="date", on="city", values="cpi"
).with_columns([
    pl.col("New York City").cast(pl.Float64),
    pl.col("San Francisco").cast(pl.Float64).interpolate()
])

st.line_chart(cpi_pivot, x="date", y=["New York City", "San Francisco"])

st.divider()
st.caption("Data sources: Open-Meteo, Zillow ZORI, BLS CPI API")