import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional

# Standard aesthetic configuration for the dashboards
CHART_TEMPLATE = "plotly_dark"
COLOR_SEQUENCE = px.colors.qualitative.Pastel

def _filter_expenses(df: pd.DataFrame) -> pd.DataFrame:
    """
    Helper function to isolate expense transactions.
    Assumes 'IsExpense' column exists from the data pipeline.
    If not, falls back to filtering negative amounts.
    """
    if 'IsExpense' in df.columns:
        return df[df['IsExpense'] == True]  # type: ignore
    elif 'Amount' in df.columns:
        return df[df['Amount'] < 0]  # type: ignore
    return df

def create_spending_trend(df: pd.DataFrame) -> go.Figure:
    """
    Creates a line chart showing the daily spending trend over time.
    
    Args:
        df: The pre-processed transaction DataFrame containing 'Date' and 'Amount'.
        
    Returns:
        go.Figure: A configured Plotly line chart.
    """
    expenses = _filter_expenses(df).copy()
    
    if 'Amount' in expenses.columns:
        expenses['Amount'] = expenses['Amount'].abs()
        
        # Aggregate spending by day
        daily_spending = expenses.groupby('Date')['Amount'].sum().reset_index()
        
        fig = px.line(
            daily_spending, 
            x='Date', 
            y='Amount',
            title='Daily Spending Trend',
            template=CHART_TEMPLATE,
            color_discrete_sequence=[COLOR_SEQUENCE[0]]
        )
    else:
        # Fallback empty figure if columns are missing
        fig = go.Figure()
        fig.update_layout(title="Daily Spending Trend (No Data)", template=CHART_TEMPLATE)

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Amount Spent",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

def create_category_breakdown(df: pd.DataFrame) -> go.Figure:
    """
    Creates a donut chart displaying spending broken down by category.
    
    Args:
        df: The pre-processed transaction DataFrame containing 'Category' and 'Amount'.
        
    Returns:
        go.Figure: A configured Plotly pie (donut) chart.
    """
    expenses = _filter_expenses(df).copy()
    
    if 'Amount' in expenses.columns and 'Category' in expenses.columns:
        expenses['Amount'] = expenses['Amount'].abs()
        
        # Aggregate spending by category
        category_spending = expenses.groupby('Category')['Amount'].sum().reset_index()
        # Filter out negligible amounts to keep the chart clean
        category_spending = category_spending[category_spending['Amount'] > 0]
        
        fig = px.pie(
            category_spending, 
            names='Category', 
            values='Amount',
            title='Spending Breakdown by Category',
            hole=0.4, # Creates the donut shape
            template=CHART_TEMPLATE,
            color_discrete_sequence=COLOR_SEQUENCE
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
    else:
        fig = go.Figure()
        fig.update_layout(title="Spending by Category (No Data)", template=CHART_TEMPLATE)

    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    return fig

def create_top_merchants(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """
    Creates a horizontal bar chart identifying the top merchants by total spending.
    
    Args:
        df: The transaction DataFrame containing merchant/description and 'Amount'.
        top_n: The number of top merchants to display (default 10).
        
    Returns:
        go.Figure: A configured Plotly horizontal bar chart.
    """
    expenses = _filter_expenses(df).copy()
    
    if 'Amount' in expenses.columns:
        expenses['Amount'] = expenses['Amount'].abs()
        
        # Determine which column to use for merchants
        merchant_col = 'Merchant' if 'Merchant' in expenses.columns else 'Description'
        
        if merchant_col in expenses.columns:
            merchant_spending = expenses.groupby(merchant_col)['Amount'].sum().reset_index()
            # Get the top N and sort ascending for the horizontal bar chart layout
            top_merchants = merchant_spending.nlargest(top_n, 'Amount').sort_values('Amount', ascending=True)
            
            fig = px.bar(
                top_merchants, 
                x='Amount', 
                y=merchant_col,
                orientation='h',
                title=f'Top {top_n} Merchants',
                template=CHART_TEMPLATE,
                color_discrete_sequence=[COLOR_SEQUENCE[1]]
            )
            fig.update_layout(
                xaxis_title="Total Spent",
                yaxis_title="Merchant"
            )
        else:
            fig = go.Figure()
            fig.update_layout(title="Top Merchants (No Data)", template=CHART_TEMPLATE)
    else:
        fig = go.Figure()
        fig.update_layout(title="Top Merchants (No Data)", template=CHART_TEMPLATE)

    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    return fig

def create_spending_heatmap(df: pd.DataFrame) -> go.Figure:
    """
    Creates a heatmap to visualize spending intensity by Day of Week and Month.
    
    Args:
        df: The transaction DataFrame containing 'Date' and 'Amount'.
            Derived columns 'Weekday' and 'Month' are used if available.
        
    Returns:
        go.Figure: A configured Plotly heatmap chart.
    """
    expenses = _filter_expenses(df).copy()
    
    if 'Amount' in expenses.columns and 'Date' in expenses.columns:
        expenses['Amount'] = expenses['Amount'].abs()
        
        # Ensure we have a datetime Date column to extract parts if missing
        if not pd.api.types.is_datetime64_any_dtype(expenses['Date']):
            expenses['Date'] = pd.to_datetime(expenses['Date'], errors='coerce')
            expenses = expenses.dropna(subset=['Date'])
            
        if 'Weekday' not in expenses.columns:
            expenses['Weekday'] = expenses['Date'].dt.day_name()  # type: ignore
        if 'Month' not in expenses.columns:
            expenses['Month'] = expenses['Date'].dt.month_name()  # type: ignore
            
        # Group by Month and Weekday
        heatmap_data = expenses.groupby(['Month', 'Weekday'])['Amount'].sum().reset_index()
        
        if not heatmap_data.empty:
            # Pivot the data to create a matrix for the heatmap
            heatmap_pivot = heatmap_data.pivot(index='Weekday', columns='Month', values='Amount').fillna(0)
            
            # Reorder weekdays logically
            weekdays_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            existing_weekdays = [day for day in weekdays_order if day in heatmap_pivot.index]
            heatmap_pivot = heatmap_pivot.reindex(existing_weekdays)
            
            # Sort columns (Months) chronologically rather than alphabetically if possible
            months_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                            'July', 'August', 'September', 'October', 'November', 'December']
            existing_months = [m for m in months_order if m in heatmap_pivot.columns]
            if existing_months:
                heatmap_pivot = heatmap_pivot[existing_months]
            
            fig = px.imshow(
                heatmap_pivot,
                labels=dict(x="Month", y="Day of Week", color="Amount Spent"),
                x=heatmap_pivot.columns,
                y=heatmap_pivot.index,
                title='Spending Heatmap (Day vs Month)',
                template=CHART_TEMPLATE,
                color_continuous_scale='Viridis',
                aspect='auto'
            )
        else:
            fig = go.Figure()
            fig.update_layout(title="Spending Heatmap (No Data)", template=CHART_TEMPLATE)
    else:
        fig = go.Figure()
        fig.update_layout(title="Spending Heatmap (No Data)", template=CHART_TEMPLATE)

    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    return fig

def create_running_balance_chart(df: pd.DataFrame) -> go.Figure:
    """
    Creates an area chart tracking the running balance (or cumulative spending) over time.
    
    Args:
        df: The transaction DataFrame containing 'Date' and optionally 'Balance'.
        
    Returns:
        go.Figure: A configured Plotly area chart.
    """
    if 'Date' not in df.columns:
        fig = go.Figure()
        fig.update_layout(title="Running Balance (No Date Column)", template=CHART_TEMPLATE)
        return fig
        
    # Ensure Date is properly formatted and sorted
    sorted_df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(sorted_df['Date']):
        sorted_df['Date'] = pd.to_datetime(sorted_df['Date'], errors='coerce')
        
    sorted_df = sorted_df.dropna(subset=['Date']).sort_values('Date')
    
    # Track the actual balance if available
    if 'Balance' in sorted_df.columns and sorted_df['Balance'].notna().any():
        balance_df = sorted_df.dropna(subset=['Balance'])
        # Take the last balance recorded for each day
        plot_df = balance_df.groupby('Date')['Balance'].last().reset_index()
        
        fig = px.area(
            plot_df, 
            x='Date', 
            y='Balance',
            title='Running Balance Trend',
            template=CHART_TEMPLATE,
            color_discrete_sequence=[COLOR_SEQUENCE[2]]
        )
        fig.update_layout(yaxis_title="Balance")
        
    # Fallback to cumulative sum of Amount if Balance is missing
    elif 'Amount' in sorted_df.columns:
        sorted_df['Cumulative_Amount'] = sorted_df['Amount'].cumsum()
        plot_df = sorted_df.groupby('Date')['Cumulative_Amount'].last().reset_index()
        
        fig = px.area(
            plot_df, 
            x='Date', 
            y='Cumulative_Amount',
            title='Cumulative Cash Flow',
            template=CHART_TEMPLATE,
            color_discrete_sequence=[COLOR_SEQUENCE[2]]
        )
        fig.update_layout(yaxis_title="Cumulative Amount")
        
    else:
        fig = go.Figure()
        fig.update_layout(title="Running Balance (No Balance/Amount)", template=CHART_TEMPLATE)

    fig.update_layout(
        xaxis_title="Date",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig
