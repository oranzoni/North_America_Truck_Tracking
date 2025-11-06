#!/usr/bin/env python3
"""
Simulate minute-by-minute truck positions along routes.

This script:
1. Loads each route JSON file
2. Computes cumulative distance along the route
3. Interpolates truck positions at 1-minute intervals
4. Computes instantaneous speed for each minute
5. Saves minute-level data as Parquet files in outputs/sims/

"""

import json
import os
from pathlib import Path
import pandas as pd
import numpy as np
from pyproj import Geod
from shapely.geometry import LineString, Point
from tqdm import tqdm


def compute_cumulative_distances(coordinates):
    """
    Compute cumulative distance along route.

    Args:
        coordinates: List of [lon, lat] pairs

    Returns:
        numpy array of cumulative distances in kilometers
    """
    geod = Geod(ellps='WGS84')

    distances = [0.0]  # Start at 0
    cumulative = 0.0

    for i in range(len(coordinates) - 1):
        lon1, lat1 = coordinates[i]
        lon2, lat2 = coordinates[i + 1]

        # Compute distance between consecutive points
        _, _, distance = geod.inv(lon1, lat1, lon2, lat2)
        cumulative += distance / 1000.0  # Convert to km
        distances.append(cumulative)

    return np.array(distances)


def interpolate_position(coordinates, cumulative_distances, target_distance):
    """
    Interpolate position at a specific distance along the route.

    Args:
        coordinates: List of [lon, lat] pairs
        cumulative_distances: Array of cumulative distances
        target_distance: Distance (km) where to interpolate

    Returns:
        (lon, lat) tuple of interpolated position
    """
    if target_distance <= 0:
        return coordinates[0]
    if target_distance >= cumulative_distances[-1]:
        return coordinates[-1]

    # Find segment containing target distance
    idx = np.searchsorted(cumulative_distances, target_distance)

    if idx == 0:
        return coordinates[0]

    # Get segment endpoints
    d1 = cumulative_distances[idx - 1]
    d2 = cumulative_distances[idx]
    coord1 = coordinates[idx - 1]
    coord2 = coordinates[idx]

    # Linear interpolation along segment
    if d2 - d1 < 1e-9:  # Avoid division by zero
        return coord1

    t = (target_distance - d1) / (d2 - d1)
    lon = coord1[0] + t * (coord2[0] - coord1[0])
    lat = coord1[1] + t * (coord2[1] - coord1[1])

    return [lon, lat]


def simulate_minute_positions(coordinates, total_duration_min):
    """
    Simulate truck positions at 1-minute intervals.

    Args:
        coordinates: List of [lon, lat] pairs
        total_duration_min: Total trip duration in minutes

    Returns:
        DataFrame with columns: minute, lon, lat, distance_km, speed_kmh
    """
    # Compute cumulative distances
    cumulative_distances = compute_cumulative_distances(coordinates)
    total_distance_km = cumulative_distances[-1]

    # Handle very short routes (less than 1 minute)
    if total_duration_min < 1.0:
        return pd.DataFrame({
            'minute': [0],
            'lon': [coordinates[0][0]],
            'lat': [coordinates[0][1]],
            'distance_km': [0.0],
            'speed_kmh': [0.0]
        })

    # Generate minute intervals
    num_minutes = int(np.ceil(total_duration_min)) + 1
    minutes = np.arange(num_minutes)

    # Compute distance at each minute (uniform speed assumption)
    distances_at_minutes = (minutes / total_duration_min) * total_distance_km
    distances_at_minutes = np.clip(distances_at_minutes, 0, total_distance_km)

    # Interpolate positions
    positions = []
    for dist in distances_at_minutes:
        pos = interpolate_position(coordinates, cumulative_distances, dist)
        positions.append(pos)

    positions = np.array(positions)

    # Compute instantaneous speeds (km/h)
    speeds = []
    for i in range(len(minutes)):
        if i == 0:
            # First minute: use distance from start
            if len(minutes) > 1:
                speed = (distances_at_minutes[1] - distances_at_minutes[0]) * 60.0
            else:
                speed = 0.0
        else:
            # Speed = distance traveled in last minute * 60 (to get km/h)
            speed = (distances_at_minutes[i] - distances_at_minutes[i-1]) * 60.0

        speeds.append(speed)

    # Create DataFrame
    df = pd.DataFrame({
        'minute': minutes,
        'lon': positions[:, 0],
        'lat': positions[:, 1],
        'distance_km': np.round(distances_at_minutes, 4),
        'speed_kmh': np.round(speeds, 2)
    })

    return df


def process_route_file(route_file):
    """
    Process a single route file and generate minute-level simulation.

    Args:
        route_file: Path to route JSON file

    Returns:
        None (saves to Parquet file)
    """
    with open(route_file, 'r') as f:
        data = json.load(f)

    # Extract route ID
    route_id = Path(route_file).stem

    # Get geometry
    features = data.get('features', [])
    if not features:
        print(f"Warning: No features in {route_id}")
        return

    geometry = features[0].get('geometry', {})
    coordinates = geometry.get('coordinates', [])

    if not coordinates:
        print(f"Warning: No coordinates in {route_id}")
        return

    # Get duration
    properties = features[0].get('properties', {})
    summary = properties.get('summary', {})

    if 'duration' in summary:
        duration_min = summary['duration'] / 60.0
    else:
        # Estimate duration from distance
        cumulative_distances = compute_cumulative_distances(coordinates)
        total_distance_km = cumulative_distances[-1]
        duration_min = (total_distance_km / 75.0) * 60.0

    # Simulate minute positions
    df = simulate_minute_positions(coordinates, duration_min)

    # Add route ID
    df.insert(0, 'route_id', route_id)

    # Save to Parquet
    output_file = Path(f'outputs/sims/{route_id}_minutes.parquet')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_file, index=False, engine='pyarrow')


def main():
    """Main execution function."""
    print("=" * 60)
    print("STEP 2: Simulating Minute-by-Minute Positions")
    print("=" * 60)

    # Define paths
    routes_dir = Path('data/ors_routes')
    output_dir = Path('outputs/sims')

    # Get all JSON files
    route_files = sorted(routes_dir.glob('*.json'))

    if not route_files:
        print(f"Error: No route files found in {routes_dir}")
        return

    print(f"Found {len(route_files)} route files")
    print()

    # Process each route
    for route_file in tqdm(route_files, desc="Simulating routes"):
        process_route_file(route_file)

    # Summary statistics
    parquet_files = list(output_dir.glob('*.parquet'))
    print()
    print("Simulation complete!")
    print(f"Generated {len(parquet_files)} simulation files in {output_dir}")

    # Load one example to show
    if parquet_files:
        example_file = parquet_files[0]
        df_example = pd.read_parquet(example_file)
        print()
        print(f"Example: {example_file.name}")
        print(f"  - Total minutes: {len(df_example)}")
        print(f"  - Total distance: {df_example['distance_km'].max():.2f} km")
        print(f"  - Avg speed: {df_example['speed_kmh'].mean():.2f} km/h")
        print()
        print("First 5 rows:")
        print(df_example.head().to_string(index=False))
    print()


if __name__ == '__main__':
    main()
