import streamlit as st
import pandas as pd

from utils.data_processing import load_daily_price_data, create_wide_price_df,load_daily_ratio_data
from utils.visualizations import plot_index_deepdive,plot_correlation_heatmap,plot_financial_ratios

# Load data
df = load_daily_price_data()
ratio_df = load_daily_ratio_data()



def index_deepdive(df):
    # Sidebar filters
    st.sidebar.header("Filters")

    # Index Type dropdown
    index_types = df['index_type'].unique()
    selected_index_type = st.sidebar.selectbox("Select Index Type", index_types, index=1)

    # Index Name multiselect
    index_names = df[df['index_type'] == selected_index_type]['symbol'].unique()
    selected_indices = st.sidebar.multiselect("Select Indices", index_names)

    # Date range slider
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    start_date = st.sidebar.date_input(
        "Select Date Range",
        min_date,
        min_value=min_date,
        max_value=max_date
    )
    
    end_date = st.sidebar.date_input(
        "Select Date Range",
        max_date,
        min_value=min_date,
        max_value=max_date
    )

    # Filter data based on selections
    filtered_df = df[
        (df['index_type'] == selected_index_type) &
        (df['symbol'].isin(selected_indices)) &
        (df['date'].dt.date >= start_date) &
        (df['date'].dt.date <= end_date)
    ].pipe(create_wide_price_df)
    
    filtered_ratio_df = ratio_df[
        (ratio_df['symbol'].isin(selected_indices)) &
        (ratio_df['date'].dt.date >= start_date) &
        (ratio_df['date'].dt.date <= end_date)
    ]

    # Create tabs
    tab1, tab2 = st.tabs(["Historical Timeseries", "Rolling Timeseries"])

    with tab1:
        index_timeseries_plots = plot_index_deepdive(filtered_df, selected_indices)
        #index_correlation_plots = plot_correlation_heatmap(filtered_df,selected_indices)
        index_val_plot = plot_financial_ratios(filtered_ratio_df,selected_indices)
        try:
            st.plotly_chart(index_timeseries_plots, use_container_width=True)
            #st.plotly_chart(index_correlation_plots, use_container_width=True)
            st.plotly_chart(index_val_plot, use_container_width=True)
        except Exception as e:
            st.write('Please select the symbol from the dropdown to continue')

    with tab2:
        st.write("Work in Progress")

index_deepdive(df)