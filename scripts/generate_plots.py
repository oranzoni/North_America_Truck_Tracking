#!/usr/bin/env python3
"""

This script creates:
1. hist_distances.png - Histogram of route distances
2. hist_durations.png - Histogram of route durations
3. scatter_distance_vs_duration.png - Scatter plot of distance vs duration
4. hist_minutes_per_state.png - Histogram of minutes per state
5. hist_avg_speed_per_minute.png - Histogram of average speeds
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm


def setup_plot_style():
    """Configure matplotlib style for consistent plots."""
    plt.style.use('default')
    plt.rcParams['figure.dpi'] = 150
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.labelsize'] = 11
    plt.rcParams['axes.titlesize'] = 12
    plt.rcParams['xtick.labelsize'] = 9
    plt.rcParams['ytick.labelsize'] = 9


def plot_distance_histogram(df_summary, output_dir):
    """Create histogram of route distances."""
    fig, ax = plt.subplots(figsize=(10, 6))

    # Use Freedman-Diaconis rule for bin width
    q75, q25 = np.percentile(df_summary['distance_km'], [75, 25])
    iqr = q75 - q25
    bin_width = 2 * iqr * len(df_summary) ** (-1/3)
    bins = int(np.ceil((df_summary['distance_km'].max() - df_summary['distance_km'].min()) / bin_width))
    bins = max(10, min(bins, 30))  # Limit bins between 10 and 30

    ax.hist(df_summary['distance_km'], bins=bins, color='steelblue', edgecolor='black', alpha=0.7)

    ax.set_xlabel('Distance (km)')
    ax.set_ylabel('Number of Routes')
    ax.set_title('Distribution of Route Distances')
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Add statistics text box
    stats_text = f"Total Routes: {len(df_summary)}\n"
    stats_text += f"Mean: {df_summary['distance_km'].mean():.1f} km\n"
    stats_text += f"Median: {df_summary['distance_km'].median():.1f} km\n"
    stats_text += f"Std Dev: {df_summary['distance_km'].std():.1f} km"

    ax.text(0.98, 0.97, stats_text, transform=ax.transAxes,
            verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
            fontsize=9)

    plt.tight_layout()
    output_file = output_dir / 'hist_distances.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_file}")


def plot_duration_histogram(df_summary, output_dir):
    """Create histogram of route durations."""
    fig, ax = plt.subplots(figsize=(10, 6))

    # Convert to hours for better readability
    durations_hours = df_summary['duration_min'] / 60.0

    # Use Freedman-Diaconis rule
    q75, q25 = np.percentile(durations_hours, [75, 25])
    iqr = q75 - q25
    bin_width = 2 * iqr * len(durations_hours) ** (-1/3)
    bins = int(np.ceil((durations_hours.max() - durations_hours.min()) / bin_width))
    bins = max(10, min(bins, 30))

    ax.hist(durations_hours, bins=bins, color='coral', edgecolor='black', alpha=0.7)

    ax.set_xlabel('Duration (hours)')
    ax.set_ylabel('Number of Routes')
    ax.set_title('Distribution of Route Durations')
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Add statistics text box
    stats_text = f"Total Routes: {len(df_summary)}\n"
    stats_text += f"Mean: {durations_hours.mean():.1f} hours\n"
    stats_text += f"Median: {durations_hours.median():.1f} hours\n"
    stats_text += f"Std Dev: {durations_hours.std():.1f} hours"

    ax.text(0.98, 0.97, stats_text, transform=ax.transAxes,
            verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
            fontsize=9)

    plt.tight_layout()
    output_file = output_dir / 'hist_durations.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_file}")


def plot_distance_vs_duration_scatter(df_summary, output_dir):
    """Create scatter plot of distance vs duration."""
    fig, ax = plt.subplots(figsize=(10, 7))

    # Convert duration to hours
    durations_hours = df_summary['duration_min'] / 60.0

    ax.scatter(df_summary['distance_km'], durations_hours,
               s=80, alpha=0.6, color='forestgreen', edgecolors='black', linewidth=0.5)

    # Add reference line for 75 km/h
    max_dist = df_summary['distance_km'].max()
    ref_dist = np.linspace(0, max_dist, 100)
    ref_duration = ref_dist / 75.0
    ax.plot(ref_dist, ref_duration, 'r--', linewidth=2, alpha=0.7, label='75 km/h reference')

    ax.set_xlabel('Distance (km)')
    ax.set_ylabel('Duration (hours)')
    ax.set_title('Route Distance vs Duration')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='upper left')

    # Add correlation coefficient
    corr = df_summary['distance_km'].corr(df_summary['duration_min'])
    ax.text(0.98, 0.02, f'Correlation: {corr:.3f}', transform=ax.transAxes,
            verticalalignment='bottom', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
            fontsize=9)

    plt.tight_layout()
    output_file = output_dir / 'scatter_distance_vs_duration.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_file}")


def plot_minutes_per_state_histogram(output_dir):
    """Create histogram of minutes per state."""
    state_file = Path('outputs/tables/all_routes_minutes_by_state.csv')

    if not state_file.exists():
        print(f"Warning: State data not found at {state_file}")
        print("Skipping state histogram.")
        return

    df_states = pd.read_csv(state_file)

    # Remove 'Unknown' if present
    df_states = df_states[df_states['state'] != 'Unknown']

    if len(df_states) == 0:
        print("Warning: No state data available after filtering.")
        return

    fig, ax = plt.subplots(figsize=(12, 7))

    # Sort by minutes and take top 20 if there are many states
    df_states_sorted = df_states.sort_values('minutes', ascending=False)
    if len(df_states_sorted) > 20:
        df_states_sorted = df_states_sorted.head(20)
        title_suffix = ' (Top 20)'
    else:
        title_suffix = ''

    # Create horizontal bar chart for better label readability
    bars = ax.barh(range(len(df_states_sorted)), df_states_sorted['minutes'],
                   color='mediumpurple', edgecolor='black', alpha=0.7)

    ax.set_yticks(range(len(df_states_sorted)))
    ax.set_yticklabels(df_states_sorted['state'])
    ax.set_xlabel('Total Minutes')
    ax.set_ylabel('State/Province')
    ax.set_title(f'Total Travel Time by State{title_suffix}')
    ax.grid(axis='x', alpha=0.3, linestyle='--')

    # Invert y-axis so highest is on top
    ax.invert_yaxis()

    # Add value labels on bars
    for i, (idx, row) in enumerate(df_states_sorted.iterrows()):
        ax.text(row['minutes'] + max(df_states_sorted['minutes']) * 0.01,
                i, f"{int(row['minutes'])}", va='center', fontsize=8)

    plt.tight_layout()
    output_file = output_dir / 'hist_minutes_per_state.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_file}")


def plot_speed_histogram(output_dir):
    """Create histogram of average speeds per minute across all routes."""
    sims_dir = Path('outputs/sims')
    parquet_files = list(sims_dir.glob('*_minutes.parquet'))

    if not parquet_files:
        print(f"Warning: No simulation files found in {sims_dir}")
        print("Skipping speed histogram.")
        return

    # Collect all speeds
    all_speeds = []

    for parquet_file in tqdm(parquet_files, desc="Loading simulation data"):
        df = pd.read_parquet(parquet_file)
        # Filter out zero speeds (start/end points)
        speeds = df[df['speed_kmh'] > 0]['speed_kmh'].values
        all_speeds.extend(speeds)

    all_speeds = np.array(all_speeds)

    if len(all_speeds) == 0:
        print("Warning: No speed data available.")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    # Use Freedman-Diaconis rule
    q75, q25 = np.percentile(all_speeds, [75, 25])
    iqr = q75 - q25
    bin_width = 2 * iqr * len(all_speeds) ** (-1/3)
    bins = int(np.ceil((all_speeds.max() - all_speeds.min()) / bin_width))
    bins = max(20, min(bins, 50))

    ax.hist(all_speeds, bins=bins, color='darkorange', edgecolor='black', alpha=0.7)

    ax.set_xlabel('Speed (km/h)')
    ax.set_ylabel('Frequency (minute intervals)')
    ax.set_title('Distribution of Travel Speeds (per minute)')
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Add statistics text box
    stats_text = f"Total Minutes: {len(all_speeds):,}\n"
    stats_text += f"Mean: {all_speeds.mean():.1f} km/h\n"
    stats_text += f"Median: {np.median(all_speeds):.1f} km/h\n"
    stats_text += f"Std Dev: {all_speeds.std():.1f} km/h"

    ax.text(0.98, 0.97, stats_text, transform=ax.transAxes,
            verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
            fontsize=9)

    # Add reference line at 75 km/h
    ax.axvline(x=75, color='red', linestyle='--', linewidth=2, alpha=0.7, label='75 km/h reference')
    ax.legend()

    plt.tight_layout()
    output_file = output_dir / 'hist_avg_speed_per_minute.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_file}")


def main():
    """Main execution function."""
    print("=" * 60)
    print("STEP 5: Generating Visualizations")
    print("=" * 60)
    print()

    setup_plot_style()

    # Output directory
    output_dir = Path('outputs/figures')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load route summary
    summary_file = Path('outputs/routes_summary.csv')
    if not summary_file.exists():
        print(f"Error: Route summary not found at {summary_file}")
        print("Run scripts/compute_distance_duration.py first.")
        return

    df_summary = pd.read_csv(summary_file)
    print(f"Loaded summary data for {len(df_summary)} routes")
    print()

    # Generate plots
    print("Generating plots...")
    print()

    plot_distance_histogram(df_summary, output_dir)
    plot_duration_histogram(df_summary, output_dir)
    plot_distance_vs_duration_scatter(df_summary, output_dir)
    plot_minutes_per_state_histogram(output_dir)
    plot_speed_histogram(output_dir)

    print()
    print("All visualizations generated successfully!")
    print(f"Saved to: {output_dir}")
    print()


if __name__ == '__main__':
    main()
