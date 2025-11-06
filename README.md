# Truck Routing – Quick Start (ORS + Optional Graph + Simulation)

## 1. OpenRouteService (ORS) API Key

**Get your free API key:**

1. Go to [openrouteservice.org/dev/#/signup](https://openrouteservice.org/dev/#/signup)
2. Sign up for a free account
3. Navigate to **Dashboard → Tokens** and create a new token
4. Copy your API key

**Store the key locally:**

**Option A – Environment variable (recommended):**
```bash
export ORS_API_KEY="YOUR_KEY_HERE"
```

**Option B – .env file:**
```
ORS_API_KEY=YOUR_KEY_HERE
```

## 2. Running ors_geopandas_pipeline.py

Downloads routes from ORS using GeoPandas and saves outputs to `ors_routes/`.

**Run:**
```bash
python ors_geopandas_pipeline.py
```

- **Input:** Reads `city_coordinates.csv` (CSV with city pairs and lat/lon columns)
- **Output:** Individual route GeoJSON files in `ors_routes/` + combined `ors_routes_combined.geojson`

## 3. (Optional) Graph Generation

Run graph generation if you want a graph view of the routes.

```bash
python scripts/graph_build.py --routes ors_routes/ --out outputs/graph/
```

- **Output:** Graph files in `outputs/graph/` (if script exists)

## 4. (Optional) Simulation

Simulate minute-by-minute positions from existing routes (local, no external API).

```bash
python scripts/compute_distance_duration.py
python scripts/simulate_minutes.py
```

- **Output:** Minute-level simulations in `outputs/sims/` and summary in `outputs/routes_summary.csv`
