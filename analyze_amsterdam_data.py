#!/usr/bin/env python3
"""
Script to analyze and visualize insect observation data from Amsterdam.
Creates histograms, statistics, and other useful visualizations.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import glob
from datetime import datetime
import argparse

# Set style for better-looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Insect group names and colors for consistency
INSECT_GROUPS = {
    4: ('Butterflies', 'red'),
    8: ('Moths', 'blue'),
    5: ('Dragonflies', 'darkblue'),
    14: ('Locusts and Crickets', 'purple'),
    17: ('Bees, Wasps and Ants', 'orange'),
    18: ('Flies', 'darkred'),
    16: ('Beetles', 'lightcoral'),
    15: ('Bugs, Plant Lice and Cicadas', 'pink'),
    6: ('Other Insects', 'gray')
}

def load_amsterdam_data():
    """
    Load all Amsterdam observation data from CSV files.
    Returns combined DataFrame with all observations.
    """
    print("Loading Amsterdam observation data...")
    
    all_dfs = []
    amsterdam_files = glob.glob("data/amsterdam/amsterdam_observations_*.csv")
    
    if not amsterdam_files:
        print("No Amsterdam data files found!")
        return pd.DataFrame()
    
    print(f"Found {len(amsterdam_files)} Amsterdam data files")
    
    for filepath in amsterdam_files:
        try:
            df = pd.read_csv(filepath)
            if not df.empty:
                all_dfs.append(df)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
    
    if not all_dfs:
        print("No data loaded!")
        return pd.DataFrame()
    
    # Combine all data
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # Remove duplicates
    original_count = len(combined_df)
    combined_df = combined_df.drop_duplicates(subset=['id'])
    duplicates_removed = original_count - len(combined_df)
    
    print(f"Loaded {len(combined_df)} unique observations")
    if duplicates_removed > 0:
        print(f"Removed {duplicates_removed} duplicate observations")
    
    return combined_df

def create_group_histogram(df, output_dir):
    """
    Create histogram showing number of observations per insect group.
    """
    print("Creating group histogram...")
    
    # Count observations by group
    group_counts = df['group_name'].value_counts()
    
    # Create figure
    plt.figure(figsize=(12, 8))
    bars = plt.bar(range(len(group_counts)), group_counts.values, 
                   color=[INSECT_GROUPS.get(i, ('Unknown', 'gray'))[1] 
                          for i in range(len(group_counts))])
    
    # Customize plot
    plt.title('Number of Observations by Insect Group (Amsterdam)', fontsize=16, fontweight='bold')
    plt.xlabel('Insect Group', fontsize=12)
    plt.ylabel('Number of Observations', fontsize=12)
    plt.xticks(range(len(group_counts)), group_counts.index, rotation=45, ha='right')
    
    # Add value labels on bars
    for i, bar in enumerate(bars):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{int(height)}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/group_histogram.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return group_counts

def create_species_analysis(df, output_dir, top_n=20):
    """
    Create analysis of most observed species.
    """
    print("Creating species analysis...")
    
    # Count observations by species
    species_counts = df['common_name'].value_counts().head(top_n)
    
    # Create figure
    plt.figure(figsize=(14, 8))
    bars = plt.barh(range(len(species_counts)), species_counts.values)
    
    # Color bars by group
    colors = []
    for species in species_counts.index:
        # Find which group this species belongs to
        species_data = df[df['common_name'] == species]
        if not species_data.empty:
            group_name = species_data['group_name'].iloc[0]
            # Find color for this group
            color = 'gray'
            for gid, (gname, gcolor) in INSECT_GROUPS.items():
                if gname == group_name:
                    color = gcolor
                    break
            colors.append(color)
        else:
            colors.append('gray')
    
    # Apply colors
    for i, bar in enumerate(bars):
        bar.set_color(colors[i])
    
    # Customize plot
    plt.title(f'Top {top_n} Most Observed Species (Amsterdam)', fontsize=16, fontweight='bold')
    plt.xlabel('Number of Observations', fontsize=12)
    plt.ylabel('Species', fontsize=12)
    plt.yticks(range(len(species_counts)), species_counts.index)
    
    # Add value labels
    for i, bar in enumerate(bars):
        width = bar.get_width()
        plt.text(width + width*0.01, bar.get_y() + bar.get_height()/2,
                f'{int(width)}', ha='left', va='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/top_species.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return species_counts

def create_temporal_analysis(df, output_dir):
    """
    Create temporal analysis showing observations over time.
    """
    print("Creating temporal analysis...")
    
    # Convert date column
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.month
    df['day_of_year'] = df['date'].dt.dayofyear
    
    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Monthly distribution
    monthly_counts = df['month'].value_counts().sort_index()
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    ax1.bar(monthly_counts.index, monthly_counts.values, color='skyblue', alpha=0.7)
    ax1.set_title('Observations by Month', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Month', fontsize=12)
    ax1.set_ylabel('Number of Observations', fontsize=12)
    ax1.set_xticks(range(1, 13))
    ax1.set_xticklabels(months)
    
    # Add value labels
    for i, v in enumerate(monthly_counts.values):
        ax1.text(monthly_counts.index[i], v + v*0.01, str(v), 
                ha='center', va='bottom', fontweight='bold')
    
    # Daily distribution (day of year)
    daily_counts = df['day_of_year'].value_counts().sort_index()
    ax2.plot(daily_counts.index, daily_counts.values, marker='o', linewidth=2, markersize=4)
    ax2.set_title('Observations by Day of Year', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Day of Year', fontsize=12)
    ax2.set_ylabel('Number of Observations', fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/temporal_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return monthly_counts, daily_counts

def create_group_comparison(df, output_dir):
    """
    Create detailed comparison between insect groups.
    """
    print("Creating group comparison...")
    
    # Calculate statistics for each group
    group_stats = []
    for group_name in df['group_name'].unique():
        group_data = df[df['group_name'] == group_name]
        
        stats = {
            'Group': group_name,
            'Total Observations': len(group_data),
            'Unique Species': group_data['common_name'].nunique(),
            'Unique Locations': group_data['location'].nunique(),
            'Unique Observers': group_data['observer'].nunique(),
            'Avg Observations per Species': len(group_data) / group_data['common_name'].nunique()
        }
        group_stats.append(stats)
    
    stats_df = pd.DataFrame(group_stats).sort_values('Total Observations', ascending=False)
    
    # Create comparison plot
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # Total observations
    bars1 = ax1.bar(range(len(stats_df)), stats_df['Total Observations'], 
                    color=[INSECT_GROUPS.get(i, ('Unknown', 'gray'))[1] 
                           for i in range(len(stats_df))])
    ax1.set_title('Total Observations by Group', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Insect Group', fontsize=12)
    ax1.set_ylabel('Number of Observations', fontsize=12)
    ax1.set_xticks(range(len(stats_df)))
    ax1.set_xticklabels(stats_df['Group'], rotation=45, ha='right')
    
    # Unique species
    bars2 = ax2.bar(range(len(stats_df)), stats_df['Unique Species'], 
                    color=[INSECT_GROUPS.get(i, ('Unknown', 'gray'))[1] 
                           for i in range(len(stats_df))])
    ax2.set_title('Unique Species by Group', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Insect Group', fontsize=12)
    ax2.set_ylabel('Number of Species', fontsize=12)
    ax2.set_xticks(range(len(stats_df)))
    ax2.set_xticklabels(stats_df['Group'], rotation=45, ha='right')
    
    # Observations vs Species scatter plot
    ax3.scatter(stats_df['Unique Species'], stats_df['Total Observations'], 
                s=100, alpha=0.7, c=[INSECT_GROUPS.get(i, ('Unknown', 'gray'))[1] 
                                     for i in range(len(stats_df))])
    ax3.set_title('Observations vs Species Diversity', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Number of Species', fontsize=12)
    ax3.set_ylabel('Number of Observations', fontsize=12)
    
    # Add group labels to scatter plot
    for i, group in enumerate(stats_df['Group']):
        ax3.annotate(group, (stats_df['Unique Species'].iloc[i], 
                            stats_df['Total Observations'].iloc[i]),
                    xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    # Average observations per species
    bars4 = ax4.bar(range(len(stats_df)), stats_df['Avg Observations per Species'], 
                    color=[INSECT_GROUPS.get(i, ('Unknown', 'gray'))[1] 
                           for i in range(len(stats_df))])
    ax4.set_title('Average Observations per Species', fontsize=14, fontweight='bold')
    ax4.set_xlabel('Insect Group', fontsize=12)
    ax4.set_ylabel('Avg Observations per Species', fontsize=12)
    ax4.set_xticks(range(len(stats_df)))
    ax4.set_xticklabels(stats_df['Group'], rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/group_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return stats_df

def create_summary_statistics(df, output_dir):
    """
    Create and save summary statistics.
    """
    print("Creating summary statistics...")
    
    # Calculate overall statistics
    total_observations = len(df)
    total_species = df['common_name'].nunique()
    total_locations = df['location'].nunique()
    total_observers = df['observer'].nunique()
    date_range = f"{df['date'].min()} to {df['date'].max()}"
    
    # Group statistics
    group_stats = df['group_name'].value_counts()
    
    # Most observed species
    top_species = df['common_name'].value_counts().head(10)
    
    # Create summary report
    summary_text = f"""
AMSTERDAM INSECT OBSERVATION ANALYSIS
=====================================

OVERALL STATISTICS
------------------
Total Observations: {total_observations:,}
Total Species: {total_species:,}
Total Locations: {total_locations:,}
Total Observers: {total_observers:,}
Date Range: {date_range}

OBSERVATIONS BY INSECT GROUP
----------------------------
"""
    
    for group, count in group_stats.items():
        percentage = (count / total_observations) * 100
        summary_text += f"{group}: {count:,} observations ({percentage:.1f}%)\n"
    
    summary_text += f"""

TOP 10 MOST OBSERVED SPECIES
----------------------------
"""
    
    for species, count in top_species.items():
        summary_text += f"{species}: {count} observations\n"
    
    # Save summary to file
    with open(f'{output_dir}/summary_statistics.txt', 'w') as f:
        f.write(summary_text)
    
    print("Summary statistics saved to summary_statistics.txt")
    
    return {
        'total_observations': total_observations,
        'total_species': total_species,
        'total_locations': total_locations,
        'total_observers': total_observers,
        'date_range': date_range,
        'group_stats': group_stats,
        'top_species': top_species
    }

def main():
    parser = argparse.ArgumentParser(description='Analyze Amsterdam insect observation data')
    parser.add_argument('--output-dir', default='analysis_output', 
                       help='Output directory for analysis results (default: analysis_output)')
    parser.add_argument('--top-species', type=int, default=20,
                       help='Number of top species to show (default: 20)')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("Starting Amsterdam insect data analysis...")
    print(f"Output directory: {args.output_dir}")
    
    # Load data
    df = load_amsterdam_data()
    
    if df.empty:
        print("No data to analyze!")
        return
    
    # Create analyses
    print("\n" + "="*50)
    print("CREATING VISUALIZATIONS")
    print("="*50)
    
    # Group histogram
    group_counts = create_group_histogram(df, args.output_dir)
    
    # Species analysis
    species_counts = create_species_analysis(df, args.output_dir, args.top_species)
    
    # Temporal analysis
    monthly_counts, daily_counts = create_temporal_analysis(df, args.output_dir)
    
    # Group comparison
    group_stats_df = create_group_comparison(df, args.output_dir)
    
    # Summary statistics
    summary_stats = create_summary_statistics(df, args.output_dir)
    
    print("\n" + "="*50)
    print("ANALYSIS COMPLETE")
    print("="*50)
    print(f"Results saved to: {args.output_dir}/")
    print("\nGenerated files:")
    print("- group_histogram.png")
    print("- top_species.png") 
    print("- temporal_analysis.png")
    print("- group_comparison.png")
    print("- summary_statistics.txt")
    
    # Print key findings
    print(f"\nKEY FINDINGS:")
    print(f"- Total observations: {summary_stats['total_observations']:,}")
    print(f"- Total species: {summary_stats['total_species']:,}")
    print(f"- Most observed group: {group_counts.index[0]} ({group_counts.iloc[0]:,} observations)")
    print(f"- Most observed species: {species_counts.index[0]} ({species_counts.iloc[0]} observations)")

if __name__ == "__main__":
    main()
