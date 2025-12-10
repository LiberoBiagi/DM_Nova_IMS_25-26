import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import pathlib

#TODO: Add back toggle for scaled and unscaled

try:
    df = pd.read_csv("Data/clustered_df.csv")
except FileNotFoundError:
    # Fallback for development if run from different dir
    df = pd.read_csv("https://raw.githubusercontent.com/LiberoBiagi/DM_Nova_IMS_25-26/refs/heads/main/Data/clustered_df.csv")

# Ensure numeric columns are actually numeric
numeric_cols = ['Income', 'Customer Lifetime Value', 'mean_spent', 
                'Income_unscaled', 'Customer Lifetime Value_unscaled', 'mean_spent_unscaled']
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Amazing Airlines Brand Colors
AA_PRIMARY = "#4ca1d6"
AA_NAVY = "#001d43"
AA_GREY = "#cacccc"
AA_DARK = "#444444"
AA_COLOR_SEQUENCE = [AA_NAVY, AA_PRIMARY, AA_GREY, AA_DARK, "#888888"]  # Extended for more clusters

# Initialize app with a bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE])

# Define options for dropdowns
gender_options = [{'label': i, 'value': i} for i in df['Gender'].unique()]
education_options = [{'label': i, 'value': i} for i in df['Education'].unique()]
marital_options = [{'label': i, 'value': i} for i in df['Marital Status'].unique()]

axis_columns = [
    'Income', 'Customer Lifetime Value', 'Subscription_Duration_Days',
    'Flights_in_Subscription', 'Total_Flights', 'percentage_flights_as_sub',
    'mean_spent', 'distance_airport', 'Total_Distance_KM',
    'Total_Num_Flights_With_Companions', 'Total_Points_Redeemed', 'PRR',
    'Avg_Flight_Dist_KM', 'Comp_Ratio', 'most_recent_flight', 'frequency'
]
axis_options = [{'label': i, 'value': i} for i in axis_columns]

def filter_data(df, selected_genders, selected_educations, selected_marital, income_range):
    dff = df.copy()
    if selected_genders:
        dff = dff[dff['Gender'].isin(selected_genders)]
    if selected_educations:
        dff = dff[dff['Education'].isin(selected_educations)]
    if selected_marital:
        dff = dff[dff['Marital Status'].isin(selected_marital)]
    
    dff = dff[(dff['Income_unscaled'] >= income_range[0]) & (dff['Income_unscaled'] <= income_range[1])]
    return dff

app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col(html.H1("Amazing Airlines Customer Intelligence", className="text-center"), width=12)
    ], className="aa-header"),

    # Feature 1: KPI Scorecards (Re-styled)
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("Total Customers", className="aa-kpi-title"),
                html.H3(id="kpi-total-customers", children="0", className="aa-kpi-value")
            ])
        ], className="aa-kpi-card shadow-sm"), width=3),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("Avg Income", className="aa-kpi-title"),
                html.H3(id="kpi-avg-income", children="$0", className="aa-kpi-value")
            ])
        ], className="aa-kpi-card shadow-sm"), width=3),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("Avg Lifetime Value", className="aa-kpi-title"),
                html.H3(id="kpi-avg-clv", children="0", className="aa-kpi-value")
            ])
        ], className="aa-kpi-card shadow-sm"), width=3),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("Avg Spend", className="aa-kpi-title"),
                html.H3(id="kpi-avg-spend", children="$0", className="aa-kpi-value")
            ])
        ], className="aa-kpi-card shadow-sm"), width=3),
    ], className="mb-5"),
    
    # Main Analytical Content
    dbc.Row([
        # Main Visuals (3D + Radar)
        dbc.Col([
            dbc.Row([
                # 3D Plot (Hero Helper)
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("1. Global Cluster View", className="aa-card-header"),
                        dbc.CardBody([
                            html.P("Rotate and zoom to explore customer separation.", className="text-muted small mb-2"),
                            dcc.Graph(id='cluster-3d-plot', style={'height': '60vh'})
                        ])
                    ], className="aa-card")
                ], width=8),
                
                # Radar Chart (Moved here for "Features")
                dbc.Col([
                     dbc.Card([
                        dbc.CardHeader("2. Cluster DNA (Features)", className="aa-card-header"),
                        dbc.CardBody([
                             html.P("Compare the average profile of the selected clusters.", className="text-muted small mb-2"),
                             dcc.Graph(id='radar-plot', style={'height': '60vh'})
                        ])
                    ], className="aa-card")
                ], width=4),
            ]),
            
            # Deep Dive Row
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                         dbc.CardHeader("3. Attribute Deep Dive (Distributions)", className="aa-card-header"),
                         dbc.CardBody([
                            html.Label("Select Metric to Compare:", className="fw-bold"),
                            dcc.Dropdown(
                                id='distribution-metric-dropdown',
                                options=axis_options,
                                value='Income',
                                clearable=False,
                                className="mb-3"
                            ),
                            dcc.Graph(id='distribution-plot', style={'height': '350px'})
                        ])
                    ], className="aa-card")
                ], width=12)
            ], className="mt-4")
            
        ], width=9),

       # Control Panel (Left Side, Reduced Visual Weight)
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Exploration Controls", className="aa-card-header"),
                dbc.CardBody([
                    html.H5("Filters", className="mb-3"),
                    html.Label("Gender"),
                    dcc.Dropdown(id='gender-filter', options=gender_options, multi=True, placeholder="All Genders"),
                    html.Br(),
                    
                    html.Label("Education"),
                    dcc.Dropdown(id='education-filter', options=education_options, multi=True, placeholder="All Education"),
                    html.Br(),
                    
                    html.Label("Marital Status"),
                    dcc.Dropdown(id='marital-filter', options=marital_options, multi=True, placeholder="All Status"),
                    html.Br(),
                    
                    html.Label("Income Range"),
                    dcc.RangeSlider(
                        id='income-slider',
                        min=df['Income_unscaled'].min(),
                        max=df['Income_unscaled'].max(),
                        step=500,
                        marks={int(val): f'${int(val/1000)}k' for val in [df['Income_unscaled'].min(), df['Income_unscaled'].mean(), df['Income_unscaled'].max()]},
                        value=[df['Income_unscaled'].min(), df['Income_unscaled'].max()]
                    ),
                    html.Hr(),
                    
                    html.H5("Graph Settings", className="mb-3"),
                    html.Label("Cluster Coloring"),
                    dcc.RadioItems(
                        id='cluster-type',
                        options=[
                            {'label': 'Behavioural', 'value': 'behavioural_cluster'},
                            {'label': 'Value', 'value': 'value_cluster'},
                            {'label': 'Behav. Fuzzy 0', 'value': 'behavioural_fuzzy_membership_0'},
                            {'label': 'Behav. Fuzzy 1', 'value': 'behavioural_fuzzy_membership_1'},
                            {'label': 'Value Fuzzy 0', 'value': 'value_fuzzy_membership_0'},
                            {'label': 'Value Fuzzy 1', 'value': 'value_fuzzy_membership_1'}
                        ],
                        value='behavioural_cluster',
                        labelStyle={'display': 'block', 'marginBottom': '5px'}
                    ),
                    html.Br(),
                    
                    html.Label("X Axis"),
                    dcc.Dropdown(id='x-axis-dropdown', options=axis_options, value='frequency', clearable=False),
                    html.Label("Y Axis", className="mt-2"),
                    dcc.Dropdown(id='y-axis-dropdown', options=axis_options, value='mean_spent', clearable=False),
                    html.Label("Z Axis", className="mt-2"),
                    dcc.Dropdown(id='z-axis-dropdown', options=axis_options, value='most_recent_flight', clearable=False),
                    
                    html.Hr(),
                    dbc.Button("Download Data", id="btn-download", color="secondary", outline=True, className="w-100"),
                    dcc.Download(id="download-dataframe-csv"),
                ])
            ], className="aa-card"),
            
            dbc.Card([
                dbc.CardHeader("Customer Details Inspector", className="aa-card-header"),
                dbc.CardBody(id='customer-detail-panel', children=[
                    html.P("Click on a global view point to inspect.", className="text-muted text-center")
                ])
            ], className="aa-card")
            
        ], width=3),
        
    ])
], fluid=True, className="bg-light")

@app.callback(
    Output('cluster-3d-plot', 'figure'),
    Input('gender-filter', 'value'),
    Input('education-filter', 'value'),
    Input('marital-filter', 'value'),
    Input('income-slider', 'value'),
    Input('x-axis-dropdown', 'value'),
    Input('y-axis-dropdown', 'value'),
    Input('z-axis-dropdown', 'value'),
    Input('cluster-type', 'value')
)
def update_graph(selected_genders, selected_educations, selected_marital, income_range, x_axis, y_axis, z_axis, cluster_col):
    dff = filter_data(df, selected_genders, selected_educations, selected_marital, income_range)
    
    if dff.empty:
        # Return an empty figure with a message to avoid crash
        fig = px.scatter_3d(template='plotly_white', title="No Data Found - Adjust Filters")
        return fig
    
    # Ensure cluster column is treated as categorical for discrete colors ONLY if not fuzzy
    if 'fuzzy' not in cluster_col:
        dff[cluster_col] = dff[cluster_col].astype(str)
    
    # Determine which columns to use for axes (Default to UNSCALED for better interpretation)
    # Check if unscaled exists, otherwise fallback to scaled
    x_col = x_axis + '_unscaled' if x_axis + '_unscaled' in dff.columns else x_axis
    y_col = y_axis + '_unscaled' if y_axis + '_unscaled' in dff.columns else y_axis
    z_col = z_axis + '_unscaled' if z_axis + '_unscaled' in dff.columns else z_axis

    fig = px.scatter_3d(
        dff,
        x=x_col,
        y=y_col,
        z=z_col,
        color=cluster_col,
        hover_data=['Loyalty#', 'City', 'Income'],
        custom_data=['Loyalty#', 'City', 'Income_unscaled', 'Gender', 'Education', 'Marital Status'],
        title=f"Customer Segments ({cluster_col.replace('_', ' ').title()})",
        color_discrete_sequence=AA_COLOR_SEQUENCE
    )
    
    fig.update_layout(
        legend_title_text='Cluster',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=AA_NAVY),
        margin=dict(l=0, r=0, t=30, b=0)
    )
    return fig

@app.callback(
    Output('customer-detail-panel', 'children'),
    Input('cluster-3d-plot', 'clickData')
)
def display_click_data(clickData):
    if clickData is None:
        return html.P("Click on a customer point to see details.", className="text-muted")
    
    # Extract data from the clicked point
    point_data = clickData['points'][0]
    custom_data = point_data.get('customdata', [])
    
    if not custom_data:
        return html.P("No details available for this point.")
        
    # Handle potential extra data (e.g. from hover_data)
    loyalty_num, city, income, gender, education, marital = custom_data[:6]
    
    details = [
        html.H5(f"Customer #{loyalty_num}", className="card-title"),
        html.Hr(),
        html.P([html.Strong("City: "), f"{city}"]),
        html.P([html.Strong("Income: "), f"${income:,.2f}"]),
        html.P([html.Strong("Gender: "), f"{gender}"]),
        html.P([html.Strong("Education: "), f"{education}"]),
        html.P([html.Strong("Marital Status: "), f"{marital}"]),
    ]
    
    # Feature 4: Fuzzy Membership Inspector
    # Find columns starting with 'behavioural_fuzzy_membership_'
    fuzzy_cols = [c for c in df.columns if 'fuzzy_membership' in c]
    if fuzzy_cols:
        # Get the full row for this customer
        customer_row = df[df['Loyalty#'] == loyalty_num]
        if not customer_row.empty:
            fuzzy_data = customer_row[fuzzy_cols].iloc[0]


            # Create short labels for better display in the bar chart
            short_labels = [c.replace('behavioural_fuzzy_membership_', 'Behav ').replace('value_fuzzy_membership_', 'Value ') for c in fuzzy_cols]
            
            # Create the bar chart for fuzzy membership
            fig = px.bar(
                x=short_labels,
                y=fuzzy_data.values,
                labels={'x': 'Cluster', 'y': 'Probability'},
                title="Cluster Membership Probability",
                color_discrete_sequence=[AA_PRIMARY]
            )
            fig.update_layout(
                margin=dict(l=0, r=0, t=30, b=0), 
                height=200,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color=AA_DARK)
            )
            details.append(dcc.Graph(figure=fig))
            
    return details

@app.callback(
    Output("kpi-total-customers", "children"),
    Output("kpi-avg-income", "children"),
    Output("kpi-avg-clv", "children"),
    Output("kpi-avg-spend", "children"),
    Input('gender-filter', 'value'),
    Input('education-filter', 'value'),
    Input('marital-filter', 'value'),
    Input('income-slider', 'value')
)
def update_kpis(selected_genders, selected_educations, selected_marital, income_range):
    dff = filter_data(df, selected_genders, selected_educations, selected_marital, income_range)
    
    total_customers = len(dff)
    
    # Safely calculate means (handle NaNs or empty df)
    avg_income = dff['Income_unscaled'].mean()
    if pd.isna(avg_income): avg_income = 0
        
    avg_clv = dff['Customer Lifetime Value_unscaled'].mean()
    if pd.isna(avg_clv): avg_clv = 0
        
    avg_spend = dff['mean_spent_unscaled'].mean()
    if pd.isna(avg_spend): avg_spend = 0
    
    return (
        f"{total_customers:,}",
        f"${avg_income:,.0f}",
        f"{avg_clv:,.0f}",
        f"${avg_spend:,.0f}"
    )

@app.callback(
    Output('radar-plot', 'figure'),
    Input('gender-filter', 'value'),
    Input('education-filter', 'value'),
    Input('marital-filter', 'value'),
    Input('income-slider', 'value'),
    Input('cluster-type', 'value')
)
def update_radar(selected_genders, selected_educations, selected_marital, income_range, cluster_col):
    dff = filter_data(df, selected_genders, selected_educations, selected_marital, income_range)
    
    if dff.empty or 'fuzzy' in cluster_col:
        return {}

    # Select numerical columns for DNA
    cols_to_plot = ['Income', 'Customer Lifetime Value', 'mean_spent', 'frequency', 'Total_Distance_KM']
    # Normalize data 0-1 for fair comparison
    dff_norm = dff.copy()
    for col in cols_to_plot:
        dff_norm[col] = (dff_norm[col] - df[col].min()) / (df[col].max() - df[col].min())
        
    # Group by cluster
    dff_grouped = dff_norm.groupby(cluster_col)[cols_to_plot].mean().reset_index()
    dff_grouped = pd.melt(dff_grouped, id_vars=[cluster_col], var_name='Metric', value_name='Score')
    
    fig = px.line_polar(dff_grouped, r='Score', theta='Metric', line_close=True, color=cluster_col, color_discrete_sequence=AA_COLOR_SEQUENCE)
    fig.update_layout(
        margin=dict(l=30, r=30, t=30, b=30),
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=AA_NAVY)
    )
    return fig

@app.callback(
    Output('distribution-plot', 'figure'),
    Input('gender-filter', 'value'),
    Input('education-filter', 'value'),
    Input('marital-filter', 'value'),
    Input('income-slider', 'value'),
    Input('cluster-type', 'value'),
    Input('distribution-metric-dropdown', 'value')
)
def update_distribution(selected_genders, selected_educations, selected_marital, income_range, cluster_col, metric):
    dff = filter_data(df, selected_genders, selected_educations, selected_marital, income_range)
    
    # Use unscaled metric if available
    plot_metric = metric
    if f"{metric}_unscaled" in dff.columns:
        plot_metric = f"{metric}_unscaled"
    
    if 'fuzzy' in cluster_col:
         fig = px.histogram(dff, x=plot_metric, color=None, title=f"Distribution of {metric}", color_discrete_sequence=[AA_PRIMARY])
    else:
        dff[cluster_col] = dff[cluster_col].astype(str)
        fig = px.box(dff, x=cluster_col, y=plot_metric, color=cluster_col, title=f"Distribution of {metric} by {cluster_col}", color_discrete_sequence=AA_COLOR_SEQUENCE)
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='white',
        font=dict(color=AA_DARK),
        margin=dict(l=40, r=20, t=40, b=40)
    )
    return fig

@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn-download", "n_clicks"),
    State('gender-filter', 'value'),
    State('education-filter', 'value'),
    State('marital-filter', 'value'),
    State('income-slider', 'value'),
    prevent_initial_call=True
)
def download_data(n_clicks, selected_genders, selected_educations, selected_marital, income_range):
    dff = filter_data(df, selected_genders, selected_educations, selected_marital, income_range)
    return dcc.send_data_frame(dff.to_csv, "filtered_customer_data.csv")

if __name__ == '__main__':
    app.run(debug=True)
