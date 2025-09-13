# Insect Population Visualization

This project visualizes insect population data from the Netherlands using the [waarneming.nl](https://waarneming.nl/api/docs/) API. It fetches observation data for various insect groups and creates interactive maps to show their distribution over time.

## Features

- **Data Fetching**: Downloads insect observation data from the waarneming.nl API for multiple insect groups
- **Interactive Maps**: Creates interactive Leaflet maps with clustered markers and color-coded insect groups
- **Date Range Support**: Can visualize data for specific dates or date ranges
- **Duplicate Handling**: Automatically removes duplicate observations when combining data from multiple days
- **Geographic Filtering**: Filters observations to only show those within the Netherlands boundaries

## Prerequisites

Make sure you have the following Python packages installed:

```bash
pip install requests pandas folium
```

## Usage

### 1. Downloading Data

Use `main.py` to fetch observation data from the API:

```bash
python main.py
```

This script will:
- Clean up any existing observation CSV files
- Fetch data for the last 30 days
- Create separate CSV files for each day and insect group (e.g., `observations_2025-08-14_4.csv`)
- Use concurrent threads to speed up the data fetching process

**Note**: The script fetches data for 9 different insect groups:
- Butterflies (ID: 4)
- Moths (ID: 8)
- Dragonflies (ID: 5)
- Locusts and Crickets (ID: 14)
- Bees, Wasps and Ants (ID: 17)
- Flies (ID: 18)
- Beetles (ID: 16)
- Bugs, Plant Lice and Cicadas (ID: 15)
- Other Insects (ID: 6)

### 2. Generating Maps

Use `visualize_map.py` to create interactive maps from the downloaded data.

#### For a date range (general data):
```bash
python visualize_map.py 2025-08-14 2025-08-16
```

#### For Amsterdam-specific data:
```bash
python visualize_map.py 2025-08-14 2025-08-16 --amsterdam
```

#### Disable green roof visualization:
```bash
python visualize_map.py 2025-08-14 2025-08-16 --amsterdam --no-green-roofs
```

**Note**: The `--amsterdam` flag uses the pre-filtered Amsterdam data from the `data/amsterdam/` folder, which provides a more focused view of insect observations within the Amsterdam area.

**Green Roofs**: By default, the map includes green roof data from `DAKEN.csv` as green circles, where the circle size is proportional to the green area (`Groen_m2` field). Use `--no-green-roofs` to disable this feature.

The script will:
- Read all relevant CSV files for the specified date(s)
- Combine and de-duplicate the data
- Create an interactive HTML map with:
  - Clustered markers for better performance
  - Color-coded pins for different insect groups
  - Pop-up information for each observation
  - A legend showing the color coding

## Output Files

### Data Files
- `observations_YYYY-MM-DD_GROUPID.csv`: Raw observation data for a specific date and insect group
- Each CSV contains columns: `id`, `common_name`, `scientific_name`, `date`, `time`, `count`, `longitude`, `latitude`, `location`, `observer`

### Map Files
- `interactive_map_YYYY-MM-DD_to_YYYY-MM-DD.html`: Interactive map for a date range (general data)
- `interactive_map_YYYY-MM-DD_to_YYYY-MM-DD_amsterdam.html`: Interactive map for a date range (Amsterdam data)

## Map Features

- **Zoom and Pan**: Interactive navigation
- **Marker Clustering**: Groups nearby observations for better performance
- **Color Coding**: Each insect group has a unique color
- **Pop-up Information**: Click on markers to see details about each observation
- **Green Roof Visualization**: Green circles showing green roof locations (size proportional to green area)
- **Legend**: Shows the color coding for each insect group and green roof information
- **Geographic Filtering**: Only shows observations within the Netherlands boundaries

## Troubleshooting

### API Rate Limiting
If you encounter "Too Many Requests" errors, the script will automatically retry with exponential backoff. You can also reduce the number of concurrent threads by modifying `max_workers` in `main.py`.

### Missing Data Files
If the visualization script can't find data files for a specific date, it will show a warning and skip that data. Make sure you've run `main.py` first to download the data.

### Geographic Bounds
The script filters observations to only show those within the Netherlands boundaries:
- Longitude: 3.2° to 7.3°
- Latitude: 50.75° to 53.7°

## Customization

### Changing Date Range
Modify the date range in `main.py` by changing these lines:
```python
start_date = today - datetime.timedelta(days=30)  # Change 30 to desired number of days
```

### Adding More Insect Groups
Add new group IDs to the `INSECT_GROUP_IDS` list in `main.py` and update the `INSECT_GROUPS` dictionary in `visualize_map.py` with the corresponding names and colors.

### Modifying Map Appearance
You can customize the map appearance by modifying the `folium.Map` parameters in `visualize_map.py`, such as:
- `zoom_start`: Initial zoom level
- `location`: Map center coordinates
- Marker colors and icons
- Legend styling

## License

This project is for educational and research purposes. Please respect the waarneming.nl API terms of service when using their data.
