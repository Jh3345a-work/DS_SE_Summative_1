import requests
import pandas as pd
from io import StringIO
import matplotlib.pyplot as plt
import numpy as np

def fetch_population_data(time_value):
    BASE = "https://www.nomisweb.co.uk/api/v01"
    DATASET = "NM_2002_1"   # Population estimates dataset
    params = {
        "time": time_value,
        "measures": 20100,         # value (not percent)
        "gender": 0,               # combined total
        "c_age": 203,              # Individuals aged 16–64
    }
    url = f"{BASE}/dataset/{DATASET}.data.csv"
    resp = requests.get(url, params=params, timeout=60)
    return pd.read_csv(StringIO(resp.text))

df_23 = fetch_population_data("2023")
df_24 = fetch_population_data("2024")

def filter_population_df(df):
    filtered_df = df[df['GEOGRAPHY_TYPE'] == 'regions']
    filtered_df = filtered_df[['DATE','GEOGRAPHY_CODE', 'GEOGRAPHY_NAME', 'OBS_VALUE']]
    filtered_df.rename(columns={'DATE': 'YEAR', 'GEOGRAPHY_NAME': 'REGION', 'OBS_VALUE': 'COUNT OF POPULATION'}, inplace=True)
    return filtered_df

filtered_df_23 = filter_population_df(df_23)
filtered_df_24 = filter_population_df(df_24)


def plot_population_by_region_2023(filtered_df_23):
    # Bar chart of population by region for 2023
    plt.figure(figsize=(10,6))
    df_plot = filtered_df_23.sort_values('COUNT OF POPULATION', ascending=False)
    plt.bar(df_plot['REGION'], df_plot['COUNT OF POPULATION'] / 1_000_000, color='C0')
    plt.xticks(rotation=45, ha='right')
    plt.ylabel('Count of Population (1,000,000s)')
    plt.title('Population by Region (2023)')
    plt.tight_layout()
    plt.show()

plot_population_by_region_2023(filtered_df_23)

def pie_population_by_region(filtered_df_24):
    plt.figure(figsize=(8, 8))
    df_plot = filtered_df_24.sort_values('COUNT OF POPULATION', ascending=False)

    values = df_plot['COUNT OF POPULATION']
    labels = df_plot['REGION']
    label_values = [f"{region}: {value:,}" for region, value in zip(labels, values)]

    wedges, _ = plt.pie(
        values,
        labels=None,
        startangle=90,
        counterclock=False
    )
    plt.legend(wedges, label_values, title="Region (Population)", loc="center left", bbox_to_anchor=(1, 0.5))
    plt.title('Population by Region (2024)')
    plt.tight_layout()
    plt.show()

pie_population_by_region(filtered_df_24)

def plot_population_share_change(filtered_df_23, filtered_df_24):
    df23 = filtered_df_23.copy(); df23['YEAR'] = 2023
    df24 = filtered_df_24.copy(); df24['YEAR'] = 2024
    df_all = pd.concat([df23, df24], ignore_index=True)

    # Compute total by year, then share (% of UK total)
    totals = df_all.groupby('YEAR')['COUNT OF POPULATION'].sum()
    df_all['SHARE_%'] = df_all.apply(lambda r: r['COUNT OF POPULATION'] / totals.loc[r['YEAR']] * 100, axis=1)

    wide_share = df_all.pivot_table(index='REGION', columns='YEAR', values='SHARE_%', aggfunc='sum')
    wide_share['PP_CHANGE'] = wide_share[2024] - wide_share[2023]  # percentage point change

    plot_df = wide_share.sort_values('PP_CHANGE', ascending=True)

    plt.figure(figsize=(10, 6))
    colors = np.where(plot_df['PP_CHANGE'] >= 0, '#72B7B2', '#E45756')
    plt.barh(plot_df.index, plot_df['PP_CHANGE'], color=colors)

    plt.xlabel('Change (percentage points)')
    plt.ylabel('Region')
    plt.title('Change in Population Share by Region (2023 to 2024)')
    plt.axvline(0, color='grey', linewidth=1)
    plt.tight_layout()
    plt.show()

plot_population_share_change(filtered_df_23, filtered_df_24)