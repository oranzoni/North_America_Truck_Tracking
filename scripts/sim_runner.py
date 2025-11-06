#!/usr/bin/env python3
"""
Simulation Runner - CLI tool for working with minute-level simulation Parquet files.

This script provides easy access to the simulation data stored in outputs/sims/.
Use it to inspect, filter, export, and visualize route simulations.
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from tqdm import tqdm


# ============================================================================
# Helper Functions
# ============================================================================

def get_sims_dir():
    """Get the simulations directory path."""
    return Path('outputs/sims')


def list_routes():
    """
    List all available route IDs from Parquet files.

    Returns:
        List of route IDs (strings)
    """
    sims_dir = get_sims_dir()

    if not sims_dir.exists():
        print(f"Error: Simulation directory not found: {sims_dir}")
        print("Run the simulation scripts first.")
        return []

    parquet_files = sorted(sims_dir.glob('*_minutes.parquet'))

    if not parquet_files:
        print(f"Warning: No simulation files found in {sims_dir}")
        return []

    route_ids = [f.stem.replace('_minutes', '') for f in parquet_files]
    return route_ids


def load_minutes(route_id):
    """
    Load minute-level simulation data for a route.

    Args:
        route_id: Route identifier (e.g., 'Los_Angeles_to_Boston')

    Returns:
        DataFrame with simulation data, or None if not found
    """
    sims_dir = get_sims_dir()
    parquet_file = sims_dir / f'{route_id}_minutes.parquet'

    if not parquet_file.exists():
        print(f"Error: Route '{route_id}' not found.")
        print(f"Expected file: {parquet_file}")
        print(f"\nAvailable routes:")
        for rid in list_routes():
            print(f"  - {rid}")
        return None

    try:
        df = pd.read_parquet(parquet_file, engine='pyarrow')
        return df
    except Exception as e:
        print(f"Error loading {parquet_file}: {e}")
        return None


def export_csv(df, output_path):
    """
    Export DataFrame to CSV.

    Args:
        df: DataFrame to export
        output_path: Path to output CSV file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Exported to CSV: {output_path}")


def export_geojson(df, output_path):
    """
    Export DataFrame to GeoJSON with Point geometries.

    Args:
        df: DataFrame with lon/lat columns
        output_path: Path to output GeoJSON file
    """
    try:
        import geopandas as gpd
        from shapely.geometry import Point
    except ImportError:
        print("Error: geopandas and shapely required for GeoJSON export")
        print("Install with: pip install geopandas shapely")
        return

    # Create Point geometries from lon/lat
    geometry = [Point(lon, lat) for lon, lat in zip(df['lon'], df['lat'])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(output_path, driver='GeoJSON')
    print(f"Exported to GeoJSON: {output_path}")


def export_parquet(df, output_path, columns=None):
    """
    Export DataFrame to Parquet.

    Args:
        df: DataFrame to export
        output_path: Path to output Parquet file
        columns: Optional list of columns to include
    """
    if columns:
        df = df[columns]

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, engine='pyarrow', index=False)
    print(f"Exported to Parquet: {output_path}")


def export_gpx(df, output_path, route_id):
    """
    Export DataFrame to GPX track format.

    Args:
        df: DataFrame with lon/lat columns
        output_path: Path to output GPX file
        route_id: Route identifier for track name
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create GPX XML
    gpx_header = '''<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Truck Route Simulator"
     xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">
'''

    gpx_track_start = f'  <trk>\n    <name>{route_id}</name>\n    <trkseg>\n'

    track_points = []
    for _, row in df.iterrows():
        lat = row['lat']
        lon = row['lon']
        track_points.append(f'      <trkpt lat="{lat}" lon="{lon}"></trkpt>')

    gpx_track_end = '    </trkseg>\n  </trk>\n'
    gpx_footer = '</gpx>'

    gpx_content = gpx_header + gpx_track_start + '\n'.join(track_points) + '\n' + gpx_track_end + gpx_footer

    with open(output_path, 'w') as f:
        f.write(gpx_content)

    print(f"Exported to GPX: {output_path}")


# ============================================================================
# Command Functions
# ============================================================================

def cmd_list(args):
    """List all available route IDs."""
    print("=" * 60)
    print("Available Route Simulations")
    print("=" * 60)

    route_ids = list_routes()

    if not route_ids:
        print("No routes found.")
        return

    print(f"\nFound {len(route_ids)} route(s):\n")
    for i, route_id in enumerate(route_ids, 1):
        # Get file size
        sims_dir = get_sims_dir()
        parquet_file = sims_dir / f'{route_id}_minutes.parquet'
        size_bytes = parquet_file.stat().st_size

        if size_bytes < 1024:
            size_str = f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"

        print(f"  {i:2d}. {route_id:40s} ({size_str})")
    print()


def cmd_head(args):
    """Preview first N rows of a route simulation."""
    df = load_minutes(args.route)

    if df is None:
        sys.exit(1)

    n = args.n
    print("=" * 60)
    print(f"Preview: {args.route} (first {n} rows)")
    print("=" * 60)
    print()
    print(df.head(n).to_string(index=False))
    print()
    print(f"Total rows: {len(df)}")
    print()


def cmd_summary(args):
    """Print summary statistics for a route."""
    df = load_minutes(args.route)

    if df is None:
        sys.exit(1)

    print("=" * 60)
    print(f"Summary: {args.route}")
    print("=" * 60)
    print()

    # Duration
    if 'minute' in df.columns:
        duration_min = df['minute'].max()
    else:
        duration_min = len(df) - 1

    duration_hours = duration_min / 60.0

    print(f"Duration:")
    print(f"  - Total minutes: {duration_min}")
    print(f"  - Total hours: {duration_hours:.2f}")
    print()

    # Distance
    if 'distance_km' in df.columns:
        total_distance = df['distance_km'].max()
        print(f"Distance:")
        print(f"  - Total: {total_distance:.2f} km")
        print()

    # Speed statistics
    if 'speed_kmh' in df.columns:
        speeds = df[df['speed_kmh'] > 0]['speed_kmh']  # Exclude zeros

        if len(speeds) > 0:
            print(f"Speed (km/h):")
            print(f"  - Min: {speeds.min():.2f}")
            print(f"  - Median: {speeds.median():.2f}")
            print(f"  - Mean: {speeds.mean():.2f}")
            print(f"  - 95th percentile: {speeds.quantile(0.95):.2f}")
            print(f"  - Max: {speeds.max():.2f}")
            print()

    # Geographic bounds
    if 'lon' in df.columns and 'lat' in df.columns:
        print(f"Geographic Bounds:")
        print(f"  - Longitude: [{df['lon'].min():.4f}, {df['lon'].max():.4f}]")
        print(f"  - Latitude: [{df['lat'].min():.4f}, {df['lat'].max():.4f}]")
        print()

    # Data info
    print(f"Data Info:")
    print(f"  - Total rows: {len(df):,}")
    print(f"  - Columns: {', '.join(df.columns)}")
    print()


def cmd_export(args):
    """Export route simulation to various formats."""
    df = load_minutes(args.route)

    if df is None:
        sys.exit(1)

    print(f"Exporting {args.route} to {args.to.upper()}...")

    if args.to == 'csv':
        export_csv(df, args.out)
    elif args.to == 'geojson':
        export_geojson(df, args.out)
    elif args.to == 'parquet':
        export_parquet(df, args.out)
    else:
        print(f"Error: Unsupported format '{args.to}'")
        print("Supported formats: csv, geojson, parquet")
        sys.exit(1)


def cmd_merge(args):
    """Merge all route simulations into a single file."""
    print("=" * 60)
    print("Merging All Route Simulations")
    print("=" * 60)
    print()

    route_ids = list_routes()

    if not route_ids:
        print("Error: No routes found to merge.")
        sys.exit(1)

    print(f"Found {len(route_ids)} routes to merge")
    print()

    # Load all routes
    all_dfs = []
    for route_id in tqdm(route_ids, desc="Loading routes"):
        df = load_minutes(route_id)
        if df is not None:
            # Ensure route_id column exists
            if 'route_id' not in df.columns:
                df.insert(0, 'route_id', route_id)
            all_dfs.append(df)

    if not all_dfs:
        print("Error: No data loaded.")
        sys.exit(1)

    # Concatenate
    print("\nConcatenating DataFrames...")
    merged_df = pd.concat(all_dfs, ignore_index=True)

    print(f"Merged {len(merged_df):,} rows")
    print()

    # Save
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_parquet(output_path, engine='pyarrow', index=False)

    size_bytes = output_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)

    print(f"Saved merged file: {output_path}")
    print(f"File size: {size_mb:.2f} MB")
    print()


def cmd_plot(args):
    """Create a static plot of the route path."""
    df = load_minutes(args.route)

    if df is None:
        sys.exit(1)

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Error: matplotlib required for plotting")
        print("Install with: pip install matplotlib")
        sys.exit(1)

    print(f"Plotting {args.route}...")

    fig, ax = plt.subplots(figsize=(12, 8))

    # Plot path
    if args.speed and 'speed_kmh' in df.columns:
        # Color by speed
        speeds = df['speed_kmh']
        scatter = ax.scatter(df['lon'], df['lat'], c=speeds, cmap='viridis',
                           s=10, alpha=0.6, edgecolors='none')
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Speed (km/h)', rotation=270, labelpad=20)
        title_suffix = " (colored by speed)"
    else:
        # Simple path
        ax.plot(df['lon'], df['lat'], 'b-', linewidth=1.5, alpha=0.7)
        ax.scatter(df['lon'].iloc[0], df['lat'].iloc[0],
                  c='green', s=100, marker='o', label='Start', zorder=5)
        ax.scatter(df['lon'].iloc[-1], df['lat'].iloc[-1],
                  c='red', s=100, marker='s', label='End', zorder=5)
        ax.legend()
        title_suffix = ""

    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title(f'Route Path: {args.route}{title_suffix}')
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal', adjustable='box')

    # Save
    output_path = Path(args.map)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Plot saved: {output_path}")
    print()


def cmd_to_gpx(args):
    """Export route to GPX track format."""
    df = load_minutes(args.route)

    if df is None:
        sys.exit(1)

    print(f"Exporting {args.route} to GPX...")
    export_gpx(df, args.out, args.route)
    print()


# ============================================================================
# Main CLI
# ============================================================================

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Simulation Runner - Work with minute-level route simulations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all routes
  python scripts/sim_runner.py list

  # Preview first 10 rows
  python scripts/sim_runner.py head --route Los_Angeles_to_Boston --n 10

  # Show summary statistics
  python scripts/sim_runner.py summary --route Miami_to_San_Francisco

  # Export to GeoJSON
  python scripts/sim_runner.py export --route Phoenix_to_Seattle \\
      --to geojson --out outputs/exports/Phoenix_to_Seattle.geojson

  # Merge all routes
  python scripts/sim_runner.py merge --out outputs/exports/all_minutes.parquet

  # Plot route path
  python scripts/sim_runner.py plot --route Los_Angeles_to_Boston \\
      --map outputs/figures/Los_Angeles_to_Boston_path.png --speed
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # list command
    parser_list = subparsers.add_parser('list', help='List all available route IDs')

    # head command
    parser_head = subparsers.add_parser('head', help='Preview first N rows of a route')
    parser_head.add_argument('--route', required=True, help='Route ID')
    parser_head.add_argument('--n', type=int, default=10, help='Number of rows (default: 10)')

    # summary command
    parser_summary = subparsers.add_parser('summary', help='Show summary statistics for a route')
    parser_summary.add_argument('--route', required=True, help='Route ID')

    # export command
    parser_export = subparsers.add_parser('export', help='Export route to different format')
    parser_export.add_argument('--route', required=True, help='Route ID')
    parser_export.add_argument('--to', required=True,
                              choices=['csv', 'geojson', 'parquet'],
                              help='Output format')
    parser_export.add_argument('--out', required=True, help='Output file path')

    # merge command
    parser_merge = subparsers.add_parser('merge', help='Merge all routes into single file')
    parser_merge.add_argument('--out', required=True, help='Output Parquet file path')

    # plot command
    parser_plot = subparsers.add_parser('plot', help='Create static plot of route path')
    parser_plot.add_argument('--route', required=True, help='Route ID')
    parser_plot.add_argument('--map', required=True, help='Output PNG file path')
    parser_plot.add_argument('--speed', action='store_true',
                            help='Color path by speed')

    # to-gpx command
    parser_gpx = subparsers.add_parser('to-gpx', help='Export route to GPX track format')
    parser_gpx.add_argument('--route', required=True, help='Route ID')
    parser_gpx.add_argument('--out', required=True, help='Output GPX file path')

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Route to appropriate command
    if args.command == 'list':
        cmd_list(args)
    elif args.command == 'head':
        cmd_head(args)
    elif args.command == 'summary':
        cmd_summary(args)
    elif args.command == 'export':
        cmd_export(args)
    elif args.command == 'merge':
        cmd_merge(args)
    elif args.command == 'plot':
        cmd_plot(args)
    elif args.command == 'to-gpx':
        cmd_to_gpx(args)


if __name__ == '__main__':
    main()
