#!/usr/bin/env python3
import os, json, glob
import pandas as pd
import numpy as np

os.makedirs("outputs", exist_ok=True)

records = []
for fp in glob.glob("ors_routes/routes_*.geojson"):
    with open(fp, "r") as f:
        gj = json.load(f)

    # Handle FeatureCollection or single Feature
    if isinstance(gj, dict) and gj.get("type") == "FeatureCollection":
        feats = gj.get("features") or []
        if not feats:
            print(f"[skip] {fp} has no features")
            continue
        feat = feats[0]
    elif isinstance(gj, dict) and gj.get("type") == "Feature":
        feat = gj
    else:
        print(f"[skip] {fp} is not a Feature/FeatureCollection")
        continue

    props = (feat.get("properties") or {})
    # Fallback pair name from filename if property missing
    pair = props.get("pair") or os.path.basename(fp).removeprefix("routes_").removesuffix(".geojson")

    # ORS summary: distance (m), duration (s)
    summary = props.get("summary") or {}
    dist_km = (summary.get("distance", 0) or 0) / 1000.0
    dur_min = (summary.get("duration", 0) or 0) / 60.0
    avg_kmh = dist_km / (dur_min / 60.0) if dur_min > 0 else np.nan

    records.append({
        "pair": pair,
        "distance_km": dist_km,
        "duration_min": dur_min,
        "avg_speed_kmh": avg_kmh,
    })

df = pd.DataFrame.from_records(records).sort_values("pair")
df.to_csv("outputs/routes.csv", index=False)
print(f"[OK] Rebuilt outputs/routes.csv with {len(df)} rows and columns: {list(df.columns)}")
