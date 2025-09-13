import pandas as pd
import folium
from folium.plugins import MarkerCluster
import sys
import os
import datetime

# Define a color palette and names for the insect groups
INSECT_GROUPS = {
    4: ('Butterflies', 'red'),
    8: ('Moths', 'blue'),
    5: ('Dragonflies', 'green'),
    14: ('Locusts and Crickets', 'purple'),
    17: ('Bees, Wasps and Ants', 'orange'),
    18: ('Flies', 'darkred'),
    16: ('Beetles', 'lightred'),
    15: ('Bugs, Plant Lice and Cicadas', 'beige'),
    6: ('Other Insects', 'darkblue')
}

def visualize_date_range_on_map(start_date_str, end_date_str):
    """
    Generates an interactive map of the Netherlands with clustered, color-coded
    insect observations for a given date range.
    """
    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    all_dfs = []
    # Iterate through each day in the date range
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
        print(f"No observation data found for the date range {start_date_str} to {end_date_str}.")
        return

    # Concatenate all dataframes and drop duplicates
    combined_df = pd.concat(all_dfs, ignore_index=True)
    combined_df.drop_duplicates(subset='id', inplace=True)
    
    # Filter out invalid coordinates
    combined_df.dropna(subset=['longitude', 'latitude'], inplace=True)
    bounds = {
        'lon_min': 3.2, 'lon_max': 7.3,
        'lat_min': 50.75, 'lat_max': 53.7
    }
    combined_df = combined_df[
        (combined_df['longitude'] >= bounds['lon_min']) & (combined_df['longitude'] <= bounds['lon_max']) &
        (combined_df['latitude'] >= bounds['lat_min']) & (combined_df['latitude'] <= bounds['lat_max'])
    ]

    if combined_df.empty:
        print("No observations found within the geographical bounds of the Netherlands for the given range.")
        return

    # Create a map centered on the Netherlands
    map_center = [52.1326, 5.2913]
    m = folium.Map(location=map_center, zoom_start=7)
    marker_cluster = MarkerCluster().add_to(m)

    # Add points to the map with the group's color
    for idx, row in combined_df.iterrows():
        group_id = row['group_id']
        group_name, group_color = INSECT_GROUPS.get(group_id, ('Unknown', 'gray'))
        popup_text = (
            f"<b>Group:</b> {group_name}<br>"
            f"<b>Species:</b> {row['common_name']}<br>"
            f"<i>({row['scientific_name']})</i><br>"
            f"<b>Observer:</b> {row['observer']}<br>"
            f"<b>Location:</b> {row['location']}"
        )
        folium.Marker(
            [row['latitude'], row['longitude']],
            popup=popup_text,
            icon=folium.Icon(color=group_color, icon='info-sign')
        ).add_to(marker_cluster)

    # Add a legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 220px; height: 250px; 
                border:2px solid grey; z-index:9999; font-size:14px;
                background-color:white;
                ">&nbsp;<b>Insect Groups Legend</b><br>
    '''
    for group_id, (name, color) in INSECT_GROUPS.items():
        legend_html += f'&nbsp;<i class="fa fa-circle" style="color:{color}"></i>&nbsp;{name}<br>'
    legend_html += '</div>'
    m.get_root().html.add_child(folium.Element(legend_html))

    # Save the map to an HTML file
    output_filename = f'interactive_map_{start_date_str}_to_{end_date_str}.html'
    m.save(output_filename)
    print(f"Interactive map saved to {output_filename}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python visualize_map.py <start_date YYYY-MM-DD> <end_date YYYY-MM-DD>")
        sys.exit(1)
    
    start_date_str = sys.argv[1]
    end_date_str = sys.argv[2]
    
    visualize_date_range_on_map(start_date_str, end_date_str)
