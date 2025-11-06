#!/usr/bin/env python3
"""
Load administrative boundaries for state-level analysis.

This script:
1. Checks if admin boundaries exist locally
2. If missing, downloads Natural Earth admin-1 (states/provinces) 1:50m
3. Filters to US, Canada, Mexico
4. Saves to data/admin/admin1_states_provinces.geojson
"""

import os
from pathlib import Path
import geopandas as gpd
import zipfile
import urllib.request
from tqdm import tqdm


def download_with_progress(url, output_path):
    """
    Download file with progress bar.

    Args:
        url: URL to download from
        output_path: Local path to save to
    """
    print(f"Downloading from {url}")

    class DownloadProgressBar(tqdm):
        def update_to(self, b=1, bsize=1, tsize=None):
            if tsize is not None:
                self.total = tsize
            self.update(b * bsize - self.n)

    with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=output_path.name) as t:
        urllib.request.urlretrieve(url, filename=output_path, reporthook=t.update_to)


def load_boundaries():
    """
    Load or download administrative boundaries.

    Returns:
        GeoDataFrame of state/province boundaries
    """
    admin_file = Path('data/admin/admin1_states_provinces.geojson')

    # Check if file already exists
    if admin_file.exists():
        print(f"Loading existing boundaries from {admin_file}")
        gdf = gpd.read_file(admin_file)
        print(f"Loaded {len(gdf)} administrative regions")
        return gdf

    print("Boundaries not found locally. Downloading from Natural Earth...")
    print()

    # Create admin directory
    admin_dir = Path('data/admin')
    admin_dir.mkdir(parents=True, exist_ok=True)

    # Natural Earth Admin 1 - States, Provinces URL
    # Using 1:50m cultural vectors - admin 1 states/provinces
    url = 'https://naciscdn.org/naturalearth/50m/cultural/ne_50m_admin_1_states_provinces.zip'

    # Download to temporary location
    temp_zip = admin_dir / 'ne_50m_admin_1_states_provinces.zip'

    try:
        download_with_progress(url, temp_zip)
    except Exception as e:
        print(f"Error downloading: {e}")
        print("Please manually download from:")
        print(url)
        print(f"And extract to {admin_dir}")
        return None

    print()
    print("Extracting...")

    # Extract zip file
    with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
        zip_ref.extractall(admin_dir)

    print("Loading shapefile...")

    # Load the shapefile
    shapefile_path = admin_dir / 'ne_50m_admin_1_states_provinces.shp'

    if not shapefile_path.exists():
        print(f"Error: Expected shapefile not found at {shapefile_path}")
        return None

    gdf = gpd.read_file(shapefile_path)

    print(f"Loaded {len(gdf)} administrative regions worldwide")

    # Filter to North America (US, Canada, Mexico)
    north_america = gdf[gdf['iso_a2'].isin(['US', 'CA', 'MX'])].copy()

    print(f"Filtered to {len(north_america)} regions in US, CA, MX")

    # Keep relevant columns
    columns_to_keep = ['name', 'name_en', 'iso_a2', 'iso_3166_2', 'postal', 'geometry']
    columns_available = [col for col in columns_to_keep if col in north_america.columns]
    north_america = north_america[columns_available]

    # Save to GeoJSON
    print(f"Saving to {admin_file}")
    north_america.to_file(admin_file, driver='GeoJSON')

    # Clean up temporary files
    print("Cleaning up temporary files...")
    temp_zip.unlink()

    # Remove extracted shapefiles
    for f in admin_dir.glob('ne_50m_admin_1_states_provinces.*'):
        f.unlink()

    print()
    print("Done!")
    return north_america


def main():
    """Main execution function."""
    print("=" * 60)
    print("STEP 3: Loading Administrative Boundaries")
    print("=" * 60)
    print()

    gdf = load_boundaries()

    if gdf is not None:
        print()
        print("Summary:")
        print(f"  - Total regions: {len(gdf)}")
        if 'iso_a2' in gdf.columns:
            print(f"  - US: {len(gdf[gdf['iso_a2'] == 'US'])}")
            print(f"  - CA: {len(gdf[gdf['iso_a2'] == 'CA'])}")
            print(f"  - MX: {len(gdf[gdf['iso_a2'] == 'MX'])}")
        print(f"  - CRS: {gdf.crs}")
        print()

        # Show a few examples
        if 'name' in gdf.columns:
            print("Example regions:")
            print(gdf[['name', 'iso_a2']].head(10).to_string(index=False))
        print()
    else:
        print()
        print("Warning: Could not load boundaries.")
        print("State-level analysis will be skipped in subsequent steps.")
        print()


if __name__ == '__main__':
    main()
