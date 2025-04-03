import streamlit as st
import pandas as pd
from datetime import datetime

# Set page config
st.set_page_config(page_title="Water Quality Analyzer", layout="wide")

# App title
st.title("🌊 Water Quality Contaminant Analyzer")

# Sidebar for file upload and filters
with st.sidebar:
    st.header("Upload Data")
    uploaded_file = st.file_uploader("Upload Water Quality Data (CSV)", type=["csv"])
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            
            # Basic data processing
            if 'ActivityStartDate' in df.columns:
                df['ActivityStartDate'] = pd.to_datetime(df['ActivityStartDate'])
            if 'ResultMeasureValue' in df.columns:
                df['ResultMeasureValue'] = pd.to_numeric(df['ResultMeasureValue'], errors='coerce')
            
            # Get available contaminants if column exists
            if 'CharacteristicName' in df.columns:
                contaminants = df['CharacteristicName'].unique()
                selected_contaminant = st.selectbox("Select Contaminant", contaminants)
                
                # Filters
                contam_data = df[df['CharacteristicName'] == selected_contaminant]
                
                if not contam_data.empty and 'ResultMeasureValue' in contam_data.columns:
                    min_val = float(contam_data['ResultMeasureValue'].min())
                    max_val = float(contam_data['ResultMeasureValue'].max())
                    
                    value_range = st.slider(
                        "Value Range",
                        min_value=min_val,
                        max_value=max_val,
                        value=(min_val, max_val)
                    )
                    if 'ActivityStartDate' in contam_data.columns:
                        min_date = contam_data['ActivityStartDate'].min().date()
                        max_date = contam_data['ActivityStartDate'].max().date()
                        date_range = st.date_input(
                            "Date Range",
                            value=(min_date, max_date),
                            min_value=min_date,
                            max_value=max_date)
            
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            st.stop()

# Main display
if uploaded_file is not None and 'CharacteristicName' in df.columns:
    try:
        # Apply filters
        filtered = df[
            (df['CharacteristicName'] == selected_contaminant) &
            (df['ResultMeasureValue'] >= value_range[0]) &
            (df['ResultMeasureValue'] <= value_range[1])
        ]
        
        if 'ActivityStartDate' in filtered.columns:
            filtered = filtered[
                (filtered['ActivityStartDate'].dt.date >= date_range[0]) &
                (filtered['ActivityStartDate'].dt.date <= date_range[1])
            ]
        
        st.subheader(f"Filtered Data: {selected_contaminant}")
        st.dataframe(filtered)
        
        # Create columns for visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            # Time series plot using Streamlit's native line_chart
            if not filtered.empty and 'ActivityStartDate' in filtered.columns:
                st.subheader("Trend Over Time")
                # Prepare data for line chart
                chart_data = filtered.set_index('ActivityStartDate')[['ResultMeasureValue']]
                st.line_chart(chart_data)
            else:
                st.warning("No date data available for time series")
        
        with col2:
            # Simple map using streamlit's native map
            if not filtered.empty and 'LatitudeMeasure' in filtered.columns and 'LongitudeMeasure' in filtered.columns:
                st.subheader("Station Locations")
                st.map(filtered[['LatitudeMeasure', 'LongitudeMeasure']].dropna())
            else:
                st.warning("No location data available for mapping")
                
    except Exception as e:
        st.error(f"Error displaying data: {str(e)}")
else:
    st.info("Please upload a water quality data file to begin analysis")
