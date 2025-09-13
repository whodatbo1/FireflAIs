#!/usr/bin/env python3
"""
Script to filter all observation data to only include entries within the Amsterdam area.
Reads all available CSV files and saves filtered data to data/amsterdam/ folder.
"""

import pandas as pd
import os
import glob
from datetime import datetime

# Amsterdam area boundaries (approximate)
AMSTERDAM_BOUNDS = {
    'lon_min': 4.7,   # Western boundary
    'lon_max': 5.1,   # Eastern boundary  
    'lat_min': 52.2,  # Southern boundary
    'lat_max': 52.5   # Northern boundary
}

# Insect group names for reference
INSECT_GROUPS = {
    4: 'Butterflies',
    8: 'Moths', 
    5: 'Dragonflies',
    14: 'Locusts_and_Crickets',
    17: 'Bees_Wasps_and_Ants',
    18: 'Flies',
    16: 'Beetles',
    15: 'Bugs_Plant_Lice_and_Cicadas',
    6: 'Other_Insects'
}

def is_in_amsterdam_area(lat, lon):
    """
    Check if coordinates are within Amsterdam area boundaries.
    """
    if pd.isna(lat) or pd.isna(lon):
        return False
    
    return (AMSTERDAM_BOUNDS['lat_min'] <= lat <= AMSTERDAM_BOUNDS['lat_max'] and
            AMSTERDAM_BOUNDS['lon_min'] <= lon <= AMSTERDAM_BOUNDS['lon_max'])

def process_observation_file(filepath):
    """
    Process a single observation CSV file and filter for Amsterdam area.
    Returns filtered DataFrame or None if no data.
    """
    try:
        df = pd.read_csv(filepath)
        if df.empty:
            return None
            
        # Filter for valid coordinates and Amsterdam area
        df = df.dropna(subset=['longitude', 'latitude'])
        amsterdam_mask = df.apply(
            lambda row: is_in_amsterdam_area(row['latitude'], row['longitude']), 
            axis=1
        )
        
        filtered_df = df[amsterdam_mask].copy()
        
        if filtered_df.empty:
            return None
            
        # Add group name for easier identification
        filename = os.path.basename(filepath)
        group_id = int(filename.split('_')[-1].split('.')[0])
        filtered_df['group_name'] = INSECT_GROUPS.get(group_id, f'Group_{group_id}')
        
        return filtered_df
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return None

def main():
    """
    Main function to process all observation files and create Amsterdam-filtered datasets.
    """
    print("Starting Amsterdam data filtering...")
    
    # Find all observation CSV files
    observation_files = glob.glob("observations_*.csv")
    
    if not observation_files:
        print("No observation files found!")
        return
    
    print(f"Found {len(observation_files)} observation files to process")
    
    # Process all files and collect Amsterdam data
    all_amsterdam_data = []
    processed_files = 0
    amsterdam_observations = 0
    
    for filepath in observation_files:
        print(f"Processing {filepath}...")
        filtered_df = process_observation_file(filepath)
        
        if filtered_df is not None:
            all_amsterdam_data.append(filtered_df)
            amsterdam_observations += len(filtered_df)
            print(f"  Found {len(filtered_df)} Amsterdam observations")
        
        processed_files += 1
    
    if not all_amsterdam_data:
        print("No Amsterdam observations found in any files!")
        return
    
    # Combine all Amsterdam data
    print(f"\nCombining data from {len(all_amsterdam_data)} files...")
    combined_df = pd.concat(all_amsterdam_data, ignore_index=True)
    
    # Remove duplicates based on observation ID
    original_count = len(combined_df)
    combined_df = combined_df.drop_duplicates(subset=['id'])
    duplicates_removed = original_count - len(combined_df)
    
    print(f"Combined data: {len(combined_df)} unique observations")
    if duplicates_removed > 0:
        print(f"Removed {duplicates_removed} duplicate observations")
    
    # Save combined Amsterdam data
    output_file = "data/amsterdam/amsterdam_observations_all.csv"
    combined_df.to_csv(output_file, index=False)
    print(f"Saved combined Amsterdam data to {output_file}")
    
    # Save data by insect group
    print("\nSaving data by insect group...")
    for group_id, group_name in INSECT_GROUPS.items():
        group_data = combined_df[combined_df['group_name'] == group_name]
        if not group_data.empty:
            group_file = f"data/amsterdam/amsterdam_observations_{group_name.lower()}.csv"
            group_data.to_csv(group_file, index=False)
            print(f"  {group_name}: {len(group_data)} observations -> {group_file}")
    
    # Save data by date
    print("\nSaving data by date...")
    combined_df['date_only'] = pd.to_datetime(combined_df['date']).dt.date
    for date, group in combined_df.groupby('date_only'):
        date_str = date.strftime('%Y-%m-%d')
        date_file = f"data/amsterdam/amsterdam_observations_{date_str}.csv"
        group.to_csv(date_file, index=False)
        print(f"  {date_str}: {len(group)} observations -> {date_file}")
    
    # Create summary statistics
    summary_stats = {
        'total_amsterdam_observations': len(combined_df),
        'total_files_processed': processed_files,
        'date_range': {
            'start': combined_df['date_only'].min(),
            'end': combined_df['date_only'].max()
        },
        'observations_by_group': combined_df['group_name'].value_counts().to_dict(),
        'observations_by_date': combined_df['date_only'].value_counts().sort_index().to_dict()
    }
    
    # Save summary statistics
    summary_file = "data/amsterdam/summary_statistics.txt"
    with open(summary_file, 'w') as f:
        f.write("Amsterdam Insect Observations Summary\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Total observations: {summary_stats['total_amsterdam_observations']}\n")
        f.write(f"Files processed: {summary_stats['total_files_processed']}\n")
        f.write(f"Date range: {summary_stats['date_range']['start']} to {summary_stats['date_range']['end']}\n\n")
        
        f.write("Observations by insect group:\n")
        for group, count in summary_stats['observations_by_group'].items():
            f.write(f"  {group}: {count}\n")
        
        f.write(f"\nObservations by date:\n")
        for date, count in summary_stats['observations_by_date'].items():
            f.write(f"  {date}: {count}\n")
    
    print(f"\nSummary statistics saved to {summary_file}")
    print(f"\nAmsterdam data filtering complete!")
    print(f"Total Amsterdam observations: {len(combined_df)}")
    print(f"Date range: {summary_stats['date_range']['start']} to {summary_stats['date_range']['end']}")

if __name__ == "__main__":
    main()
