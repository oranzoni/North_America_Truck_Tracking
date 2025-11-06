#!/usr/bin/env python3
"""
Compute distance and duration for each route.

This script:
1. Loads each route JSON file from data/ors_routes/
2. Computes geodesic distance in kilometers
3. Estimates duration in minutes (distance / 75 km/h default speed)
4. Saves summary to outputs/routes_summary.csv
"""

import json
import os
from pathlib import Path
import pandas as pd
from pyproj import Geod
from tqdm import tqdm


def compute_route_distance(coordinates):
    """
    Compute geodesic distance along a route using WGS84 ellipsoid.

    Args:
        coordinates: List of [lon, lat] pairs

    Returns:
        Distance in kilometers
    """
    geod = Geod(ellps='WGS84')

    total_distance = 0.0

    for i in range(len(coordinates) - 1):
        lon1, lat1 = coordinates[i]
        lon2, lat2 = coordinates[i + 1]

        # Compute distance between consecutive points
        _, _, distance = geod.inv(lon1, lat1, lon2, lat2)
        total_distance += distance

    # Convert meters to kilometers
    return total_distance / 1000.0


def process_route_file(file_path):
    """
    Process a single route JSON file.

    Args:
        file_path: Path to route JSON file

    Returns:
        Dictionary with route_id, distance_km, duration_min
    """
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Extract route ID from filename
    route_id = Path(file_path).stem

    # Get geometry coordinates
    features = data.get('features', [])
    if not features:
        print(f"Warning: No features in {route_id}")
        return None

    geometry = features[0].get('geometry', {})
    coordinates = geometry.get('coordinates', [])

    if not coordinates:
        print(f"Warning: No coordinates in {route_id}")
        return None

    # Compute distance
    distance_km = compute_route_distance(coordinates)

    # Extract existing duration from properties if available, otherwise estimate
    properties = features[0].get('properties', {})
    summary = properties.get('summary', {})

    # Duration from API is in seconds, convert to minutes
    if 'duration' in summary:
        duration_min = summary['duration'] / 60.0
    else:
        # Estimate: assume 75 km/h average speed
        duration_min = (distance_km / 75.0) * 60.0

    return {
        'route_id': route_id,
        'distance_km': round(distance_km, 3),
        'duration_min': round(duration_min, 2),
        'avg_speed_kmh': round(distance_km / (duration_min / 60.0), 2) if duration_min > 0 else 0
    }


def main():
    """Main execution function."""
    print("=" * 60)
    print("STEP 1: Computing Route Distances and Durations")
    print("=" * 60)

    # Define paths
    routes_dir = Path('data/ors_routes')
    output_file = Path('outputs/routes_summary.csv')

    # Get all JSON files
    route_files = sorted(routes_dir.glob('*.json'))

    if not route_files:
        print(f"Error: No route files found in {routes_dir}")
        return

    print(f"Found {len(route_files)} route files")
    print()

    # Process each route
    results = []
    for route_file in tqdm(route_files, desc="Processing routes"):
        result = process_route_file(route_file)
        if result:
            results.append(result)

    # Create DataFrame and save
    df = pd.DataFrame(results)
    df = df.sort_values('distance_km', ascending=False)

    # Save to CSV
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)

    print()
    print("Summary Statistics:")
    print("-" * 60)
    print(f"Total routes: {len(df)}")
    print(f"Total distance: {df['distance_km'].sum():.2f} km")
    print(f"Average distance: {df['distance_km'].mean():.2f} km")
    print(f"Min distance: {df['distance_km'].min():.2f} km")
    print(f"Max distance: {df['distance_km'].max():.2f} km")
    print(f"Average duration: {df['duration_min'].mean():.2f} minutes ({df['duration_min'].mean()/60:.2f} hours)")
    print()
    print(f"Results saved to: {output_file}")
    print()

    # Display top routes
    print("Top 5 longest routes:")
    print(df.head().to_string(index=False))
    print()


if __name__ == '__main__':
    main()
