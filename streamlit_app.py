import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import folium_static
from datetime import datetime

# Set page config
st.set_page_config(page_title="Water Quality Analyzer", layout="wide")

# App title
st.title("🌊 Water Quality Contaminant Analyzer")

# Sidebar for file upload and filters
with st.sidebar:
    st.header("Upload Data")
    part1_file = st.file_uploader("Upload Part 1 Database (CSV)", type=["csv"])
    part2_file = st.file_uploader("Upload Part 2 Database (CSV)", type=["csv"])
    
    st.header("Filters")
    contaminant = st.text_input("Search for a contaminant:")
    
    if part2_file is not None:
        try:
            df2 = pd.read_csv(part2_file)
            # Convert date column to datetime
            df2['ActivityStartDate'] = pd.to_datetime(df2['ActivityStartDate'])
            # Convert measurement values to numeric
            df2['ResultMeasureValue'] = pd.to_numeric(df2['ResultMeasureValue'], errors='coerce')
            
            # Get unique contaminants from the data
            all_contaminants = df2['CharacteristicName'].unique()
            if contaminant:
                matching_contaminants = [c for c in all_contaminants if contaminant.lower() in str(c).lower()]
                selected_contaminant = st.selectbox("Select contaminant:", matching_contaminants)
            else:
                selected_contaminant = st.selectbox("Select contaminant:", all_contaminants)
            
            # Get min/max values for the selected contaminant
            contam_data = df2[df2['CharacteristicName'] == selected_contaminant]
            min_val, max_val = contam_data['ResultMeasureValue'].min(), contam_data['ResultMeasureValue'].max()
            
            # Value range slider
            value_range = st.slider(
                "Select value range:",
                min_value=float(min_val),
                max_value=float(max_val),
                value=(float(min_val), float(max_val))
            )
            
            # Date range picker
            min_date = contam_data['ActivityStartDate'].min().date()
            max_date = contam_data['ActivityStartDate'].max().date()
            date_range = st.date_input(
                "Select date range:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            # Filter button
            filter_button = st.button("Apply Filters")
            
        except Exception as e:
            st.error(f"Error processing data: {str(e)}")
            st.stop()

# Main content area
if part2_file is not None and 'df2' in locals():
    # Apply filters when button is clicked
    if filter_button:
        try:
            # Filter by contaminant
            filtered_data = df2[df2['CharacteristicName'] == selected_contaminant]
            
            # Filter by value range
            filtered_data = filtered_data[
                (filtered_data['ResultMeasureValue'] >= value_range[0]) & 
                (filtered_data['ResultMeasureValue'] <= value_range[1])
            ]
            
            # Filter by date range
            if len(date_range) == 2:
                filtered_data = filtered_data[
                    (filtered_data['ActivityStartDate'].dt.date >= date_range[0]) & 
                    (filtered_data['ActivityStartDate'].dt.date <= date_range[1])
                ]
            
            # Display filtered data
            st.subheader(f"Filtered Data for {selected_contaminant}")
            st.dataframe(filtered_data)
            
            # Create two columns for map and time series
            col1, col2 = st.columns(2)
            
            with col1:
                # Create map
                st.subheader("Station Locations")
                if not filtered_data.empty:
                    # Get unique stations with their coordinates
                    stations = filtered_data.drop_duplicates(subset=['MonitoringLocationIdentifier'])
                    
                    # Create map centered on the mean of all stations
                    m = folium.Map(
                        location=[stations['ResultDepthHeightMeasure/MeasureValue'].mean(), 
                                 stations['ResultDepthAltitudeReferencePointText'].mean()],
                        zoom_start=10
                    )
                    
                    # Add markers for each station
                    for idx, row in stations.iterrows():
                        folium.Marker(
                            [row['ResultDepthHeightMeasure/MeasureValue'], 
                             row['ResultDepthAltitudeReferencePointText']],
                            popup=f"{row['MonitoringLocationIdentifier']}<br>{selected_contaminant}: {row['ResultMeasureValue']}"
                        ).add_to(m)
                    
                    # Display map
                    folium_static(m)
                else:
                    st.warning("No stations found with the selected filters.")
            
            with col2:
                # Create time series plot
                st.subheader(f"Trend of {selected_contaminant} Over Time")
                if not filtered_data.empty:
                    fig = px.line(
                        filtered_data,
                        x='ActivityStartDate',
                        y='ResultMeasureValue',
                        color='MonitoringLocationIdentifier',
                        labels={
                            'ActivityStartDate': 'Date',
                            'ResultMeasureValue': f'{selected_contaminant} ({filtered_data["ResultMeasure/MeasureUnitCode"].iloc[0]})',
                            'MonitoringLocationIdentifier': 'Station'
                        },
                        title=f'Trend of {selected_contaminant} Over Time'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No data available for the selected filters.")
                    
        except Exception as e:
            st.error(f"Error generating visualizations: {str(e)}")

elif part1_file is not None:
    st.warning("Part 1 data upload detected but functionality not yet implemented.")
else:
    st.info("Please upload water quality data files to begin analysis.")
