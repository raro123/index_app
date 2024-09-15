import streamlit as st
import pandas as pd
from datetime import datetime
from utils.data_processing import load_daily_price_data, calculate_returns_wide, robust_vol
from utils.visualizations import plot_performance

#load data
df = load_daily_price_data()
resample_dict = {'Daily':None,'Weekly':'W-FRI', 'Monthly':'ME','Quarterly':'QE','Annual':'YE'}

# Sidebar filters
st.sidebar.header("Filters")

# Date range slider
min_date = df['date'].min().date()
max_date = df['date'].max().date()
start_date, end_date = st.sidebar.date_input(
     "Select Date Range",
      [min_date, max_date],
      min_value=min_date,
      max_value=max_date
     )

n_periods = st.sidebar.slider("Select number of periods",
                        min_value=1, max_value=5, value=3)

granularity = st.sidebar.selectbox('Select the Period Granularity', ['Daily','Weekly','Monthly','Quarterly','Annual'])

logrets_price_broad_df = calculate_returns_wide(df.query('(index_type=="PRICE")&(index_category=="BROAD")'), resample=resample_dict[granularity])
logrets_tri_broad_df = calculate_returns_wide(df.query('(index_type=="TRI")&(index_category=="BROAD")'),resample=resample_dict[granularity])
logrets_price_sectoral_df = calculate_returns_wide(df.query('(index_type=="PRICE")&(index_category=="SECTORAL")'),resample=resample_dict[granularity])
logrets_tri_sectoral_df = calculate_returns_wide(df.query('(index_type=="TRI")&(index_category=="SECTORAL")'),resample=resample_dict[granularity])
logrets_vol_price_broad_df = logrets_price_broad_df.apply(robust_vol)
logrets_vol_tri_broad_df = logrets_tri_broad_df.apply(robust_vol)
logrets_vol_price_sectoral_df = logrets_price_sectoral_df.apply(robust_vol)
logrets_vol_tri_sectoral_df = logrets_tri_sectoral_df.apply(robust_vol)

tab1, tab2 = st.tabs(["Broad Index Movements", "Sectoral Index Movements"])
with tab1:
        zscore_price_broad_df = logrets_price_broad_df/logrets_vol_price_broad_df
        zscore_tri_broad_df = logrets_tri_broad_df/logrets_vol_tri_broad_df
        fig_z_price_broad = plot_performance(zscore_price_broad_df, n_periods)
        fig_rets_price_broad = plot_performance(logrets_price_broad_df, n_periods, data_zscored=False)
        fig_vol_price_broad = plot_performance(logrets_vol_price_broad_df, n_periods, data_zscored=False)
        
        st.subheader("NIFTY Broad Price Indices Performance")
        st.plotly_chart(fig_z_price_broad, use_container_width=True)
        st.plotly_chart(fig_rets_price_broad, use_container_width=True)
        st.plotly_chart(fig_vol_price_broad, use_container_width=True)
with tab2:
        zscore_price_sectoral_df = logrets_price_sectoral_df/logrets_vol_price_sectoral_df
        zscore_tri_sectoral_df = logrets_tri_sectoral_df/logrets_vol_tri_sectoral_df
        fig_z_price_sect = plot_performance(zscore_price_sectoral_df, n_periods)
        fig_rets_price_sect = plot_performance(logrets_price_sectoral_df, n_periods,data_zscored=False)
        fig_vol_price_sect = plot_performance(logrets_vol_price_sectoral_df, n_periods,data_zscored=False)
        
        st.subheader("NIFTY Sectoral Price Indices Performance")
        st.plotly_chart(fig_z_price_sect, use_container_width=True)
        st.plotly_chart(fig_rets_price_sect, use_container_width=True)
        st.plotly_chart(fig_vol_price_sect, use_container_width=True)
