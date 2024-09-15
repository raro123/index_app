import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List
from utils.data_processing import robust_vol



def plot_index_returns_histograms(df, index_type, category):
    # Filter the dataframe based on index_type and category
    filtered_df = df[(df['index_type'] == index_type) & (df['index_category'] == category)]
    
    if filtered_df.empty:
        return go.Figure().add_annotation(text="No data found", showarrow=False, font=dict(size=20))
    
    # Sort the dataframe by date
    filtered_df = filtered_df.sort_values('date')
    
    # Calculate daily returns
    filtered_df['daily_return'] = filtered_df.groupby('symbol')['close'].pct_change()
    
    # Remove rows with NaN values (first row for each symbol)
    filtered_df = filtered_df.dropna(subset=['daily_return'])
    
    # Get unique symbols
    symbols = filtered_df['symbol'].unique()
    
    if len(symbols) == 0:
        return go.Figure().add_annotation(text="No valid data found", showarrow=False, font=dict(size=20))
    
    # Calculate number of rows and columns for subplots
    n_symbols = len(symbols)
    n_cols = min(3, n_symbols)
    n_rows = (n_symbols + n_cols - 1) // n_cols
    
    # Create subplots
    fig = make_subplots(rows=n_rows, cols=n_cols,
                        subplot_titles=symbols,
                        vertical_spacing=0.1,
                        horizontal_spacing=0.05)
    
    # Plot histograms for each symbol
    for i, symbol in enumerate(symbols):
        symbol_data = filtered_df[filtered_df['symbol'] == symbol]
        
        row = i // n_cols + 1
        col = i % n_cols + 1
        
        # Add histogram
        fig.add_trace(
            go.Histogram(x=symbol_data['daily_return'], 
                         name=symbol,
                         nbinsx=50,
                         opacity=0.7),
            row=row, col=col
        )
        
        # Update axes
        fig.update_xaxes(title_text="Daily Return", 
                         row=row, col=col, 
                         tickformat='.1%',
                         hoverformat='.2%')
        fig.update_yaxes(title_text="Frequency", row=row, col=col)
    
    # Update layout
    fig.update_layout(
        title_text=f'Daily Returns Histograms for {index_type} Indices ({category})',
        showlegend=False,
        height=400*n_rows,
        width=1200,
    )
    
    return fig

def plot_index_returns_boxplots(df, index_type, category):
    # Filter the dataframe based on index_type and category
    filtered_df = df[(df['index_type'] == index_type) & (df['index_category'] == category)]
    
    if filtered_df.empty:
        return go.Figure().add_annotation(text="No data found", showarrow=False, font=dict(size=20))
    
    # Sort the dataframe by date
    filtered_df = filtered_df.sort_values('date')
    
    # Calculate daily returns
    filtered_df['daily_return'] = filtered_df.groupby('symbol')['close'].pct_change()
    
    # Remove rows with NaN values (first row for each symbol)
    filtered_df = filtered_df.dropna(subset=['daily_return'])
    
    if filtered_df.empty:
        return go.Figure().add_annotation(text="No valid data found", showarrow=False, font=dict(size=20))
    
    # Create boxplot
    fig = go.Figure()
    
    fig.add_trace(go.Box(
        x=filtered_df['symbol'],
        y=filtered_df['daily_return'],
        boxpoints='outliers',
        jitter=0.3,
        whiskerwidth=0.2,
        marker_size=2,
        line_width=1
    ))
    
    # Update layout
    fig.update_layout(
        title_text=f'Daily Returns Boxplots for {index_type} Indices ({category})',
        yaxis_title='Daily Return',
        xaxis_title='Symbols',
        height=600,
        width=max(1000, len(filtered_df['symbol'].unique()) * 50),  # Adjust width based on number of symbols
        yaxis=dict(
            tickformat='.1%',
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='red'
        ),
        boxmode='group',
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Rockwell"
        )
    )
    
    return fig


def plot_performance(zscore_change_df: pd.DataFrame, n_periods: int, data_zscored = True) -> go.Figure:
    """
    Plots the performance of NIFTY indices based on the z-score changes.

    Parameters:
    - zscore_change_df: pd.DataFrame containing z-score changes.

    Returns:
    - go.Figure: Plotly figure object.
    """
    # Create subplots
    df = zscore_change_df.iloc[-n_periods:].sort_index(ascending=False).T
    df.columns = df.columns.strftime('%Y-%m-%d')
    fig = make_subplots(rows=1, cols=len(df.columns), subplot_titles=df.columns, shared_yaxes=True, shared_xaxes=True)

    # Add traces for each column
    for i, column in enumerate(df.columns, 1):
        column_data = df[column].sort_values()

        fig.add_trace(
            go.Bar(
                y=column_data.index,
                x=column_data.values,
                name=column,
                text=column_data.values.round(4),
                textposition='outside',
                orientation='h'
            ),
            row=1, col=i
        )

        # Add vertical lines
        if data_zscored:
            for x in [-2, -1, 1, 2]:
                fig.add_vline(x=x, line_width=1, line_dash="dash", line_color="gray", row=1, col=i)

    # Update layout
    fig.update_layout(
        height=750,
        width=600 * len(df.columns),  # Adjust width based on number of columns
        title_text="NIFTY Indices Performance",
        showlegend=False,
        barmode='group'
    )

    # Update x-axes
    fig.update_xaxes(title_text="Performance", tickformat='.2f')

    # Update y-axes
    fig.update_yaxes(autorange="reversed")  # To maintain consistent order across subplots

    return fig


def plot_index_deepdive(index_data: pd.DataFrame, selected_symbols: List[str]) -> go.Figure:
    """
    Create a deep dive analysis plot for selected indices.

    This function generates a plotly figure with three subplots:
    1. Cumulative NAV (rebased to 100) for all selected indices
    2. Underwater drawdown plot for all selected indices
    3. Volatility time series for all selected indices

    Parameters:
    -----------
    index_data : pd.DataFrame
        A DataFrame containing the index data with:
        - DatetimeIndex representing the dates
        - Columns representing different index symbols
        - Values representing the closing prices of the indices
    selected_symbols : List[str]
        A list of symbol names to plot

    Returns:
    --------
    go.Figure
        A plotly Figure object containing the three subplots with all selected indices.

    Notes:
    ------
    The function assumes that the input DataFrame has been properly
    preprocessed and is sorted by date.
    """
    fig = make_subplots(rows=3, cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=0.1,
                        subplot_titles=("Cumulative NAV (Rebased to 100)", "Drawdown", "Volatility"))

    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    index_data = index_data[selected_symbols].dropna()
    for i, symbol in enumerate(selected_symbols):
        if symbol not in index_data.columns:
            continue

        color = colors[i % len(colors)]
        symbol_data = index_data[symbol].dropna()
        
        # Calculate returns and cumulative NAV
        returns = symbol_data.pct_change()
        cumulative_nav = (1 + returns).cumprod() * 100  # Rebased to 100

        # Cumulative NAV time series
        fig.add_trace(go.Scatter(x=cumulative_nav.index, y=cumulative_nav, 
                                 mode='lines', name=symbol,
                                 line=dict(color=color, width=2)),
                      row=1, col=1)

        # Underwater drawdown plot
        drawdown = (cumulative_nav / cumulative_nav.cummax()) - 1
        fig.add_trace(go.Scatter(x=drawdown.index, y=drawdown, 
                                 mode='lines', name=symbol,
                                 line=dict(color=color, width=2),
                                 showlegend=False),
                      row=2, col=1)

        # Volatility time series
        volatility = robust_vol(returns, annualise_stdev=True)
        fig.add_trace(go.Scatter(x=volatility.index, y=volatility, 
                                 mode='lines', name=symbol,
                                 line=dict(color=color, width=2),
                                 showlegend=False),
                      row=3, col=1)

    # Update layout
    fig.update_layout(
        height=1200, 
        width=1000, 
        title=dict(
            text="Deepdive Analysis for Selected Indices",
            font=dict(size=24, color="#333"),
            x=0.5,
            y=0.95
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=12),
            bgcolor="rgba(255,255,255,0.5)",
            bordercolor="#333",
            borderwidth=1
        ),
        plot_bgcolor='rgba(240,240,240,0.5)',
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12, color="#333")
    )

    # Update axes
    fig.update_xaxes(
        showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.5)',
        zeroline=False, linewidth=1, linecolor='#333'
    )
    fig.update_yaxes(
        showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.5)',
        zeroline=False, linewidth=1, linecolor='#333'
    )

    # Update y-axis titles
    fig.update_yaxes(title_text="NAV (Rebased to 100)",type='log' ,row=1, col=1)
    fig.update_yaxes(title_text="Drawdown", row=2, col=1)
    fig.update_yaxes(title_text="Volatility", row=3, col=1)


    return fig

def plot_correlation_heatmap(index_data: pd.DataFrame, selected_symbols: List[str]) -> go.Figure:
    """
    Create a correlation heatmap for the returns of selected indices.

    Parameters:
    -----------
    index_data : pd.DataFrame
        A DataFrame containing the index data with:
        - DatetimeIndex representing the dates
        - Columns representing different index symbols
        - Values representing the closing prices of the indices
    selected_symbols : List[str]
        A list of symbol names to include in the correlation heatmap

    Returns:
    --------
    go.Figure
        A plotly Figure object containing the correlation heatmap.

    Notes:
    ------
    The function assumes that the input DataFrame has been properly
    preprocessed and is sorted by date.
    """
    # Calculate returns
    returns_data = index_data[selected_symbols].pct_change().dropna()

    # Calculate correlation matrix
    corr_matrix = returns_data.corr()

    # Create mask for upper triangle
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))

    # Create heatmap
    heatmap = go.Heatmap(
        z=corr_matrix.mask(mask),
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        zmin=-1, zmax=1,
        colorscale='RdBu',
        reversescale=True,
        colorbar=dict(title='Correlation', titleside='right'),
        hovertemplate='%{x}<br>%{y}<br>Correlation: %{z:.2f}<extra></extra>'
    )

    # Create annotations
    annotations = []
    for i, row in enumerate(corr_matrix.values):
        for j, value in enumerate(row):
            if i <= j:  # Only annotate lower triangle
                continue
            annotations.append(
                dict(
                    x=corr_matrix.columns[j],
                    y=corr_matrix.index[i],
                    text=f'{value:.2f}',
                    showarrow=False,
                    font=dict(color='white' if abs(value) > 0.5 else 'black')
                )
            )

    # Create layout
    layout = go.Layout(
        title=dict(
            text='Correlation Heatmap of Selected Indices',
            font=dict(size=24, color="#333"),
            x=0.5,
            y=0.95
        ),
        width=800,
        height=700,
        xaxis=dict(title='', ticks='', side='top'),
        yaxis=dict(title='', ticks='', ticksuffix=' ', autorange='reversed'),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12, color="#333")
    )

    # Create figure
    fig = go.Figure(data=[heatmap], layout=layout)

    # Add annotations to figure
    fig.update_layout(annotations=annotations)

    return fig