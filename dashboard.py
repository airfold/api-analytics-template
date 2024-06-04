import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# Streamlit app configuration
st.set_page_config(
    page_title="API Monitoring",
    layout="wide",
    page_icon="📊",
    menu_items={
        "Get help": "https://github.com/airfold/api-analytics-template",
        "About": "https://www.airfold.co",
    },
)

# Constants and environment variables
api_url = "https://api.airfold.co/v1"
api_token = os.getenv("AIRFOLD_API_KEY")


def pipe_to_df(pipe, params=None, api_token=None):
    if not api_token:
        api_token = os.getenv("AIRFOLD_API_KEY")

    url = f"{api_url}/pipes/{pipe}.json"
    headers = {"Authorization": f"Bearer {api_token}"}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()["data"]
        df = pd.DataFrame(data)
        return df
    else:
        response.raise_for_status()


def get_total_metrics(api_token=None):
    return pipe_to_df("totals", api_token=api_token)


def get_metrics(
    time_range=None,
    api_token=None,
):
    params = {}
    if time_range:
        params["time_range"] = time_range

    df = pipe_to_df("metrics", params=params, api_token=api_token)
    df["ts"] = pd.to_datetime(df["ts"])

    # Convert relevant columns to floats
    int_columns = [
        "request_count",
        "error_count",
    ]
    df[int_columns] = df[int_columns].astype(float)

    # fill NaNs in quantile/average with zeros
    df = df.fillna(value=0)
    return df


# Sidebar for filters
with st.sidebar:
    st.image(
        "https://i.gyazo.com/b8ea59576765a4b5065b8cf1ef9e701d.png",
        width=200,
    )

    time_range = st.slider(label="Select range in minutes", min_value=5, max_value=60, step=1, value=30)
    # Refresh button
    refresh_button = st.button("Refresh")


df = get_metrics(api_token=api_token, time_range=time_range)
total_df = get_total_metrics(api_token=api_token)

print(df)


# Display high-level metrics
def display_metrics(df):
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Requests", total_df["request_count"][0])
        col2.metric("Total Errors", total_df["error_count"][0])
        col3.metric("Average Latency", str(total_df["latency_p50"][0]) + "ms")


# Display charts
def display_charts(df):
    if not df.empty:
        col1, col2 = st.columns(2)
        fig1 = px.line(
            df,
            x="ts",
            y=["request_count", "error_count"],
            title="Total Requests",
            labels={"value": "Requests", "variable": "Metric"},
        )
        col1.plotly_chart(fig1)

        fig2 = px.line(
            df,
            x="ts",
            y=["latency_p50", "latency_p95"],
            title="Latency",
            labels={"value": "Latency", "variable": "Metric"},
        )
        col2.plotly_chart(fig2)


# Main content
with st.spinner("Loading data..."):
    display_metrics(total_df)
    display_charts(df)
