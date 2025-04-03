import streamlit as st
import pandas as pd

# Set page config
st.set_page_config(page_title="Water Quality Analyzer", layout="wide")

# App title
st.title("🌊 Water Quality Dashboard")

# File upload section - SIMPLIFIED
st.sidebar.header("Upload Your Files")
results_file = st.sidebar.file_uploader("Water Quality Results (CSV)", type=["csv"])
stations_file = st.sidebar.file_uploader("Station Locations (CSV)", type=["csv"])

# Process results data
if results_file is not None:
    df_results = pd.read_csv(results_file)
    st.subheader("Water Quality Data")
    st.dataframe(df_results)
    
    # Show available characteristics
    if 'CharacteristicName' in df_results.columns:
        selected_contaminant = st.selectbox(
            "Select Characteristic to Analyze",
            df_results['CharacteristicName'].unique()
        )
        
        # Filter and show data
        filtered = df_results[df_results['CharacteristicName'] == selected_contaminant]
        st.line_chart(filtered.set_index('ActivityStartDate')['ResultMeasureValue'])

# Process stations data - SIMPLIFIED MAP
if stations_file is not None:
    df_stations = pd.read_csv(stations_file)
    st.subheader("Station Locations")
    
    # Simple map - just needs lat/lon columns
    if 'LatitudeMeasure' in df_stations.columns and 'LongitudeMeasure' in df_stations.columns:
        st.map(df_stations.rename(columns={
            'LatitudeMeasure': 'lat',
            'LongitudeMeasure': 'lon'
        }))
    else:
        st.warning("Station file needs 'LatitudeMeasure' and 'LongitudeMeasure' columns")

if results_file is None and stations_file is None:
    st.info("Please upload both files to begin analysis")
