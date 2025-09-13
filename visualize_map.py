import pandas as pd
import folium
from folium.plugins import MarkerCluster
import sys
import os
import datetime
import argparse

# Define a color palette and names for the insect groups
# Using colors distinct from green (used for green roofs)
INSECT_GROUPS = {
    4: ('Butterflies', 'red'),
    8: ('Moths', 'blue'),
    5: ('Dragonflies', 'darkblue'),
    14: ('Locusts and Crickets', 'purple'),
    17: ('Bees, Wasps and Ants', 'orange'),
    18: ('Flies', 'darkred'),
    16: ('Beetles', 'lightred'),
    15: ('Bugs, Plant Lice and Cicadas', 'pink'),
    6: ('Other Insects', 'gray')
}

def load_green_roof_data():
    """
    Load green roof data from DAKEN.csv file.
    Returns DataFrame with coordinates and green area data.
    """
    try:
        df = pd.read_csv('DAKEN.csv', sep=';')
        # Filter out rows with missing coordinates or green area data
        df = df.dropna(subset=['LNG', 'LAT', 'Groen_m2'])
        # Convert to numeric
        df['LNG'] = pd.to_numeric(df['LNG'], errors='coerce')
        df['LAT'] = pd.to_numeric(df['LAT'], errors='coerce')
        df['Groen_m2'] = pd.to_numeric(df['Groen_m2'], errors='coerce')
        # Remove any remaining invalid data
        df = df.dropna(subset=['LNG', 'LAT', 'Groen_m2'])
        return df
    except Exception as e:
        print(f"Error loading green roof data: {e}")
        return pd.DataFrame()

def visualize_date_range_on_map(start_date_str, end_date_str, use_amsterdam=False, show_green_roofs=True, max_observations=5000):
    """
    Generates an interactive map of the Netherlands with clustered, color-coded
    insect observations for a given date range.
    
    Args:
        start_date_str: Start date in YYYY-MM-DD format
        end_date_str: End date in YYYY-MM-DD format
        use_amsterdam: If True, use Amsterdam-specific data files
        show_green_roofs: If True, overlay green roof data as circles
        max_observations: Maximum number of observations to include (for performance)
    """
    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    all_dfs = []
    
    if use_amsterdam:
        # Use Amsterdam-specific data files
        print("Using Amsterdam-specific data...")
        for date in pd.date_range(start_date, end_date):
            date_str = date.strftime('%Y-%m-%d')
            filename = f'data/amsterdam/amsterdam_observations_{date_str}.csv'
            if os.path.exists(filename):
                try:
                    df = pd.read_csv(filename)
                    if not df.empty:
                        all_dfs.append(df)
                        print(f"  Loaded {len(df)} Amsterdam observations for {date_str}")
                except Exception as e:
                    print(f"Error reading Amsterdam data for {date_str}: {e}")
    else:
        # Use general observation files
        print("Using general observation data...")
        for date in pd.date_range(start_date, end_date):
            date_str = date.strftime('%Y-%m-%d')
            # Iterate through each insect group for that day
            for group_id in INSECT_GROUPS:
                filename = f'observations_{date_str}_{group_id}.csv'
                if os.path.exists(filename):
                    try:
                        df = pd.read_csv(filename)
                        if not df.empty:
                            df['group_id'] = group_id
                            all_dfs.append(df)
                    except Exception as e:
                        print(f"Error reading or processing CSV for group {group_id} on {date_str}: {e}")

    if not all_dfs:
        data_type = "Amsterdam" if use_amsterdam else "general"
        print(f"No {data_type} observation data found for the date range {start_date_str} to {end_date_str}.")
        return

    # Concatenate all dataframes and drop duplicates
    combined_df = pd.concat(all_dfs, ignore_index=True)
    combined_df.drop_duplicates(subset=['id'], inplace=True)
    
    # # Sample data if too many observations (for performance)
    # if len(combined_df) > max_observations:
    #     print(f"Sampling {max_observations} observations from {len(combined_df)} total observations for better performance")
    #     combined_df = combined_df.sample(n=max_observations, random_state=42)
    
    # Filter out invalid coordinates
    combined_df.dropna(subset=['longitude', 'latitude'], inplace=True)
    
    # Apply geographic filtering based on data type
    if use_amsterdam:
        # Amsterdam data is already filtered, but we can apply Netherlands bounds as backup
        bounds = {
            'lon_min': 3.2, 'lon_max': 7.3,
            'lat_min': 50.75, 'lat_max': 53.7
        }
    else:
        # General data needs Netherlands filtering
        bounds = {
            'lon_min': 3.2, 'lon_max': 7.3,
            'lat_min': 50.75, 'lat_max': 53.7
        }
    
    combined_df = combined_df[
        (combined_df['longitude'] >= bounds['lon_min']) & (combined_df['longitude'] <= bounds['lon_max']) &
        (combined_df['latitude'] >= bounds['lat_min']) & (combined_df['latitude'] <= bounds['lat_max'])
    ]

    if combined_df.empty:
        data_type = "Amsterdam" if use_amsterdam else "general"
        print(f"No {data_type} observations found within the geographical bounds for the given range.")
        return

    # Create a map centered on the Netherlands (or Amsterdam if using Amsterdam data)
    if use_amsterdam:
        map_center = [52.3676, 4.9041]  # Amsterdam center
        zoom_start = 10
        map_title = "Amsterdam"
    else:
        map_center = [52.1326, 5.2913]  # Netherlands center
        zoom_start = 7
        map_title = "Netherlands"
    
    m = folium.Map(location=map_center, zoom_start=zoom_start)
    
    # Create layer groups for different species with clustering
    species_layers = {}
    for group_id, (name, color) in INSECT_GROUPS.items():
        species_layers[group_id] = folium.FeatureGroup(name=f"Insect: {name}")
    
    # Create green roof layer
    green_roof_layer = folium.FeatureGroup(name="Green Roofs")
    
    # Add green roof data as circles (if requested)
    if show_green_roofs:
        green_roof_df = load_green_roof_data()
        if not green_roof_df.empty:
            print(f"Loading {len(green_roof_df)} green roof locations...")
            
            # Calculate radius range (min 5m, max 50m) based on green area
            min_area = green_roof_df['Groen_m2'].min()
            max_area = green_roof_df['Groen_m2'].max()
            
            for idx, row in green_roof_df.iterrows():
                # Calculate radius proportional to green area (5-50 pixels)
                area = row['Groen_m2']
                radius = 5 + (area - min_area) / (max_area - min_area) * 45
                
                # Create popup text
                popup_text = (
                    f"<b>Green Roof</b><br>"
                    f"<b>Address:</b> {row['Adres']}<br>"
                    f"<b>Green Area:</b> {area:.0f} m²<br>"
                    f"<b>Total Area:</b> {row['Totaal_m2']} m²<br>"
                    f"<b>District:</b> {row['Stadsdeel']}<br>"
                    f"<b>Year:</b> {row['Realisatiejaar']}"
                )
                
                # Add circle marker to green roof layer
                folium.CircleMarker(
                    location=[row['LAT'], row['LNG']],
                    radius=radius,
                    popup=popup_text,
                    color='green',
                    weight=2,
                    fillColor='lightgreen',
                    fillOpacity=0.6,
                    opacity=0.8
                ).add_to(green_roof_layer)
        else:
            print("No green roof data found or error loading data.")
    
    # Add green roof layer to map
    if show_green_roofs:
        green_roof_layer.add_to(m)
    
    # Group data by species for clustering
    species_data = {}
    for idx, row in combined_df.iterrows():
        # Handle both general data (with group_id) and Amsterdam data (with group_name)
        if 'group_id' in row and not pd.isna(row['group_id']):
            group_id = int(row['group_id'])
            group_name, group_color = INSECT_GROUPS.get(group_id, ('Unknown', 'gray'))
        elif 'group_name' in row and not pd.isna(row['group_name']):
            group_name = row['group_name']
            # Find the color and group_id for this group name
            # Handle both underscore and space versions
            group_color = 'gray'
            group_id = None
            for gid, (gname, gcolor) in INSECT_GROUPS.items():
                # Check both the original name and underscore version
                # Also handle the specific case of "Bugs, Plant Lice and Cicadas" vs "Bugs_Plant_Lice_and_Cicadas"
                normalized_gname = gname.replace(' ', '_').replace(',', '').replace('_', '')
                normalized_group_name = group_name.replace('_', '').replace(',', '')
                if (gname == group_name or 
                    gname.replace(' ', '_') == group_name or
                    normalized_gname == normalized_group_name):
                    group_color = gcolor
                    group_id = gid
                    break
        else:
            group_name = 'Unknown'
            group_color = 'gray'
            group_id = None
        
        if group_id not in species_data:
            species_data[group_id] = []
        
        species_data[group_id].append({
            'lat': row['latitude'],
            'lon': row['longitude'],
            'group_name': group_name,
            'group_color': group_color,
            'common_name': row['common_name'],
            'scientific_name': row['scientific_name'],
            'observer': row['observer'],
            'location': row['location']
        })
    
    # Add species layers to map with clustering
    for group_id, data_list in species_data.items():
        if group_id in species_layers:
            # Create a marker cluster for this species
            group_name, group_color = INSECT_GROUPS[group_id]
            
            # Create marker cluster with custom icon function
            marker_cluster = MarkerCluster(
                icon_create_function=f"""
                function(cluster) {{
                    var childCount = cluster.getChildCount();
                    var c = 'marker-cluster-{group_color}';
                    return new L.DivIcon({{
                        html: '<div><span>' + childCount + '</span></div>',
                        className: 'marker-cluster ' + c,
                        iconSize: new L.Point(40, 40)
                    }});
                }}
                """
            ).add_to(species_layers[group_id])
            
            for data in data_list:
                popup_text = (
                    f"<b>Group:</b> {data['group_name']}<br>"
                    f"<b>Species:</b> {data['common_name']}<br>"
                    f"<i>({data['scientific_name']})</i><br>"
                    f"<b>Observer:</b> {data['observer']}<br>"
                    f"<b>Location:</b> {data['location']}"
                )
                
                folium.Marker(
                    [data['lat'], data['lon']],
                    popup=popup_text,
                    icon=folium.Icon(color=data['group_color'], icon='info-sign')
                ).add_to(marker_cluster)
    
    # Add species layers to map
    for layer in species_layers.values():
        layer.add_to(m)

    # Add layer control for toggling layers
    folium.LayerControl().add_to(m)
    
    # Add custom CSS for colored marker clusters
    css_style = '''
    <style>
    .marker-cluster-small {
        background-color: rgba(181, 226, 140, 0.6);
    }
    .marker-cluster-small div {
        background-color: rgba(110, 204, 57, 0.6);
    }
    
    /* Custom colors for different species groups */
    .marker-cluster-red {
        background-color: rgba(255, 0, 0, 0.6) !important;
    }
    .marker-cluster-red div {
        background-color: rgba(200, 0, 0, 0.8) !important;
    }
    
    .marker-cluster-blue {
        background-color: rgba(0, 0, 255, 0.6) !important;
    }
    .marker-cluster-blue div {
        background-color: rgba(0, 0, 200, 0.8) !important;
    }
    
    .marker-cluster-darkblue {
        background-color: rgba(0, 0, 139, 0.6) !important;
    }
    .marker-cluster-darkblue div {
        background-color: rgba(0, 0, 100, 0.8) !important;
    }
    
    .marker-cluster-purple {
        background-color: rgba(128, 0, 128, 0.6) !important;
    }
    .marker-cluster-purple div {
        background-color: rgba(100, 0, 100, 0.8) !important;
    }
    
    .marker-cluster-orange {
        background-color: rgba(255, 165, 0, 0.6) !important;
    }
    .marker-cluster-orange div {
        background-color: rgba(200, 130, 0, 0.8) !important;
    }
    
    .marker-cluster-darkred {
        background-color: rgba(139, 0, 0, 0.6) !important;
    }
    .marker-cluster-darkred div {
        background-color: rgba(100, 0, 0, 0.8) !important;
    }
    
    .marker-cluster-lightred {
        background-color: rgba(255, 99, 99, 0.6) !important;
    }
    .marker-cluster-lightred div {
        background-color: rgba(200, 70, 70, 0.8) !important;
    }
    
    .marker-cluster-pink {
        background-color: rgba(255, 192, 203, 0.6) !important;
    }
    .marker-cluster-pink div {
        background-color: rgba(200, 150, 160, 0.8) !important;
    }
    
    .marker-cluster-gray {
        background-color: rgba(128, 128, 128, 0.6) !important;
    }
    .marker-cluster-gray div {
        background-color: rgba(100, 100, 100, 0.8) !important;
    }
    </style>
    '''
    
    # Add a simple legend
    legend_title = f"{map_title} Map Legend"
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 200px; height: 200px; 
                border:2px solid grey; z-index:9999; font-size:12px;
                background-color:white; padding: 10px; border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                ">&nbsp;<b>{legend_title}</b><br><br>
    '''
    
    # Add insect groups legend
    legend_html += '&nbsp;<b>Insect Groups:</b><br>'
    for group_id, (name, color) in INSECT_GROUPS.items():
        legend_html += f'&nbsp;<i class="fa fa-circle" style="color:{color}"></i>&nbsp;{name}<br>'
    
    # Add green roof information
    if show_green_roofs:
        legend_html += '<br>&nbsp;<b>Green Roofs:</b><br>'
        legend_html += '&nbsp;<i class="fa fa-circle" style="color:green"></i>&nbsp;Green roofs (size = area)<br>'
    
    legend_html += '<br>&nbsp;<b>Use the layer control</b><br>&nbsp;<b>in the top-right to</b><br>&nbsp;<b>toggle layers on/off</b>'
    legend_html += '</div>'
    
    # Add CSS and legend to map
    m.get_root().html.add_child(folium.Element(css_style))
    m.get_root().html.add_child(folium.Element(legend_html))

    # Save the map to an HTML file
    data_suffix = "_amsterdam" if use_amsterdam else ""
    output_filename = f'interactive_map_{start_date_str}_to_{end_date_str}{data_suffix}.html'
    m.save(output_filename)
    print(f"Interactive map saved to {output_filename}")

def main():
    parser = argparse.ArgumentParser(description='Generate interactive maps of insect observations')
    parser.add_argument('start_date', help='Start date in YYYY-MM-DD format')
    parser.add_argument('end_date', help='End date in YYYY-MM-DD format')
    parser.add_argument('--amsterdam', action='store_true', 
                       help='Use Amsterdam-specific data instead of general observation data')
    parser.add_argument('--no-green-roofs', action='store_true',
                       help='Disable green roof visualization')
    parser.add_argument('--max-observations', type=int, default=5000,
                       help='Maximum number of observations to include (default: 5000)')
    
    args = parser.parse_args()
    
    show_green_roofs = not args.no_green_roofs
    visualize_date_range_on_map(args.start_date, args.end_date, 
                               use_amsterdam=args.amsterdam, 
                               show_green_roofs=show_green_roofs,
                               max_observations=args.max_observations)

if __name__ == '__main__':
    main()