Truck Routing – Background & Attempted Approaches

This document summarizes all major approaches tested for building a North American truck-accessible routing system, describing both the intent and the reasons for failure.
The goal was to compute all pairwise highway routes between major metropolitan regions using open data, offline tools, and lightweight computation on a personal computer (16 GB RAM, ~6-year-old laptop).

1. Full North America OSRM Attempt

Goal:
Download the full North America extract from Geofabrik
 and run a local OSRM server with a custom truck.lua profile for realistic heavy-vehicle routing.

Steps:

Acquired the large north-america-latest.osm.pbf (~100 GB).

Preprocessed it with:

osrm-extract -p profiles/truck.lua north-america-latest.osm.pbf
osrm-partition north-america-latest.osrm
osrm-customize north-america-latest.osrm
osrm-routed --algorithm mld


Designed the truck.lua profile to exclude non-truck roads and handle speed limits.

Result:
Failed due to hardware limits.
OSRM extraction and partitioning exhausted 16 GB RAM and swap space; preprocessing never completed. Docker container eventually terminated due to memory pressure.

2. Full North America with Valhalla

Goal:
Use the same Geofabrik North America extract with Valhalla (open-source routing engine) to attempt more flexible routing.

Steps:

Set up Valhalla Docker instance.

Imported the .osm.pbf data.

Tried to use the truck costing profile.

Result:
 Same limitation — preprocessing the full continent was infeasible on local hardware.
Memory usage exceeded capacity during the graph building phase.

3. Regional Split: East / Central / West OSRM Servers

Goal:
Split the North American dataset into three manageable regions:

east.osm.pbf

central.osm.pbf

west.osm.pbf

Then run three OSRM Docker servers simultaneously, each serving its own region.

Process:

Downloaded regional PBF subsets.

Used Docker OSRM containers on different ports (8001, 8002, 8003).

Routed between major city centroids using custom truck profiles.

Integrated geocoding (lat/lon for 22 metropolitan regions) and post-processing for analytics.

Result:
Still failed — while smaller, preprocessing each region sequentially was still RAM-intensive.
Running multiple containers concurrently led to disk I/O thrashing and swap exhaustion.
Overall routing performance was unstable, with incomplete partitions and container crashes.

4. Osmium-Filtered Highways Only

Goal:
Reduce data volume drastically by filtering OSM data to include only truck-accessible highways (tags such as highway=motorway|trunk, hgv!=no, access!=no, etc.) and exclude footways, residential roads, etc.

Process:

Used osmium tags-filter and osmium extract to create a smaller subset:

osmium tags-filter north-america-latest.osm.pbf w/highway=motorway,trunk


Ran osrm-extract and osrm-partition on the filtered file.

Result:
Failed again — despite reduced file size, OSRM still required more RAM for preprocessing than available locally.
Partial extractions were successful but routing server failed to start due to incomplete graph coverage.

5. Smaller Subsets & Fewer Routes

Goal:
Test minimal workloads by:

Using smaller state-level or corridor-level extracts.

Running limited pairwise routes.

Process:

Extracted only selected metro-region corridors.

Attempted lightweight OSRM builds (e.g., “Chicago–Kansas City”, “Houston–Dallas”).

Result:
Still limited by hardware during the osrm-partition stage.
Even smaller regional extracts exceeded memory limits when multiple runs were chained together.

6. Current Approach – OpenRouteService (ORS) API

After multiple failed attempts to process large-scale routing locally, the final and stable solution adopted was OpenRouteService (ORS) via its public API.

Key differences:

External routing engine (no local Docker needed).

Simple Python-based call structure using ors_geopandas_pipeline.py.

Routes retrieved as GeoJSON and analyzed locally with pandas, geopandas, and the simulation workflow.

✅ Result: Reliable, reproducible, and lightweight.
The trade-off is dependence on an external API and an API key, but it enabled full route coverage and integration with downstream analytics (simulation, state-level minutes, histograms, etc.).

Summary Table
Attempt	Tool / Engine	Data Size	Local / External	Result
1	OSRM (full NA)	~100 GB	Local	❌ Memory overflow
2	Valhalla (full NA)	~100 GB	Local	❌ Memory overflow
3	OSRM (3 splits)	~3×30 GB	Local (3 Docker servers)	❌ Still too heavy
4	OSRM (filtered OSM)	Reduced	Local	❌ RAM + coverage issues
5	OSRM (small corridors)	Minimal	Local	❌ Unstable, still heavy
6	ORS API (current)	Lightweight	External	✅ Working
Final Note

The OpenRouteService API workflow (via ors_geopandas_pipeline.py) proved to be the most practical and efficient approach given the hardware constraints.
All subsequent analytics (distance histograms, duration estimation, minute-level simulations) are based on the ORS-generated routes.