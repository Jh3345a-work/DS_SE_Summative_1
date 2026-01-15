import pandas as pd
import matplotlib.pyplot as plt
import pytest
from streamlit_app import fetch_population_data, filter_population_df, fig_population_by_region, fig_pie_population, fig_population_share_change
from io import StringIO
from unittest.mock import patch

# This is my quick sanity check to ensure tests are running
def test_imports():
    import streamlit_app
    assert hasattr(streamlit_app, "fetch_population_data")



@patch("requests.get")
def test_fetch_population_data(mock_get):
    '''
    This is my TDD test implemented prior to developing fetch_population_data. 
    '''
    # Here I am setting up the mock response
    mock_csv = "DATE,GEOGRAPHY_TYPE,GEOGRAPHY_NAME,OBS_VALUE\n2020,regions,North East,1000000"
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = mock_csv
    mock_get.return_value.raise_for_status = lambda: None

    # This calls the function with year 2020
    df = fetch_population_data("2020")

    # This asserts that a DataFrame is returned with expected content
    assert isinstance(df, pd.DataFrame)
    assert "DATE" in df.columns
    assert df.iloc[0]["GEOGRAPHY_NAME"] == "North East"
    assert df.iloc[0]["OBS_VALUE"] == 1000000


# Unit Test 1: Test filter_population_df
def test_filter_population_df():
    # Sample input DataFrame
    data = {
        "DATE": ["2020", "2021"],
        "GEOGRAPHY_CODE": ["E12000001", "E12000002"],
        "GEOGRAPHY_TYPE": ["regions", "regions"],
        "GEOGRAPHY_NAME": ["North East", "North West"],
        "OBS_VALUE": ["1000000", "2000000"]
    }
    df = pd.DataFrame(data)

    filtered = filter_population_df(df)

    # This checks column names
    assert set(filtered.columns) == {"YEAR", "REGION", "GEOGRAPHY_CODE", "COUNT OF POPULATION"}
    # This checks the data types
    assert filtered["YEAR"].dtype == int
    assert filtered["COUNT OF POPULATION"].dtype == int

# Unit Test 2: Test fig_population_by_region
def test_fig_population_by_region():
    df = pd.DataFrame({
        "REGION": ["A", "B"],
        "COUNT OF POPULATION": [1000000, 2000000]
    })
    fig = fig_population_by_region(df, 2023)
    assert isinstance(fig, plt.Figure) # This checks that the Figure object is returned correctly using the sample data

# Unit Test 3: Test fig_pie_population
def test_fig_pie_population():
    df = pd.DataFrame({
        "REGION": ["A", "B"],
        "COUNT OF POPULATION": [1000000, 2000000]
    })
    fig = fig_pie_population(df, 2024)
    assert isinstance(fig, plt.Figure) # This checks that the Figure object is returned correctly using the sample data

# Unit Test 4: Test fig_population_share_change
def test_fig_population_share_change():
    df23 = pd.DataFrame({"REGION": ["A", "B"], "COUNT OF POPULATION": [1000000, 2000000]})
    df24 = pd.DataFrame({"REGION": ["A", "B"], "COUNT OF POPULATION": [1500000, 2500000]})
    fig = fig_population_share_change(df23, df24)
    assert isinstance(fig, plt.Figure) # This checks that the Figure object is returned correctly using the sample data
