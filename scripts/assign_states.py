#!/usr/bin/env python3
"""
Assign states to minute-level route points via spatial join.

This script:
1. Loads minute-level simulation Parquet files
2. Loads administrative boundaries
3. Performs spatial join to assign state/province to each minute
4. Counts minutes per state for each route
5. Aggregates all routes to create global state-time summary
6. Saves per-route and aggregated CSVs
"""

from pathlib import Path
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from tqdm import tqdm


def load_admin_boundaries():
    """
    Load administrative boundaries.

    Returns:
        GeoDataFrame of boundaries, or None if not available
    """
    admin_file = Path('data/admin/admin1_states_provinces.geojson')

    if not admin_file.exists():
        print(f"Warning: Admin boundaries not found at {admin_file}")
        print("Run scripts/load_boundaries.py first.")
        return None

    print(f"Loading boundaries from {admin_file}")
    gdf = gpd.read_file(admin_file)
    print(f"Loaded {len(gdf)} administrative regions")
    return gdf


def assign_states_to_route(parquet_file, boundaries_gdf):
    """
    Assign states to minute-level points for a single route.

    Args:
        parquet_file: Path to route simulation Parquet file
        boundaries_gdf: GeoDataFrame of administrative boundaries

    Returns:
        DataFrame with state assignments and minute counts
    """
    # Load minute-level data
    df = pd.read_parquet(parquet_file)

    # Create GeoDataFrame from points
    geometry = [Point(lon, lat) for lon, lat in zip(df['lon'], df['lat'])]
    gdf_points = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')

    # Ensure boundaries are in same CRS
    if boundaries_gdf.crs != gdf_points.crs:
        boundaries_gdf = boundaries_gdf.to_crs(gdf_points.crs)

    # Spatial join: find which state each point is in
    joined = gpd.sjoin(gdf_points, boundaries_gdf, how='left', predicate='within')

    # Extract state name (try multiple possible columns)
    state_column = None
    for col in ['name', 'name_en', 'postal', 'iso_3166_2']:
        if col in joined.columns:
            state_column = col
            break

    if state_column is None:
        print(f"Warning: No state name column found in boundaries")
        return None

    # Count minutes per state
    state_counts = joined.groupby(state_column).size().reset_index(name='minutes')

    # Add route_id
    route_id = df['route_id'].iloc[0] if 'route_id' in df.columns else parquet_file.stem.replace('_minutes', '')
    state_counts.insert(0, 'route_id', route_id)

    # Rename state column to standardized name
    state_counts.rename(columns={state_column: 'state'}, inplace=True)

    # Handle NaN (points not in any state - could be in water or outside coverage)
    state_counts['state'] = state_counts['state'].fillna('Unknown')

    return state_counts


def main():
    """Main execution function."""
    print("=" * 60)
    print("STEP 4: Assigning States to Route Minutes")
    print("=" * 60)
    print()

    # Load boundaries
    boundaries_gdf = load_admin_boundaries()

    if boundaries_gdf is None:
        print("Cannot proceed without boundaries. Exiting.")
        return

    print()

    # Get all simulation Parquet files
    sims_dir = Path('outputs/sims')
    parquet_files = sorted(sims_dir.glob('*_minutes.parquet'))

    if not parquet_files:
        print(f"Error: No simulation files found in {sims_dir}")
        print("Run scripts/simulate_minutes.py first.")
        return

    print(f"Found {len(parquet_files)} simulation files")
    print()

    # Process each route
    all_results = []

    for parquet_file in tqdm(parquet_files, desc="Processing routes"):
        result = assign_states_to_route(parquet_file, boundaries_gdf)

        if result is not None:
            all_results.append(result)

            # Save per-route summary
            route_id = result['route_id'].iloc[0]
            output_file = Path(f'outputs/tables/{route_id}_minutes_by_state.csv')
            output_file.parent.mkdir(parents=True, exist_ok=True)
            result.to_csv(output_file, index=False)

    if not all_results:
        print("No results to aggregate.")
        return

    # Concatenate all results
    df_all = pd.concat(all_results, ignore_index=True)

    # Aggregate: total minutes per state across all routes
    df_aggregated = df_all.groupby('state')['minutes'].sum().reset_index()
    df_aggregated = df_aggregated.sort_values('minutes', ascending=False)

    # Save aggregated results
    output_file = Path('outputs/tables/all_routes_minutes_by_state.csv')
    df_aggregated.to_csv(output_file, index=False)

    print()
    print("State assignment complete!")
    print(f"Saved per-route summaries to: outputs/tables/")
    print(f"Saved aggregated summary to: {output_file}")
    print()

    # Display top states
    print("Top 10 states by total minutes:")
    print(df_aggregated.head(10).to_string(index=False))
    print()

    # Summary statistics
    print("Summary:")
    print(f"  - Total routes processed: {len(all_results)}")
    print(f"  - Total states/provinces: {len(df_aggregated)}")
    print(f"  - Total minutes across all routes: {df_aggregated['minutes'].sum():,}")
    print()


if __name__ == '__main__':
    main()
