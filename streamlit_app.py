
import requests
import pandas as pd
from io import StringIO
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

BASE = "https://www.nomisweb.co.uk/api/v01"
DATASET = "NM_2002_1"  # This defines the population estimates dataset.

@st.cache_data(show_spinner="Fetching data from NOMIS…")
def fetch_population_data(time_value: str) -> pd.DataFrame:
    '''
    This function fetches population data from NOMIS API for a given year (time_value) and stores it in a DataFrame.
    
    Parameters:
        time_value (str): The year for which to fetch data (e.g., "2023").

    Returns:
        pd.DataFrame: Raw population data returned by the NOMIS API as a parsed CSV table.

    '''
    
    params = {
        "time": time_value,
        "measures": 20100,  # This defines the measure as a numeric value (not percent).
        "gender": 0,        # This defines gender as combined total.
        "c_age": 203,       # This defines age group as 16–64. If all ages is needed, use 0.
    }
    url = f"{BASE}/dataset/{DATASET}.data.csv"
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    # Since NOMIS returns text/csv, StringIO is used to parse directly.
    return pd.read_csv(StringIO(r.text))


def filter_population_df(df: pd.DataFrame) -> pd.DataFrame:
    '''
    This function filters and cleans the raw NOMIS population DataFrame to region level records.

    Parameters:
        df (pd.DataFrame): Raw DataFrame returned from the NOMIS API.

    Returns:
        pd.DataFrame: A filtered DataFrame with REGION, YEAR, and
                      COUNT OF POPULATION columns ready for plotting.

    '''
    
    filtered = df[df["GEOGRAPHY_TYPE"] == "regions"][["DATE", "GEOGRAPHY_CODE", "GEOGRAPHY_NAME", "OBS_VALUE"]].copy()

    # This rename the columns to be suitable for the data visualisations.
    filtered.rename(
        columns={
            "DATE": "YEAR",
            "GEOGRAPHY_NAME": "REGION",
            "OBS_VALUE": "COUNT OF POPULATION",
        },
        inplace=True,
    )
    filtered["YEAR"] = pd.to_numeric(filtered["YEAR"], errors="coerce").astype("Int64")
    filtered["COUNT OF POPULATION"] = pd.to_numeric(filtered["COUNT OF POPULATION"], errors="coerce")
    
    # This check drops the rows where year or value is missing.
    filtered = filtered.dropna(subset=["YEAR", "COUNT OF POPULATION"]).copy()
    filtered["YEAR"] = filtered["YEAR"].astype(int)
    return filtered


def fig_population_by_region(df_year: pd.DataFrame, year: int):
    '''
    This function creates a bar chart showing population counts by region for a given year.

    Parameters:
        df_year (pd.DataFrame): Cleaned DataFrame containing region and population columns.
        year (int): The year displayed in the chart title.

    Returns:
        matplotlib.figure.Figure: A bar chart figure ready to be rendered in Streamlit.

    '''
    
    df_plot = df_year.sort_values("COUNT OF POPULATION", ascending=False)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(df_plot["REGION"], df_plot["COUNT OF POPULATION"] / 1_000_000, color="C0")
    ax.set_ylabel("Count of population (millions)")
    ax.set_title(f"Population by Region ({year})")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    return fig


def fig_pie_population(df_year: pd.DataFrame, year: int):
    ''' 
    This function creates a pie chart showing the population distribution by region for a given year. 
    
    Parameters:
        df_year (pd.DataFrame): Cleaned DataFrame containing regional population counts.
        year (int): The year displayed in the chart title.

    Returns:
        matplotlib.figure.Figure: A pie chart figure ready to be rendered in Streamlit.
    '''
    
    df_plot = df_year.sort_values("COUNT OF POPULATION", ascending=False)
    values = df_plot["COUNT OF POPULATION"].values
    labels = df_plot["REGION"].values
    label_values = [f"{region}: {value:,.0f}" for region, value in zip(labels, values)]

    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, _ = ax.pie(values, labels=None, startangle=90, counterclock=False)
    ax.legend(wedges, label_values, title="Region (Population)", loc="center left", bbox_to_anchor=(1, 0.5))
    ax.set_title(f"Population by Region ({year})")
    fig.tight_layout()
    return fig


def fig_population_share_change(df23: pd.DataFrame, df24: pd.DataFrame):
    '''
    This function creates a horizontal bar chart showing the change in population share by region between 2023 and 2024.

    Parameters:
        df23 (pd.DataFrame): Cleaned population data for 2023.
        df24 (pd.DataFrame): Cleaned population data for 2024.

    Returns:
        matplotlib.figure.Figure or None:
            A bar chart figure if both years are present; otherwise Non
    '''

    df23 = df23.copy(); df23["YEAR"] = 2023
    df24 = df24.copy(); df24["YEAR"] = 2024
    df_all = pd.concat([df23, df24], ignore_index=True)

    # This computes totals by year, then share (% of UK total for these regions).
    totals = df_all.groupby("YEAR")["COUNT OF POPULATION"].sum()
    df_all["SHARE_%"] = df_all.apply(lambda r: r["COUNT OF POPULATION"] / totals.loc[r["YEAR"]] * 100, axis=1)

    wide_share = df_all.pivot_table(index="REGION", columns="YEAR", values="SHARE_%", aggfunc="sum")
    # This safety check ensures both 2023 and 2024 exist in the table before calculating change.
    if not {2023, 2024}.issubset(wide_share.columns):
        return None

    wide_share["PP_CHANGE"] = wide_share[2024] - wide_share[2023]  # This calculates the percentage-point change between 2023 and 2024.
    plot_df = wide_share.sort_values("PP_CHANGE", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = np.where(plot_df["PP_CHANGE"] >= 0, "#72B7B2", "#E45756")
    ax.barh(plot_df.index, plot_df["PP_CHANGE"], color=colors)
    ax.set_xlabel("Change (percentage points)")
    ax.set_ylabel("Region")
    ax.set_title("Change in Population Share by Region (2023 → 2024)")
    ax.axvline(0, color="grey", linewidth=1)
    fig.tight_layout()
    return fig


if __name__ == "__main__":
    st.set_page_config(page_title="NOMIS Population Estimates", layout="wide")
    
    # This section designs the main and application layour for the NOMIS population estimates app. 
    # [Bug Fix] Above comment is no longer a docstring so that it is not shown within the Streamlit app.
    
    # This produces the Header Row (logo + title).
    col_logo, col_title = st.columns([1, 12])   # Adjust rations to change column widths.
    with col_logo:
        st.image("images/DfE.jpg", width=120)   # Adjust to set logo width for alignment.
    with col_title:
        st.title("NOMIS Population Estimates – Data Visualisation App")
        st.caption("Source: NOMIS API | Ages 16–64 | Measure: Absolute Value | Gender: Total")

    st.divider()

    # This section fetches data with error handling, then cleans and validates the results.
    try:
        df_23 = fetch_population_data("2023")
        df_24 = fetch_population_data("2024")
    except requests.HTTPError as e:
        st.error(f"HTTP error from NOMIS: {e}")
        st.stop()
    except requests.RequestException as e:
        st.error(f"Network error contacting NOMIS: {e}")
        st.stop()

    filtered_df_23 = filter_population_df(df_23)
    filtered_df_24 = filter_population_df(df_24)

    if filtered_df_23.empty or filtered_df_24.empty:
        st.stop()


    # This produces the 3 visualisations in separate tabs.
    tab1, tab2, tab3 = st.tabs(["Bar Chart (2023)", "Pie Chart (2024)", "Percentage Change (2023 to 2024)"])

    with tab1:   
        left, mid, right = st.columns([1, 2, 1])
        with mid:
            st.pyplot(fig_population_by_region(filtered_df_23, 2023), use_container_width=True)

    with tab2:
        left, mid, right = st.columns([1, 2, 1])
        with mid:
            st.pyplot(fig_pie_population(filtered_df_24, 2024), use_container_width=True)

    with tab3:
        left, mid, right = st.columns([1, 2, 1]) 
        with mid:
            st.pyplot(fig_population_share_change(filtered_df_23, filtered_df_24), use_container_width=True)

