#!/usr/bin/env python3
import os, json, time, requests, geopandas as gpd, pandas as pd
from shapely.geometry import LineString
from tqdm import tqdm

import sys, os
api_key = os.environ.get("ORS_API_KEY") or ""
if not api_key.strip():
    print("Missing ORS_API_KEY — export it first or hardcode below.")
    # Uncomment the next line to hardcode temporarily:
    # api_key = "your_real_api_key_here"
    sys.exit(1)
else:
    print(f"[✓] ORS key detected: {api_key[:6]}...{api_key[-4:]}")


API_URL = "https://api.openrouteservice.org/v2/directions/driving-hgv/geojson"
HEADERS = {"Authorization": api_key, "Content-Type": "application/json"}
SLEEP_SEC = 2.0  # free tier safe rate

pairs = pd.read_csv("city_coordinates.csv")
out_dir = "ors_routes"
os.makedirs(out_dir, exist_ok=True)

records = []

for _, r in tqdm(pairs.iterrows(), total=len(pairs)):
    pair_name = f"{r.City_A}_to_{r.City_B}".replace(" ", "_")
    geojson_path = os.path.join(out_dir, f"{pair_name}.json")

    if os.path.exists(geojson_path) and os.path.getsize(geojson_path) > 1000:
        print(f"[skip] {pair_name}")
        continue

    body = {
        "coordinates": [[r.Lon_A, r.Lat_A], [r.Lon_B, r.Lat_B]],
        "attributes": ["avgspeed"],
        "instructions": False,
        "units": "km"
    }

    resp = requests.post(API_URL, headers=HEADERS, json=body)
    if resp.status_code == 200:
        with open(geojson_path, "w") as f:
            f.write(resp.text)
        print(f"[ok] {pair_name}")
    else:
        print(f"[fail] {pair_name} -> {resp.status_code}")
    time.sleep(SLEEP_SEC)

# --- Load all routes into GeoDataFrame ---
gdfs = []
for file in os.listdir(out_dir):
    if not file.endswith(".json"):
        continue
    path = os.path.join(out_dir, file)
    try:
        gdf = gpd.read_file(path)
        gdf["pair"] = file.replace(".json", "")
        gdfs.append(gdf)
    except Exception as e:
        print(f"[warn] Failed {file}: {e}")

routes = pd.concat(gdfs, ignore_index=True)
routes = gpd.GeoDataFrame(routes, geometry="geometry", crs="EPSG:4326")

import ast

def parse_summary(val):
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        try:
            return ast.literal_eval(val)
        except Exception:
            return {}
    return {}

routes["summary"] = routes["summary"].apply(parse_summary)
routes["distance_km"] = routes["summary"].apply(lambda s: s.get("distance", 0) / 1000)
routes["duration_min"] = routes["summary"].apply(lambda s: s.get("duration", 0) / 60)


routes["duration_hr"] = routes["summary"].apply(lambda s: s.get("duration", 0)/3600)
routes["avg_speed_kmh"] = routes["distance_km"] / routes["duration_hr"]

# Save for notebook use
routes.to_file("ors_routes_combined.geojson", driver="GeoJSON")
routes[["pair", "distance_km", "duration_hr", "avg_speed_kmh"]].to_csv("route_summaries.csv", index=False)

print("\n Saved combined GeoJSON and CSV summaries")

