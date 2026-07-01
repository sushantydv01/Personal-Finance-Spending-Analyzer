import os
import base64
import tempfile
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State, no_update, callback_context
import dash_bootstrap_components as dbc

# Import our modular logic
from utils.data_loader import process_data
from components.charts import (
    create_spending_trend,
    create_category_breakdown,
    create_top_merchants,
    create_spending_heatmap,
    create_running_balance_chart
)

# Initialize the Dash app with a modern Dark theme (DARKLY)
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server
app.title = "Finance Analyzer"

# -------------------------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------------------------

def parse_contents(contents, filename):
    """
    Decodes the uploaded file, saves it to a temporary location, 
    and runs it through the processing pipeline.
    """
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # We use a temporary file to leverage our existing process_data pipeline
        # without mixing data loading/cleaning logic in the app layer.
        fd, temp_path = tempfile.mkstemp(suffix=".csv")
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(decoded)
                
            # Process data using the pipeline
            df = process_data(temp_path)
            return df
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return None


# -------------------------------------------------------------------------------------
# App Layout
# -------------------------------------------------------------------------------------

app.layout = dbc.Container([
    # Store for processed DataFrame (JSON format)
    dcc.Store(id='stored-data'),
    
    # Header Row
    dbc.Row([
        dbc.Col(html.H2("Personal Finance Analyzer", className="text-center my-4 font-weight-bold"), width=12)
    ]),
    
    # Upload and Filters Row
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Data Source & Filters", className="card-title"),
                    html.Hr(),
                    
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            'Drag and Drop or ', html.A('Select a CSV File', style={'fontWeight': 'bold', 'color': '#17a2b8'})
                        ]),
                        className="dash-upload",
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '2px',
                            'borderStyle': 'dashed',
                            'borderColor': '#666',
                            'borderRadius': '8px',
                            'textAlign': 'center',
                            'marginBottom': '15px'
                        },
                        multiple=False
                    ),
                    html.Div(id='upload-status', className="text-info mb-4 text-center"),
                    
                    # Filters
                    html.Label("Filter by Category:"),
                    dcc.Dropdown(
                        id='category-filter',
                        options=[],
                        multi=True,
                        placeholder="Select categories...",
                        className="mb-4 text-dark" # text-dark ensures dropdown text is visible on light dropdown background
                    ),
                    
                    html.Label("Filter by Date Range:"),
                    html.Br(),
                    dcc.DatePickerRange(
                        id='date-filter',
                        start_date_placeholder_text="Start Date",
                        end_date_placeholder_text="End Date",
                        display_format='YYYY-MM-DD',
                        className="w-100 mb-2"
                    )
                ])
            ], className="mb-4 shadow-sm h-100")
        ], md=4),
        
        # Summary/KPIs could go here, for now we will place the Running Balance or Trend
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Loading(
                        id="loading-trend",
                        type="circle",
                        children=dcc.Graph(id='spending-trend-chart', style={'height': '400px'})
                    )
                ])
            ], className="mb-4 shadow-sm h-100")
        ], md=8)
    ], className="mb-4"),
    
    # Charts Grid Row 1
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Loading(
                        type="circle",
                        children=dcc.Graph(id='category-breakdown-chart')
                    )
                ])
            ], className="mb-4 shadow-sm")
        ], md=5),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Loading(
                        type="circle",
                        children=dcc.Graph(id='top-merchants-chart')
                    )
                ])
            ], className="mb-4 shadow-sm")
        ], md=7)
    ]),
    
    # Charts Grid Row 2
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Loading(
                        type="circle",
                        children=dcc.Graph(id='heatmap-chart')
                    )
                ])
            ], className="mb-4 shadow-sm")
        ], md=6),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Loading(
                        type="circle",
                        children=dcc.Graph(id='running-balance-chart')
                    )
                ])
            ], className="mb-4 shadow-sm")
        ], md=6)
    ])
    
], fluid=True, className="p-4")


# -------------------------------------------------------------------------------------
# Callbacks
# -------------------------------------------------------------------------------------

@app.callback(
    [Output('stored-data', 'data'),
     Output('upload-status', 'children'),
     Output('category-filter', 'options'),
     Output('spending-trend-chart', 'figure'),
     Output('category-breakdown-chart', 'figure'),
     Output('top-merchants-chart', 'figure'),
     Output('heatmap-chart', 'figure'),
     Output('running-balance-chart', 'figure')],
    [Input('upload-data', 'contents'),
     Input('category-filter', 'value'),
     Input('date-filter', 'start_date'),
     Input('date-filter', 'end_date')],
    [State('upload-data', 'filename'),
     State('stored-data', 'data')]
)
def update_dashboard(contents, selected_categories, start_date, end_date, filename, stored_data):
    """
    SINGLE MAIN CALLBACK ARCHITECTURE
    Handles both file uploads and filter interactions to update the entire dashboard.
    This avoids callback spaghetti and circular dependencies by consolidating state evaluation.
    """
    ctx = callback_context
    if not ctx.triggered:
        # Default state before any interaction
        return no_update, "Please upload a transaction CSV.", [], {}, {}, {}, {}, {}
        
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    df = pd.DataFrame()
    upload_msg = "Please upload a transaction CSV."
    
    # 1. Handle New File Upload
    if trigger_id == 'upload-data' and contents is not None:
        df = parse_contents(contents, filename)
        if df is None:
            return no_update, f"❌ Error processing file: {filename}", no_update, {}, {}, {}, {}, {}
        upload_msg = f"✅ Successfully loaded: {filename}"
        
    # 2. Handle Existing Data (Filter triggered)
    elif stored_data is not None:
        df = pd.read_json(stored_data, orient='split')
        upload_msg = f"📊 Currently viewing: {filename}" if filename else "📊 Viewing current data"
        
    if df is None or df.empty:
        return no_update, upload_msg, [], {}, {}, {}, {}, {}
        
    # Ensure Date column is proper datetime for filtering
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
    # Generate Dropdown Options before applying the category filter
    # This allows users to always see all available categories even if some are filtered out
    categories = []
    if 'Category' in df.columns:
        unique_cats = df['Category'].dropna().unique().tolist()
        categories = [{'label': c, 'value': c} for c in sorted(unique_cats)]
        
    # 3. Apply Filters
    filtered_df = df.copy()
    
    if selected_categories:
        filtered_df = filtered_df[filtered_df['Category'].isin(selected_categories)]
        
    if start_date:
        filtered_df = filtered_df[filtered_df['Date'] >= pd.to_datetime(start_date)]
        
    if end_date:
        filtered_df = filtered_df[filtered_df['Date'] <= pd.to_datetime(end_date)]
        
    # 4. Generate Charts
    fig_trend = create_spending_trend(filtered_df)
    fig_cat = create_category_breakdown(filtered_df)
    fig_merch = create_top_merchants(filtered_df)
    fig_heat = create_spending_heatmap(filtered_df)
    fig_bal = create_running_balance_chart(filtered_df)
    
    # Serialize dataframe to JSON for storage if it was freshly uploaded
    new_store_data = no_update
    if trigger_id == 'upload-data':
        store_df = df.copy()
        if 'Date' in store_df.columns:
            # Convert datetime to string to avoid JSON serialization issues
            store_df['Date'] = store_df['Date'].dt.strftime('%Y-%m-%d')
        new_store_data = store_df.to_json(orient='split')
        
    return (
        new_store_data,
        upload_msg,
        categories,
        fig_trend,
        fig_cat,
        fig_merch,
        fig_heat,
        fig_bal
    )

if __name__ == '__main__':
    app.run_server(debug=True)
