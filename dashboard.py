import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard", layout="wide")
st.title("EDA Dashboard - AIAI Customer loyalty")

#Loading data
df = pd.read_csv("customer_data.csv")


# Define filter sidebar
st.sidebar.header("Filter Segmentation")

st.markdown("---")

# CLV Slider Filter
clv_min_default = df['Customer Lifetime Value'].min() 
clv_max_default = df['Customer Lifetime Value'].max()
selected_clv_range = (clv_min_default, clv_max_default) 

# Geographic Filter
selected_provinces = st.sidebar.multiselect(
    "2. Filter by Province/State",
    options=df['Province or State'].unique(),
    default=df['Province or State'].unique(),
)

# Demographic Filter
selected_education = st.sidebar.multiselect(
    "3. Filter by Education Level",
    options=df['Education'].unique(),
    default=df['Education'].unique(),
)


# Loyalty Status Filter
selected_loyalty = st.sidebar.multiselect(
    "4. Filter by Loyalty Status",
    options=df['LoyaltyStatus'].unique(),
    default=df['LoyaltyStatus'].unique(),
)

# Application of the Filter
df_filtered = df[
    #CLV Filter (Range Check)
    (df['Customer Lifetime Value'] >= selected_clv_range[0]) &
    (df['Customer Lifetime Value'] <= selected_clv_range[1]) &
    
    #Geographic Filter 
    (df['Province or State'].isin(selected_provinces)) &
    
    #Demographic Filter 
    (df['Education'].isin(selected_education)) &
    
 
    #Loyalty status 
    (df['LoyaltyStatus'].isin(selected_loyalty))
]

if df_filtered.empty:
    st.warning("No customers match the current filter selection. Please adjust your filters.")
    st.stop() #this message will return if filters don't match the data


# METRICS 
col1, col2, col3, col4 = st.columns(4)


with col1:
    total_customers = len(df_filtered)
    st.metric(label= "Total Customers", value=f"{total_customers:,}")

with col2: 
    avg_clv = df_filtered['Customer Lifetime Value'].mean()
    st.metric(label="Avg Customer Lifetime Value", value=f"{avg_clv:,.0f}")


with col3:
    avg_distance = df_filtered['Avg_Flight_Dist_KM'].mean()
    st.metric(label="Avg. Flight Distance", value=f"{avg_distance:,.0f} KM")

with col4:
    if 'PRR' in df_filtered.columns:
        avg_prr = df_filtered['PRR'].mean() * 100
        st.metric(label="Avg. PRR", value=f"{avg_prr:,.1f}%")
    else:
        st.metric(label="Avg. PRR", value="N/A")

st.markdown("---") # Separator 

# INTERACTIVE MAP 
col_map, col_chart = st.columns([2, 1])

with col_map:
    st.subheader('Interactive Map')

    # Aggregation 
    df_map = df_filtered.groupby(['Province or State', 'Latitude', 'Longitude']).agg(
        Avg_Distance_KM=('Avg_Flight_Dist_KM', 'mean'),
        Total_Flights_Volume=('Total_Flights', 'sum'),
        Customer_Count=('LoyaltyStatus', 'count'),
    ).reset_index() 

    # Plotting 
    fig_map = px.scatter_mapbox(
        df_map,
        lat='Latitude',
        lon='Longitude',

        color='Avg_Distance_KM',
        size='Total_Flights_Volume',

        hover_name='Province or State', 
        hover_data={
            'Customer_Count': True,
            'Avg_Distance_KM': ':.0f',
            'Total_Flights_Volume': ':.1f'
        }, 

        color_continuous_scale=px.colors.sequential.Viridis,

        center={"lat": 40.0, "lon": -100.0}, 
        zoom=2.5,

        mapbox_style="carto-positron", 
        height=450,
        title="Geographic Segmentation by Avg. Flight Distance and Volume"
    )
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_map, use_container_width=True)



with col_chart:
    st.subheader('Customer Distribution by Loyalty Status')
    
    #  to count the size of each LoyaltyStatus group
    df_loyalty = df_filtered.groupby('LoyaltyStatus').size().reset_index(name='Count')

    # Pie Chart for Loyalty status
    fig_pie = px.pie(
        df_loyalty,
        names='LoyaltyStatus',  # The categories to display in the legend/slices
        values='Count',         # The size of each slice
        title='Loyalty Status',
        color_discrete_sequence=px.colors.sequential.Agsunset, 
    )
    # Ensure the title and data labels are readable
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    
    st.plotly_chart(fig_pie, use_container_width=True)
