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
    results_file = st.file_uploader("Upload Water Quality Results (CSV)", type=["csv"])
    stations_file = st.file_uploader("Upload Stations Data (CSV)", type=["csv"])

# Function to create station map
def create_station_map(df):
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
            ax.scatter(org_df[lon_col], org_df[lat_col],
                       color=color, marker='o', s=50,
                       transform=ccrs.PlateCarree(),
                       alpha=0.7,
                       label=f'{org} Sites')
    
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

# Process results data
if results_file is not None:
    try:
        df_results = pd.read_csv(results_file)
        
        # Data processing
        if 'ActivityStartDate' in df_results.columns:
            df_results['ActivityStartDate'] = pd.to_datetime(df_results['ActivityStartDate'])
        if 'ResultMeasureValue' in df_results.columns:
            df_results['ResultMeasureValue'] = pd.to_numeric(df_results['ResultMeasureValue'], errors='coerce')
        
        # Get available contaminants
        if 'CharacteristicName' in df_results.columns:
            contaminants = df_results['CharacteristicName'].unique()
            selected_contaminant = st.selectbox("Select Contaminant", contaminants)
            
            # Filters
            contam_data = df_results[df_results['CharacteristicName'] == selected_contaminant]
            
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
                        max_value=max_date
                    )
                
                # Apply filters
                filtered = df_results[
                    (df_results['CharacteristicName'] == selected_contaminant) &
                    (df_results['ResultMeasureValue'] >= value_range[0]) &
                    (df_results['ResultMeasureValue'] <= value_range[1])
                ]
                
                if 'ActivityStartDate' in filtered.columns:
                    filtered = filtered[
                        (filtered['ActivityStartDate'].dt.date >= date_range[0]) &
                        (filtered['ActivityStartDate'].dt.date <= date_range[1])
                    ]
                
                st.subheader(f"Filtered Data: {selected_contaminant}")
                st.dataframe(filtered)
                
                # Time series plot
                if not filtered.empty and 'ActivityStartDate' in filtered.columns:
                    st.subheader("Trend Over Time")
                    chart_data = filtered.set_index('ActivityStartDate')[['ResultMeasureValue']]
                    st.line_chart(chart_data)
                
    except Exception as e:
        st.error(f"Error processing results data: {str(e)}")

# Process stations data
if stations_file is not None:
    try:
        df_stations = pd.read_csv(stations_file)
        st.subheader("Station Information")
        st.dataframe(df_stations)
        
        # Create map
        if 'LatitudeMeasure' in df_stations.columns and 'LongitudeMeasure' in df_stations.columns:
            st.subheader("Station Locations")
            
            # Option 1: Simple Streamlit map
            st.map(df_stations.rename(columns={
                'LatitudeMeasure': 'lat',
                'LongitudeMeasure': 'lon'
            }))
            
            # Option 2: Advanced Cartopy map
            st.subheader("Detailed Station Map")
            fig = create_station_map(df_stations)
            
            # Save figure to a bytes buffer and display
            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
            st.image(buf, use_column_width=True)
            
            # Show station statistics
            st.subheader("Station Statistics")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("Monitoring Location Types:")
                st.write(df_stations['MonitoringLocationTypeName'].value_counts())
            
            with col2:
                st.write("Organizations:")
                st.write(df_stations['OrganizationIdentifier'].value_counts())
                
    except Exception as e:
        st.error(f"Error processing stations data: {str(e)}")

if results_file is None and stations_file is None:
    st.info("Please upload data files to begin analysis")
