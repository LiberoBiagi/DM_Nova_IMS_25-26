import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import pathlib

# TODO: Unscale axis before visualization -> DONE
# TODO: Drop down menu to select axis (x,y,z) -> DONE
# TODO: Add buttons for selecting different cluster types -> DONE

try:
    df = pd.read_csv("Data/clustered_df.csv")
except FileNotFoundError:
    # Fallback for development if run from different dir
    df = pd.read_csv("https://raw.githubusercontent.com/LiberoBiagi/DM_Nova_IMS_25-26/refs/heads/main/Data/clustered_df.csv")

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

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Airline Customer Clustering Dashboard", className="text-center my-4"), width=12)
    ]),
    
    dbc.Row([
        # Sidebar
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Filters"),
                dbc.CardBody([
                    html.Label("Gender"),
                    dcc.Dropdown(id='gender-filter', options=gender_options, multi=True, placeholder="Select Gender"),
                    html.Br(),
                    
                    html.Label("Education"),
                    dcc.Dropdown(id='education-filter', options=education_options, multi=True, placeholder="Select Education"),
                    html.Br(),
                    
                    html.Label("Marital Status"),
                    dcc.Dropdown(id='marital-filter', options=marital_options, multi=True, placeholder="Select Status"),
                    html.Br(),
                    
                    html.Label("Income Range"),
                    dcc.RangeSlider(
                        id='income-slider',
                        min=df['Income'].min(),
                        max=df['Income'].max(),
                        step=500,
                        marks={int(val): f'${int(val)}k' for val in [df['Income'].min(), df['Income'].mean(), df['Income'].max()]},
                        value=[df['Income'].min(), df['Income'].max()]
                    ),
                    html.Br(),
                    
                    html.Label("X Axis"),
                    dcc.Dropdown(id='x-axis-dropdown', options=axis_options, value='frequency', clearable=False),
                    html.Br(),

                    html.Label("Y Axis"),
                    dcc.Dropdown(id='y-axis-dropdown', options=axis_options, value='mean_spent', clearable=False),
                    html.Br(),

                    html.Label("Z Axis"),
                    dcc.Dropdown(id='z-axis-dropdown', options=axis_options, value='most_recent_flight', clearable=False),
                    html.Br(),

                    html.Label("Cluster Type"),
                    dcc.RadioItems(
                        id='cluster-type',
                        options=[
                            {'label': 'Behavioural', 'value': 'behavioural_cluster'},
                            {'label': 'Value', 'value': 'value_cluster'},
                            {'label': 'Behavioural Fuzzy 0', 'value': 'behavioural_fuzzy_membership_0'},
                            {'label': 'Behavioural Fuzzy 1', 'value': 'behavioural_fuzzy_membership_1'},
                            {'label': 'Value Fuzzy 0', 'value': 'value_fuzzy_membership_0'},
                            {'label': 'Value Fuzzy 1', 'value': 'value_fuzzy_membership_1'}
                        ],
                        value='behavioural_cluster',
                        inline=True
                    ),
                    html.Br(),
                    
                    html.Label("Axis Scaling"),
                    dbc.Switch(
                        id='scale-toggle',
                        label="Scale Axes",
                        value=False
                    ),
                    html.Br(),
                    
                    dbc.Button("Download Filtered Data", id="btn-download", color="primary", className="w-100"),
                    dcc.Download(id="download-dataframe-csv"),
                ])
            ], className="mb-4"),
            
            dbc.Card([
                dbc.CardHeader("Customer Details"),
                dbc.CardBody(id='customer-detail-panel', children=[
                    html.P("Click on a customer point to see details.", className="text-muted")
                ])
            ])
        ], width=3),
        
        # Main Graph Area
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(id='cluster-3d-plot', style={'height': '80vh'})
                ])
            ])
        ], width=9)
    ])
], fluid=True)

@app.callback(
    Output('cluster-3d-plot', 'figure'),
    Input('gender-filter', 'value'),
    Input('education-filter', 'value'),
    Input('marital-filter', 'value'),
    Input('income-slider', 'value'),
    Input('x-axis-dropdown', 'value'),
    Input('y-axis-dropdown', 'value'),
    Input('z-axis-dropdown', 'value'),
    Input('cluster-type', 'value'),
    Input('scale-toggle', 'value')
)
def update_graph(selected_genders, selected_educations, selected_marital, income_range, x_axis, y_axis, z_axis, cluster_col, use_scaled):
    dff = df.copy()
    
    if selected_genders:
        dff = dff[dff['Gender'].isin(selected_genders)]
    if selected_educations:
        dff = dff[dff['Education'].isin(selected_educations)]
    if selected_marital:
        dff = dff[dff['Marital Status'].isin(selected_marital)]
    
    dff = dff[(dff['Income'] >= income_range[0]) & (dff['Income'] <= income_range[1])]
    
    # Ensure cluster column is treated as categorical for discrete colors ONLY if not fuzzy
    if 'fuzzy' not in cluster_col:
        dff[cluster_col] = dff[cluster_col].astype(str)
    
    # Determine which columns to use for axes
    if use_scaled:
        x_col = x_axis
        y_col = y_axis
        z_col = z_axis
    else:
        x_col = x_axis + '_unscaled'
        y_col = y_axis + '_unscaled'
        z_col = z_axis + '_unscaled'

    fig = px.scatter_3d(
        dff,
        x=x_col,
        y=y_col,
        z=z_col,
        color=cluster_col,
        hover_data=['Loyalty#', 'City', 'Income'],
        custom_data=['Loyalty#', 'City', 'Income_unscaled', 'Gender', 'Education', 'Marital Status'],
        title=f"Customer Segments ({cluster_col.replace('_', ' ').title()})"
    )
    
    fig.update_layout(legend_title_text='Cluster')
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
    
    return details

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
    dff = df.copy()
    
    if selected_genders:
        dff = dff[dff['Gender'].isin(selected_genders)]
    if selected_educations:
        dff = dff[dff['Education'].isin(selected_educations)]
    if selected_marital:
        dff = dff[dff['Marital Status'].isin(selected_marital)]
    
    dff = dff[(dff['Income'] >= income_range[0]) & (dff['Income'] <= income_range[1])]
    
    return dcc.send_data_frame(dff.to_csv, "filtered_customer_data.csv")

if __name__ == '__main__':
    app.run(debug=True)
