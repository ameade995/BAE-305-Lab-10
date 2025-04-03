import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Set page config
st.set_page_config(page_title="Water Quality Analyzer", layout="wide")

# App title
st.title("🌊 Advanced Water Quality Dashboard")

# File upload section
with st.sidebar:
    st.header("Data Upload")
    uploaded_files = st.file_uploader(
        "Upload both Results and Stations files",
        type=["csv"],
        accept_multiple_files=True
    )

# Initialize session state
if 'results_df' not in st.session_state:
    st.session_state.results_df = None
if 'stations_df' not in st.session_state:
    st.session_state.stations_df = None

# Process uploaded files
if uploaded_files and len(uploaded_files) == 2:
    for file in uploaded_files:
        df = pd.read_csv(file)
        if 'CharacteristicName' in df.columns:
            st.session_state.results_df = df
        elif 'MonitoringLocationIdentifier' in df.columns:
            st.session_state.stations_df = df

# Main analysis section
if st.session_state.results_df is not None and st.session_state.stations_df is not None:
    # Data processing
    results_df = st.session_state.results_df
    stations_df = st.session_state.stations_df
    
    # Convert dates and numeric values
    results_df['ActivityStartDate'] = pd.to_datetime(results_df['ActivityStartDate'])
    results_df['ResultMeasureValue'] = pd.to_numeric(results_df['ResultMeasureValue'], errors='coerce')
    
    # Get unique characteristics
    characteristics = results_df['CharacteristicName'].unique()
    
    # Sidebar controls
    with st.sidebar:
        st.header("Analysis Parameters")
        selected_characteristics = st.multiselect(
            "Select Characteristics",
            characteristics,
            default=characteristics[:2] if len(characteristics) > 1 else characteristics[:1]
        )
        
        # Date range selector
        min_date = results_df['ActivityStartDate'].min().date()
        max_date = results_df['ActivityStartDate'].max().date()
        date_range = st.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Value range slider (dynamic based on selected characteristics)
        if selected_characteristics:
            min_val = results_df[results_df['CharacteristicName'].isin(selected_characteristics)]['ResultMeasureValue'].min()
            max_val = results_df[results_df['CharacteristicName'].isin(selected_characteristics)]['ResultMeasureValue'].max()
            value_range = st.slider(
                "Select Value Range",
                min_value=float(min_val),
                max_value=float(max_val),
                value=(float(min_val), float(max_val))
            )

    # Filter data based on selections
    if len(date_range) == 2 and selected_characteristics:
        filtered_results = results_df[
            (results_df['CharacteristicName'].isin(selected_characteristics)) &
            (results_df['ResultMeasureValue'] >= value_range[0]) &
            (results_df['ResultMeasureValue'] <= value_range[1]) &
            (results_df['ActivityStartDate'].dt.date >= date_range[0]) &
            (results_df['ActivityStartDate'].dt.date <= date_range[1])
        ]
        
        # Merge with station data
        merged_data = pd.merge(
            filtered_results,
            stations_df,
            on='MonitoringLocationIdentifier',
            how='left'
        )
        
        # Create tabs for different views
        tab1, tab2 = st.tabs(["Time Series Analysis", "Spatial Analysis"])
        
        with tab1:
            # Interactive time series plot
            st.subheader("Contaminant Trends Over Time")
            if not filtered_results.empty:
                fig = px.line(
                    filtered_results,
                    x='ActivityStartDate',
                    y='ResultMeasureValue',
                    color='MonitoringLocationIdentifier',
                    line_group='CharacteristicName',
                    facet_col='CharacteristicName',
                    labels={
                        'ActivityStartDate': 'Date',
                        'ResultMeasureValue': 'Concentration',
                        'MonitoringLocationIdentifier': 'Station ID'
                    },
                    height=600
                )
                fig.update_layout(legend_title_text='Station ID')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No data available for the selected filters")
        
        with tab2:
            # Map visualization
            st.subheader("Station Locations with Selected Measurements")
            if not merged_data.empty and 'LatitudeMeasure' in merged_data.columns and 'LongitudeMeasure' in merged_data.columns:
                # Create a density map
                fig = px.density_mapbox(
                    merged_data,
                    lat='LatitudeMeasure',
                    lon='LongitudeMeasure',
                    z='ResultMeasureValue',
                    hover_name='MonitoringLocationName',
                    hover_data=['CharacteristicName', 'ResultMeasureValue'],
                    animation_frame=pd.to_datetime(merged_data['ActivityStartDate']).dt.strftime('%Y-%m'),
                    mapbox_style="stamen-terrain",
                    zoom=6,
                    height=600,
                    title=f"Measurement Distribution: {', '.join(selected_characteristics)}"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Show station statistics
                st.subheader("Station Measurements Summary")
                st.dataframe(
                    merged_data.groupby(['MonitoringLocationIdentifier', 'CharacteristicName'])['ResultMeasureValue']
                    .describe()
                    .unstack()
                    .round(2)
                )
            else:
                st.warning("No location data available for mapping")
    else:
        st.warning("Please select both date range and at least one characteristic")
else:
    st.info("Please upload both Results and Stations CSV files to begin analysis")

# Requirements needed (save as requirements.txt)
'''
streamlit==1.32.2
pandas==2.1.4
plotly==5.18.0
numpy==1.26.3
'''
