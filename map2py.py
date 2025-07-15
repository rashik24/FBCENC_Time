import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# ────────────────────────────────
# CONFIG
# ────────────────────────────────

st.set_page_config(layout="wide")
st.title("Access Score Map Explorer")

# ────────────────────────────────
# LOAD DATA
# ────────────────────────────────

# Load cleaned CSV
final_results_cleaned = pd.read_csv('/Users/rsiddiq2/Downloads/llama-index/final_cleaned.csv')

# Load shapefile
tracts_gdf = gpd.read_file("/Users/rsiddiq2/Downloads/llama-index/cb_2023_37_tract_500k.shp")
counties_of_interest = [
    "Brunswick County",
    "Carteret County",
    "Chatham County",
    "Columbus County",
    "Craven County",
    "Duplin County",
    "Durham County",
    "Edgecombe County",
    "Franklin County",
    "Granville County",
    "Greene County",
    "Halifax County",
    "Harnett County",
    "Johnston County",
    "Jones County",
    "Lee County",
    "Lenoir County",
    "Moore County",
    "Nash County",
    "New Hanover County",
    "Onslow County",
    "Orange County",
    "Pamlico County",
    "Pender County",
    "Person County",
    "Pitt County",
    "Richmond County",
    "Sampson County",
    "Scotland County",
    "Vance County",
    "Wake County",
    "Warren County",
    "Wayne County",
    "Wilson County"
]

county_column = "NAMELSADCO"

# Filter to only those counties
tracts_gdf = tracts_gdf[
    tracts_gdf[county_column].isin(counties_of_interest)
]

# Ensure GEOIDs match
tracts_gdf["GEOID"] = tracts_gdf["GEOID"].astype(str)
final_results_cleaned["GEOID"] = final_results_cleaned["GEOID"].astype(str)

# ────────────────────────────────
# FUNCTION TO EXTRACT HOUR
# ────────────────────────────────

def extract_start_hour(window_str):
    """
    Extracts the starting hour (int) from a time window string like '12:00–13:59'
    """
    if pd.isna(window_str):
        return None
    try:
        start_time = window_str.split("–")[0]
        hour = int(start_time.split(":")[0])
        return hour
    except Exception:
        return None

# Create hour_numeric column FIRST
final_results_cleaned["hour_numeric"] = final_results_cleaned["hour"].apply(extract_start_hour)

# ────────────────────────────────
# USER SELECTIONS
# ────────────────────────────────

# Choose week
available_weeks = sorted(final_results_cleaned["week"].dropna().unique())
week_val = st.selectbox("Select Week", available_weeks)

# Now filter week_data AFTER hour_numeric exists
week_data = final_results_cleaned[
    final_results_cleaned["week"] == week_val
]

# Choose day
available_days = sorted(week_data["day"].dropna().unique())
day_val = st.selectbox("Select Day", available_days)

# Filter to this day
week_day_data = week_data.loc[
    week_data["day"] == day_val
].dropna(subset=["hour_numeric"])

# Find unique hours
hours_available = (
    week_day_data["hour_numeric"]
    .dropna()
    .sort_values()
    .unique()
)

if len(hours_available) == 0:
    st.warning("No data available for this day.")
    st.stop()

# Slider for hour
hour_val = st.slider(
    "Select Hour",
    min_value=int(hours_available.min()),
    max_value=int(hours_available.max()),
    value=int(hours_available.min()),
    step=1,
)

# ────────────────────────────────
# FILTER FINAL DATA
# ────────────────────────────────

subset = final_results_cleaned[
    (final_results_cleaned["week"] == week_val) &
    (final_results_cleaned["day"] == day_val) &
    (final_results_cleaned["hour_numeric"] == hour_val)
]

if subset.empty:
    st.warning("No data for this time slice.")
else:
    vmin_local = subset["Access_Score"].min()
    vmax_local = subset["Access_Score"].max()

    if vmin_local == vmax_local:
        vmin_local -= 1
        vmax_local += 1

    # Merge with shapefile
    merged_gdf = tracts_gdf.merge(
        subset,
        on="GEOID",
        how="left"
    )
    merged_gdf["Access_Score"] = merged_gdf["Access_Score"].fillna(0)

    # Plot map
    fig, ax = plt.subplots(1, 1, figsize=(6, 6))
    merged_gdf.plot(
        column="Access_Score",
        cmap="OrRd",
        linewidth=0.2,
        edgecolor="gray",
        legend=True,
        ax=ax,
        vmin=vmin_local,
        vmax=vmax_local
    )
    #ax.set_title(f"Access Score Map\nWeek {week_val}, {day_val}, Hour {hour_val}", fontsize=16)
    ax.axis("off")

    st.pyplot(fig)
