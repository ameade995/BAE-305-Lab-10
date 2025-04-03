import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from io import BytesIO

# Set page config
st.set_page_config(page_title="Water Quality Analyzer", layout="wide")

# App title
st.title("🌊 Water Quality Dashboard")

# Sidebar for file uploads
with st.sidebar:
    st.header("Upload Data")
    # File uploaders now appear together
    uploaded_files = st.file_uploader(
        "Upload both Water Quality Results and Stations Data",
        type=["csv"],
        accept_multiple_files=True
    )
    
    # Separate the files after upload
    results_file = None
    stations_file = None
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            if "result" in uploaded_file.name.lower():
                results_file = uploaded_file
            elif "station" in uploaded_file.name.lower():
                stations_file = uploaded_file
            else:
                # Auto-detect based on columns if filenames don't match
                peek = pd.read_csv(uploaded_file, nrows=1)
                if "CharacteristicName" in peek.columns:
                    results_file = uploaded_file
                elif "MonitoringLocationIdentifier" in peek.columns:
                    stations_file = uploaded_file

# Function to create station map
def create_station_map(df):
    try:
        # Identify coordinate columns
        lat_col = 'LatitudeMeasure'
        lon_col = 'LongitudeMeasure'
        
        # Create figure
        fig = plt.figure(figsize=(14, 8))
        ax = plt.axes(projection=ccrs.PlateCarree())
        
        # Add map features
        ax.add_feature(cfeature.LAND, facecolor='lightgray')
        ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
        ax.add_feature(cfeature.COASTLINE, edgecolor='black')
        ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='gray')
        ax.add_feature(cfeature.LAKES, alpha=0.5, facecolor='lightblue')
        ax.add_feature(cfeature.RIVERS, edgecolor='lightblue')
        ax.add_feature(cfeature.STATES, linestyle=':', edgecolor='gray')
        
        # Plot monitoring locations with different colors by organization
        org_colors = {
            'USGS-KY': 'blue',
            '11NPSWRD_WQX': 'green',
            '31ORWUNT_WQX': 'red'
        }
        
        for org, color in org_colors.items():
            org_df = df[df['OrganizationIdentifier'] == org]
            if not org_df.empty:
                ax.scatter(
                    org_df[lon_col], 
                    org_df[lat_col],
                    color=color, 
                    marker='o', 
                    s=50,
                    transform=ccrs.PlateCarree(),
                    alpha=0.7,
                    label=f'{org} Sites'
                )
        
        # Set map extent with buffer
        buffer = 1.5  # degrees of buffer around stations
        ax.set_extent([
            df[lon_col].min() - buffer,
            df[lon_col].max() + buffer,
            df[lat_col].min() - buffer,
            df[lat_col].max() + buffer
        ])
        
        # Add title and legend
        plt.title('Water Quality Monitoring Stations', fontsize=16, pad=20)
        plt.legend(loc='upper right')
        
        # Add gridlines
        gl = ax.gridlines(draw_labels=True, linestyle='--', alpha=0.5)
        gl.top_labels = False
        gl.right_labels = False
        
        return fig
    except Exception as e:
        st.error(f"Error creating map: {str(e)}")
        return None

# Main display area
tab1, tab2 = st.tabs(["Results Analysis", "Station Mapping"])

with tab1:
    if results_file is not None:
        try:
            df_results = pd.read_csv(results_file)
            
            # Data processing
            if 'ActivityStartDate' in df_results.columns:
                df_results['ActivityStartDate'] = pd.to_datetime(df_results['ActivityStartDate'])
            
            # Let user select which characteristic to analyze
            if 'CharacteristicName' in df_results.columns:
                characteristics = df_results['CharacteristicName'].unique()
                selected_characteristic = st.selectbox(
                    "Select Characteristic to Analyze",
                    characteristics,
                    key="char_select"
                )
                
                # Filter data for selected characteristic
                char_data = df_results[df_results['CharacteristicName'] == selected_characteristic]
                
                # Let user select specific measurement if available
                if 'ResultMeasureValue' in char_data.columns:
                    char_data['ResultMeasureValue'] = pd.to_numeric(
                        char_data['ResultMeasureValue'], 
                        errors='coerce'
                    )
                    
                    # Date range selector
                    if 'ActivityStartDate' in char_data.columns:
                        min_date = char_data['ActivityStartDate'].min().date()
                        max_date = char_data['ActivityStartDate'].max().date()
                        date_range = st.date_input(
                            "Select Date Range",
                            value=[min_date, max_date],
                            min_value=min_date,
                            max_value=max_date,
                            key="date_range"
                        )
                    
                    # Value range slider
                    min_val = float(char_data['ResultMeasureValue'].min())
                    max_val = float(char_data['ResultMeasureValue'].max())
                    value_range = st.slider(
                        "Select Value Range",
                        min_value=min_val,
                        max_value=max_val,
                        value=(min_val, max_val),
                        key="value_range"
                    )
                    
                    # Apply filters
                    filtered = char_data[
                        (char_data['ResultMeasureValue'] >= value_range[0]) &
                        (char_data['ResultMeasureValue'] <= value_range[1])
                    ]
                    
                    if 'ActivityStartDate' in filtered.columns and len(date_range) == 2:
                        filtered = filtered[
                            (filtered['ActivityStartDate'].dt.date >= date_range[0]) &
                            (filtered['ActivityStartDate'].dt.date <= date_range[1])
                        ]
                    
                    # Display filtered data
                    st.subheader(f"Filtered Data for {selected_characteristic}")
                    st.dataframe(filtered)
                    
                    # Visualization
                    if not filtered.empty:
                        if 'ActivityStartDate' in filtered.columns:
                            st.subheader("Trend Over Time")
                            chart_data = filtered.set_index('ActivityStartDate')[['ResultMeasureValue']]
                            st.line_chart(chart_data)
                        
                        # Show statistics
                        st.subheader("Statistics")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric(
                                "Average Value", 
                                f"{filtered['ResultMeasureValue'].mean():.2f}"
                            )
                        
                        with col2:
                            st.metric(
                                "Number of Measurements",
                                len(filtered)
                            )
            
        except Exception as e:
            st.error(f"Error processing results: {str(e)}")
    else:
        st.info("Upload water quality results data to see analysis")

with tab2:
    if stations_file is not None:
        try:
            df_stations = pd.read_csv(stations_file)
            
            # Let user select what to display
            st.subheader("Station Data")
            
            # Column selection
            default_cols = [
                'MonitoringLocationIdentifier',
                'MonitoringLocationName',
                'MonitoringLocationTypeName',
                'LatitudeMeasure',
                'LongitudeMeasure',
                'OrganizationIdentifier'
            ]
            available_cols = [col for col in default_cols if col in df_stations.columns]
            
            selected_cols = st.multiselect(
                "Select columns to display",
                df_stations.columns,
                default=available_cols,
                key="station_cols"
            )
            
            # Display station data
            st.dataframe(df_stations[selected_cols])
            
            # Mapping options
            st.subheader("Mapping Options")
            map_type = st.radio(
                "Select map type",
                ["Simple Interactive Map", "Detailed Geographic Map"],
                key="map_type"
            )
            
            if 'LatitudeMeasure' in df_stations.columns and 'LongitudeMeasure' in df_stations.columns:
                if map_type == "Simple Interactive Map":
                    st.map(df_stations.rename(columns={
                        'LatitudeMeasure': 'lat',
                        'LongitudeMeasure': 'lon'
                    }))
                else:
                    fig = create_station_map(df_stations)
                    if fig:
                        buf = BytesIO()
                        fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
                        st.image(buf, use_column_width=True)
            
            # Station statistics
            st.subheader("Station Statistics")
            
            if 'MonitoringLocationTypeName' in df_stations.columns:
                st.write("**By Location Type:**")
                st.bar_chart(df_stations['MonitoringLocationTypeName'].value_counts())
            
            if 'OrganizationIdentifier' in df_stations.columns:
                st.write("**By Organization:**")
                st.bar_chart(df_stations['OrganizationIdentifier'].value_counts())
                
        except Exception as e:
            st.error(f"Error processing stations: {str(e)}")
    else:
        st.info("Upload station location data to see mapping")

if not uploaded_files:
    st.info("Please upload both water quality results and station location files")
