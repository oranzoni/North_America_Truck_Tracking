# Simulation Data Runbook

A practical guide for working with minute-level truck route simulation data.

## What Are the Simulation Files?

The `outputs/sims/` directory contains **minute-by-minute position data** for each truck route. Each file is a Parquet file (compressed columnar format) with one row per minute of travel.

### File Naming Convention

```
outputs/sims/{route_id}_minutes.parquet
```

Examples:
- `Los_Angeles_to_Boston_minutes.parquet`
- `Miami_to_San_Francisco_minutes.parquet`
- `Phoenix_to_Seattle_minutes.parquet`

### Schema

Each Parquet file contains these columns:

| Column | Type | Description |
|--------|------|-------------|
| `route_id` | string | Route identifier (e.g., "Los_Angeles_to_Boston") |
| `minute` | int | Minute index (0 = start, 1 = first minute, etc.) |
| `lon` | float | Longitude (decimal degrees, WGS84) |
| `lat` | float | Latitude (decimal degrees, WGS84) |
| `distance_km` | float | Cumulative distance traveled (km) |
| `speed_kmh` | float | Instantaneous speed during this minute (km/h) |

**Note:** These are tabular files with lon/lat columns, not GeoDataFrames. You can convert them to GeoJSON/Shapefile using the export commands below.

---

## Quick Start with CLI

The `scripts/sim_runner.py` tool provides easy access to all simulation data.

### 1. List Available Routes

See all routes that have simulation data:

```bash
python scripts/sim_runner.py list
```

**Output:**
```
============================================================
Available Route Simulations
============================================================

Found 8 route(s):

   1. Los_Angeles_to_Boston                  (138.0 KB)
   2. Los_Angeles_to_San_Diego                (10.0 KB)
   3. Miami_to_San_Francisco                 (141.0 KB)
   4. New_York_to_Philadelphia                 (8.8 KB)
   5. Philadelphia_to_Baltimore                (9.3 KB)
   6. Phoenix_to_Seattle                      (64.0 KB)
   7. San_Antonio_to_Austin                    (8.0 KB)
   8. Washington_to_Baltimore                  (6.5 KB)
```

---

### 2. Preview Data

Quickly inspect the first N rows of any route:

```bash
python scripts/sim_runner.py head --route Los_Angeles_to_Boston --n 100
```

**Output:**
```
============================================================
Preview: Los_Angeles_to_Boston (first 10 rows)
============================================================

                route_id  minute         lon        lat  distance_km  speed_kmh
Los_Angeles_to_Boston       0 -118.243683  34.052234       0.0000      70.28
Los_Angeles_to_Boston       1 -118.231456  34.058923       1.1713      70.28
Los_Angeles_to_Boston       2 -118.219229  34.065612       2.3427      70.28
...

Total rows: 4123
```

**Tip:** Use `--n 5` for just 5 rows, or `--n 100` for more context.

---

### 3. Get Summary Statistics

View key metrics for a route:

```bash
python scripts/sim_runner.py summary --route Miami_to_San_Francisco
```

**Output:**
```
============================================================
Summary: Miami_to_San_Francisco
============================================================

Duration:
  - Total minutes: 4195
  - Total hours: 69.92

Distance:
  - Total: 4951.73 km

Speed (km/h):
  - Min: 70.76
  - Median: 70.82
  - Mean: 70.82
  - 95th percentile: 70.85
  - Max: 70.85

Geographic Bounds:
  - Longitude: [-122.4194, -80.1918]
  - Latitude: [25.7617, 37.7749]

Data Info:
  - Total rows: 4,196
  - Columns: route_id, minute, lon, lat, distance_km, speed_kmh
```

---

### 4. Export to Different Formats

#### Export to CSV

Good for Excel, Google Sheets, or other spreadsheet tools:

```bash
python scripts/sim_runner.py export \
  --route Los_Angeles_to_San_Diego \
  --to csv \
  --out outputs/exports/Los_Angeles_to_San_Diego.csv
```

The CSV will include all columns: `route_id`, `minute`, `lon`, `lat`, `distance_km`, `speed_kmh`.

#### Export to GeoJSON

Perfect for GIS tools (QGIS, ArcGIS, web maps):

```bash
python scripts/sim_runner.py export \
  --route Phoenix_to_Seattle \
  --to geojson \
  --out outputs/exports/Phoenix_to_Seattle.geojson
```

This creates Point features with WGS84 coordinates. Each point has properties from the data columns.

**Use case:** Load in QGIS to visualize the route on a map with basemaps and other layers.

#### Export to Parquet

Re-export or filter columns:

```bash
python scripts/sim_runner.py export \
  --route New_York_to_Philadelphia \
  --to parquet \
  --out outputs/exports/New_York_to_Philadelphia_copy.parquet
```

**Why?** Parquet is fast and compact. Great for sharing or archiving.

---

### 5. Merge All Routes

Combine all routes into a single file for global analysis:

```bash
python scripts/sim_runner.py merge \
  --out outputs/exports/all_minutes.parquet
```

**Output:**
```
============================================================
Merging All Route Simulations
============================================================

Found 8 routes to merge

Loading routes: 100%|████████████| 8/8 [00:00<00:00, 300.00it/s]

Concatenating DataFrames...
Merged 10,957 rows

Saved merged file: outputs/exports/all_minutes.parquet
File size: 0.39 MB
```

The merged file includes a `route_id` column to identify each route.

**Use case:** Analyze speed distributions, state crossings, or time patterns across the entire fleet.

---

### 6. Plot Route Paths

Create a quick static visualization:

#### Simple Path Plot

```bash
python scripts/sim_runner.py plot \
  --route Los_Angeles_to_Boston \
  --map outputs/figures/Los_Angeles_to_Boston_path.png
```

Shows the path with start (green circle) and end (red square) markers.

#### Speed-Colored Path Plot

```bash
python scripts/sim_runner.py plot \
  --route Phoenix_to_Seattle \
  --map outputs/figures/Phoenix_to_Seattle_path.png \
  --speed
```

Colors the path by instantaneous speed (km/h). Great for spotting speed variations along the route.

**Tip:** These are quick exploratory plots. For publication-quality maps, export to GeoJSON and use QGIS or a mapping library.

---

### 7. Export to GPX (Optional)

For use with GPS devices or routing tools:

```bash
python scripts/sim_runner.py to-gpx \
  --route San_Antonio_to_Austin \
  --out outputs/exports/San_Antonio_to_Austin.gpx
```

GPX files can be opened in Google Earth, Garmin devices, or routing apps.

---

## Working from Python REPL

If you prefer interactive Python:

### Load a Single Route

```python
import pandas as pd

# Load simulation data
df = pd.read_parquet('outputs/sims/Los_Angeles_to_Boston_minutes.parquet')

# Inspect
print(df.head())
print(df.info())

# Basic stats
print(f"Total distance: {df['distance_km'].max():.2f} km")
print(f"Duration: {df['minute'].max()} minutes")
print(f"Average speed: {df['speed_kmh'].mean():.2f} km/h")
```

### Quick Plot with Matplotlib

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_parquet('outputs/sims/Phoenix_to_Seattle_minutes.parquet')

# Create plot
fig, ax = plt.subplots(figsize=(10, 8))
ax.plot(df['lon'], df['lat'], 'b-', linewidth=1.5)
ax.scatter(df['lon'].iloc[0], df['lat'].iloc[0], c='green', s=100, label='Start')
ax.scatter(df['lon'].iloc[-1], df['lat'].iloc[-1], c='red', s=100, label='End')
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_title('Phoenix to Seattle Route')
ax.set_aspect('equal')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('my_route_plot.png', dpi=150)
plt.show()
```

### Filter by Speed

Find minutes where speed exceeded 75 km/h:

```python
import pandas as pd

df = pd.read_parquet('outputs/sims/Miami_to_San_Francisco_minutes.parquet')

# Filter
fast_segments = df[df['speed_kmh'] > 75]

print(f"Found {len(fast_segments)} minutes with speed > 75 km/h")
print(fast_segments[['minute', 'lon', 'lat', 'speed_kmh']].head())
```

### Load All Routes

```python
import pandas as pd
from pathlib import Path

# Find all Parquet files
sims_dir = Path('outputs/sims')
parquet_files = sims_dir.glob('*_minutes.parquet')

# Load and concatenate
dfs = []
for pf in parquet_files:
    df = pd.read_parquet(pf)
    dfs.append(df)

all_routes = pd.concat(dfs, ignore_index=True)

print(f"Loaded {len(all_routes):,} total minutes across {all_routes['route_id'].nunique()} routes")
```

---

## Parquet 101

### What is Parquet?

Parquet is a **columnar storage format** designed for analytics:

- **Fast:** Optimized for reading specific columns
- **Compact:** Built-in compression (typically 5-10x smaller than CSV)
- **Typed:** Preserves data types (no "01234" → 1234 issues)
- **Portable:** Works with Python, R, SQL, Spark, and many BI tools

### Reading Parquet

```python
import pandas as pd

# Read entire file
df = pd.read_parquet('outputs/sims/route_minutes.parquet')

# Read specific columns only (faster!)
df = pd.read_parquet('outputs/sims/route_minutes.parquet',
                     columns=['lon', 'lat', 'speed_kmh'])
```

## Common Tasks

### Task: Find the Longest Route

```bash
python scripts/sim_runner.py list
# Manually check file sizes

# Or via Python:
```

```python
import pandas as pd
from pathlib import Path

routes = {}
for pf in Path('outputs/sims').glob('*_minutes.parquet'):
    route_id = pf.stem.replace('_minutes', '')
    df = pd.read_parquet(pf)
    routes[route_id] = df['distance_km'].max()

# Sort by distance
sorted_routes = sorted(routes.items(), key=lambda x: x[1], reverse=True)
print("Longest routes:")
for route, dist in sorted_routes[:5]:
    print(f"  {route}: {dist:.2f} km")
```

### Task: Calculate Total Fleet Distance

```bash
python scripts/sim_runner.py merge --out outputs/exports/all_minutes.parquet
```

```python
import pandas as pd

df = pd.read_parquet('outputs/exports/all_minutes.parquet')

# Total distance per route
distances = df.groupby('route_id')['distance_km'].max()
print(f"Total fleet distance: {distances.sum():.2f} km")
```

### Task: Export Multiple Routes to CSV

```bash
# Bash loop
for route in Los_Angeles_to_Boston Miami_to_San_Francisco Phoenix_to_Seattle; do
  python scripts/sim_runner.py export \
    --route $route \
    --to csv \
    --out outputs/exports/${route}.csv
done
```

Or use `scripts/cli_examples.sh` (see below).

### Task: Find Average Speed Across All Routes

```python
import pandas as pd

df = pd.read_parquet('outputs/exports/all_minutes.parquet')

# Exclude zero-speed points (start/end)
speeds = df[df['speed_kmh'] > 0]['speed_kmh']

print(f"Average speed: {speeds.mean():.2f} km/h")
print(f"Median speed: {speeds.median():.2f} km/h")
print(f"Std dev: {speeds.std():.2f} km/h")
```

---

## Troubleshooting

### Problem: `ModuleNotFoundError: No module named 'pyarrow'`

**Solution:** Install PyArrow:

```bash
pip install pyarrow
```

Or reinstall all dependencies:

```bash
pip install -r requirements.txt
```

---

### Problem: `FileNotFoundError: outputs/sims/ROUTE_ID_minutes.parquet`

**Cause:** The route ID is incorrect or the simulation hasn't been generated.

**Solution:**

1. Check available routes:
   ```bash
   python scripts/sim_runner.py list
   ```

2. Use the exact route ID shown (case-sensitive, underscores matter).

3. If no routes exist, run the simulation pipeline:
   ```bash
   python scripts/simulate_minutes.py
   ```

---

### Problem: Export commands create huge files

**Cause:** CSV and GeoJSON are text-based (much larger than Parquet).

**Solutions:**

- **Stick with Parquet** for large datasets
- **Filter before exporting:**

  ```python
  import pandas as pd

  # Load and filter
  df = pd.read_parquet('outputs/sims/route_minutes.parquet')
  df_sample = df[df['minute'] % 10 == 0]  # Every 10th minute

  # Export smaller file
  df_sample.to_csv('outputs/exports/route_sampled.csv', index=False)
  ```

- **Use compression for CSV:**

  ```python
  df.to_csv('route.csv.gz', index=False, compression='gzip')
  ```

---

### Problem: Plots look distorted (lon/lat aspect ratio)

**Cause:** Equal aspect ratio not applied.

**Solution:** Always use `ax.set_aspect('equal')` when plotting lon/lat:

```python
fig, ax = plt.subplots()
ax.plot(df['lon'], df['lat'])
ax.set_aspect('equal', adjustable='box')  # Critical!
plt.show()
```

---

### Problem: Can't install geopandas for GeoJSON export

**Cause:** Geopandas has complex dependencies (GDAL, GEOS, etc.).

**Solutions:**

1. **Use conda (recommended):**
   ```bash
   conda install geopandas
   ```

2. **Or export to CSV** and convert in QGIS:
   ```bash
   python scripts/sim_runner.py export --route ROUTE --to csv --out route.csv
   ```
   Then in QGIS: Layer → Add Delimited Text Layer → Set X = lon, Y = lat, CRS = EPSG:4326

3. **Use Docker** (for complex environments):
   ```dockerfile
   FROM python:3.10
   RUN apt-get update && apt-get install -y gdal-bin libgdal-dev
   RUN pip install geopandas
   ```

---

### Problem: "RuntimeWarning: invalid value encountered in divide"

**Cause:** Speed calculation may produce NaN or inf for zero-distance segments.

**Solution:** This is expected for start/end points. The scripts filter out zero-speed values automatically. Ignore the warning or filter manually:

```python
df_clean = df[df['speed_kmh'].notna() & (df['speed_kmh'] > 0)]
```

---

### Problem: Merged file is too large to load

**Cause:** All routes combined may exceed RAM.

**Solutions:**

1. **Load in chunks:**
   ```python
   import pandas as pd

   # Read first 1000 rows
   df = pd.read_parquet('all_minutes.parquet', engine='pyarrow')
   df_sample = df.head(1000)
   ```

2. **Filter by route before loading:**
   ```python
   # Using PyArrow filters
   import pyarrow.parquet as pq

   table = pq.read_table('all_minutes.parquet',
                         filters=[('route_id', '=', 'Los_Angeles_to_Boston')])
   df = table.to_pandas()
   ```

3. **Use DuckDB for SQL queries:**
   ```python
   import duckdb

   result = duckdb.query("""
       SELECT route_id, AVG(speed_kmh) as avg_speed
       FROM 'all_minutes.parquet'
       WHERE speed_kmh > 0
       GROUP BY route_id
   """).to_df()
   ```

---

## Ready-to-Use Commands

See `scripts/cli_examples.sh` for copy-paste commands for all common tasks.

---

## Additional Resources

- **Pandas Parquet docs:** https://pandas.pydata.org/docs/reference/api/pandas.read_parquet.html
- **GeoPandas GeoJSON:** https://geopandas.org/en/stable/docs/user_guide/io.html
- **PyArrow Parquet:** https://arrow.apache.org/docs/python/parquet.html
- **Matplotlib tutorials:** https://matplotlib.org/stable/tutorials/index.html

---

## Next Steps

1. **Explore the data:**
   ```bash
   python scripts/sim_runner.py list
   python scripts/sim_runner.py summary --route YOUR_ROUTE
   ```

2. **Export for analysis:**
   ```bash
   python scripts/sim_runner.py export --route YOUR_ROUTE --to csv --out route.csv
   ```

3. **Create visualizations:**
   ```bash
   python scripts/sim_runner.py plot --route YOUR_ROUTE --map route_map.png --speed
   ```

4. **Read the main README:** `README.md` for the full project documentation.

---

