import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Set page config
st.set_page_config(page_title="Water Quality Analyzer", layout="wide")

# App title
st.title("🌊 Water Quality Contaminant Analyzer")

# Try to import folium with fallback
try:
    import folium
    from streamlit_folium import folium_static
    folium_available = True
except ImportError:
    folium_available = False
    st.warning("Map functionality disabled - folium package not installed")

# Sidebar for file upload and filters
with st.sidebar:
    st.header("Upload Data")
    part2_file = st.file_uploader("Upload Water Quality Data (CSV)", type=["csv"])
    
    if part2_file is not None:
        try:
            df = pd.read_csv(part2_file)
            
            # Data processing
            df['ActivityStartDate'] = pd.to_datetime(df['ActivityStartDate'])
            df['ResultMeasureValue'] = pd.to_numeric(df['ResultMeasureValue'], errors='coerce')
            
            # Get available contaminants
            contaminants = df['CharacteristicName'].unique()
            selected_contaminant = st.selectbox("Select Contaminant", contaminants)
            
            # Filters
            contam_data = df[df['CharacteristicName'] == selected_contaminant]
            min_val, max_val = contam_data['ResultMeasureValue'].min(), contam_data['ResultMeasureValue'].max()
            
            value_range = st.slider(
                "Value Range",
                min_value=float(min_val),
                max_value=float(max_val),
                value=(float(min_val), float(max_val))
            )
            
            min_date = contam_data['ActivityStartDate'].min().date()
            max_date = contam_data['ActivityStartDate'].max().date()
            date_range = st.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            st.stop()

# Main display
if part2_file is not None:
    try:
        # Apply filters
        filtered = df[
            (df['CharacteristicName'] == selected_contaminant) &
            (df['ResultMeasureValue'] >= value_range[0]) &
            (df['ResultMeasureValue'] <= value_range[1]) &
            (df['ActivityStartDate'].dt.date >= date_range[0]) &
            (df['ActivityStartDate'].dt.date <= date_range[1])
        ]
        
        st.subheader(f"Filtered Data: {selected_contaminant}")
        st.dataframe(filtered)
        
        # Create columns for visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            # Time series plot
            st.subheader("Trend Over Time")
            fig = px.line(
                filtered,
                x='ActivityStartDate',
                y='ResultMeasureValue',
                color='MonitoringLocationIdentifier',
                labels={
                    'ActivityStartDate': 'Date',
                    'ResultMeasureValue': f'{selected_contaminant} Concentration'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Map display (only if folium available)
            if folium_available and not filtered.empty:
                st.subheader("Station Locations")
                try:
                    # Create map
                    m = folium.Map(
                        location=[
                            filtered['ResultDepthHeightMeasure/MeasureValue'].mean(),
                            filtered['ResultDepthAltitudeReferencePointText'].mean()
                        ],
                        zoom_start=10
                    )
                    
                    # Add markers
                    for _, row in filtered.iterrows():
                        folium.Marker(
                            [row['ResultDepthHeightMeasure/MeasureValue'],
                             row['ResultDepthAltitudeReferencePointText']],
                            popup=f"{row['MonitoringLocationIdentifier']}<br>{row['ResultMeasureValue']}"
                        ).add_to(m)
                    
                    folium_static(m)
                except Exception as e:
                    st.warning(f"Could not display map: {str(e)}")
            elif not folium_available:
                st.warning("Map display requires folium package")
            else:
                st.warning("No location data available")
                
    except Exception as e:
        st.error(f"Error displaying data: {str(e)}")
else:
    st.info("Please upload a water quality data file to begin analysis")
