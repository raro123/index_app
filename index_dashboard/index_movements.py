import streamlit as st
import pandas as pd
from datetime import datetime
from utils.data_processing import load_daily_price_data, calculate_returns_wide, robust_vol
from utils.visualizations import plot_performance

# load data
df = load_daily_price_data()


def index_movement(df):
    resample_dict = {'Daily': None, 'Weekly': 'W-FRI',
                     'Monthly': 'ME', 'Quarterly': 'QE', 'Annual': 'YE'}

    # Sidebar filters
    st.sidebar.header("Filters")

    # Index Type dropdown
    index_types = df['index_type'].unique()
    selected_index_type = st.sidebar.selectbox(
        "Select Index Type", index_types)

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

    n_periods = st.sidebar.slider("Select number of periods",
                                  min_value=1, max_value=5, value=3)

    granularity = st.sidebar.selectbox('Select the Period Granularity', [
                                       'Daily', 'Weekly', 'Monthly', 'Quarterly', 'Annual'])

        # Filter data based on selections
    filtered_df = df[
        (df['index_type'] == selected_index_type) &
        (df['date'].dt.date >= start_date) &
        (df['date'].dt.date <= end_date)
    ]

    logrets_broad_df = calculate_returns_wide(filtered_df.query('index_category=="BROAD"'), resample=resample_dict[granularity])
    logrets_sectoral_df = calculate_returns_wide(filtered_df.query('index_category=="SECTORAL"'), resample=resample_dict[granularity])
    logrets_vol_broad_df = logrets_broad_df.apply(robust_vol)
    logrets_vol_sectoral_df = logrets_sectoral_df.apply(robust_vol)
    
    tab1, tab2 = st.tabs(["Broad Index Movements", "Sectoral Index Movements"])
    with tab1:
            zscore_broad_df = logrets_broad_df/logrets_vol_broad_df
            fig_z_price_broad = plot_performance(zscore_broad_df, n_periods)
            fig_rets_price_broad = plot_performance(logrets_broad_df, n_periods, data_zscored=False)
            fig_vol_price_broad = plot_performance(logrets_vol_broad_df, n_periods, data_zscored=False)

            st.subheader("NIFTY Broad Price Indices Performance")
            st.plotly_chart(fig_z_price_broad, use_container_width=True)
            st.plotly_chart(fig_rets_price_broad, use_container_width=True)
            st.plotly_chart(fig_vol_price_broad, use_container_width=True)
    with tab2:
            zscore_sectoral_df = logrets_sectoral_df/logrets_vol_sectoral_df
            fig_z_price_sect = plot_performance(zscore_sectoral_df, n_periods)
            fig_rets_price_sect = plot_performance(logrets_sectoral_df, n_periods, data_zscored=False)
            fig_vol_price_sect = plot_performance(logrets_vol_sectoral_df, n_periods, data_zscored=False)


            st.subheader("NIFTY Sectoral Price Indices Performance")
            st.plotly_chart(fig_z_price_sect, use_container_width=True)
            st.plotly_chart(fig_rets_price_sect, use_container_width=True)
            st.plotly_chart(fig_vol_price_sect, use_container_width=True)


index_movement(df)
