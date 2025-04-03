import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Set page config
st.set_page_config(page_title="Water Quality Analyzer", layout="wide")

# App title
st.title("🌊 Water Quality Dashboard")

# File upload section
with st.sidebar:
    st.header("Upload Data")
    uploaded_files = st.file_uploader(
        "Upload both Results and Stations CSV files",
        type=["csv"],
        accept_multiple_files=True
    )

# Process uploaded files
results_df, stations_df = None, None
if uploaded_files and len(uploaded_files) == 2:
    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            if 'CharacteristicName' in df.columns:
                results_df = df
            elif 'MonitoringLocationIdentifier' in df.columns:
                stations_df = df
        except Exception as e:
            st.error(f"Error reading {file.name}: {str(e)}")

# Main analysis section
if results_df is not None and stations_df is not None:
    # Data processing
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
            default=characteristics[:1] if len(characteristics) > 0 else []
        )
        
        # Date range selector
        min_date = results_df['ActivityStartDate'].min().to_pydatetime().date()
        max_date = results_df['ActivityStartDate'].max().to_pydatetime().date()
        date_range = st.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Value range slider
        if selected_characteristics:
            char_data = results_df[results_df['CharacteristicName'].isin(selected_characteristics)]
            min_val = float(char_data['ResultMeasureValue'].min())
            max_val = float(char_data['ResultMeasureValue'].max())
            value_range = st.slider(
                "Select Value Range",
                min_value=min_val,
                max_value=max_val,
                value=(min_val, max_val)
            )

    # Filter data based on selections
    if selected_characteristics and len(date_range) == 2:
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
        ).dropna(subset=['LatitudeMeasure', 'LongitudeMeasure'])
        
        # Create tabs
        tab1, tab2 = st.tabs(["📈 Time Series", "🗺️ Station Map"])

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
                    height=500
                )
                fig.update_layout(
                    legend_title_text='Station ID',
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No data available for the selected filters")

        with tab2:
            # Map visualization - THIS IS THE FIXED VERSION
            st.subheader("Station Locations with Measurements")
            if not merged_data.empty:
                # Create a new column combining station name and measurement
                merged_data['Station_Label'] = (
                    merged_data['MonitoringLocationName'] + ": " + 
                    merged_data['ResultMeasureValue'].round(2).astype(str) + " " +
                    merged_data['ResultMeasure/MeasureUnitCode'].fillna('')
                )
                
                # Display the map with markers
                st.map(
                    merged_data.rename(columns={
                        'LatitudeMeasure': 'lat',
                        'LongitudeMeasure': 'lon'
                    }),
                    zoom=7,
                    size=20,  # Marker size
                    color='#FF0000'  # Red color for markers
                )
                
                # Show data table
                st.subheader("Measurement Data")
                st.dataframe(
                    merged_data[[
                        'MonitoringLocationName',
                        'CharacteristicName', 
                        'ResultMeasureValue',
                        'ActivityStartDate'
                    ]].sort_values('ActivityStartDate', ascending=False),
                    height=300
                )
            else:
                st.warning("No station location data available for mapping")
    else:
        st.warning("Please select both date range and at least one characteristic")
else:
    st.info("Please upload both Results and Stations CSV files to begin analysis")
