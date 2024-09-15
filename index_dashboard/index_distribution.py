import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
from utils.data_processing import load_daily_price_data, performance_stats_instruments, calculate_returns_wide
from utils.visualizations import plot_index_returns_boxplots, plot_index_returns_histograms

#load data
df = load_daily_price_data()
def index_distribution(df):

    # Sidebar filters
    st.sidebar.header("Filters")

    # Index Type dropdown
    index_types = df['index_type'].unique()
    selected_index_type = st.sidebar.selectbox("Select Index Type", index_types)

    # Index Category dropdown
    index_categories = df[df['index_type'] == selected_index_type]['index_category'].unique()
    selected_index_category = st.sidebar.selectbox("Select Index Category", index_categories)

    # Date range slider
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    start_date, end_date = st.sidebar.date_input(
        "Select Date Range",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    # Filter data based on selections
    filtered_df = df[
        (df['index_type'] == selected_index_type) &
        (df['index_category'] == selected_index_category) &
        (df['date'].dt.date >= start_date) &
        (df['date'].dt.date <= end_date)
    ]

    # Display boxplot
    boxplot_fig = plot_index_returns_boxplots(filtered_df, selected_index_type, selected_index_category)
    st.plotly_chart(boxplot_fig,use_container_width=True)
    
    # Performance stats
    st.header('NIFTY Indices performance stats')
    st.dataframe(performance_stats_instruments(calculate_returns_wide(filtered_df,'simple')),use_container_width=True)
    
    logrets_df = calculate_returns_wide(filtered_df)
    index_list =  logrets_df.columns.to_list()
    st.header('Nifty Indices Returns')
    selected_index = st.multiselect('select index', options= index_list)
    st.dataframe(
            (logrets_df.stack()
            .reset_index()
            .groupby(['symbol',pd.Grouper(key = 'date',freq='ME')])
            .sum()
            .reset_index()
            .assign(year = lambda x: x.date.dt.year.astype('str'),
                    month = lambda x: x.date.dt.month)
            .pivot(columns='month',values=0,index= ['symbol','year'])
            .assign(ytd = lambda x:x.sum(axis=1))
            .apply(np.expm1)
            .mul(100)
            .reset_index()
            .query('symbol in @selected_index')
            .style.format('{:.1f}%',na_rep='-',subset=[ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 'ytd'])
            ),use_container_width=True
        )
    
    # # Display histogram
    # histogram_fig = plot_index_returns_histograms(filtered_df, selected_index_type, selected_index_category)
    # st.plotly_chart(histogram_fig)

index_distribution(df)  