"""
Demonstration script for Phase 3 completion conditions:
- Demonstrates one origin-to-hospital route.
- Demonstrates alternative routes.
- Shows route distance, travel time, average speed, and campus delay.
- Shows real Bengaluru road geometry segments and cardinal headings.
"""

import sys, os
sys.path.insert(0, os.path.abspath("."))
from src.network.ambulance_graph import get_ambulance_road_graphs
from src.network.ambulance_router import AmbulanceRouter, PROFILE_MINIMUM_TIME
from components.gis_map import calculate_bearing, bearing_to_cardinal

# 1. Initialize
g_multi, g_di = get_ambulance_road_graphs()
router = AmbulanceRouter(graph_multi=g_multi, graph_di=g_di)

# 2. Select Origin and Hospital Destination
origin_id = "INT_001_RAJARAJESHWARI_JUNCTION"  # Majestic Core / Mysore Road
hospital_id = "BLR_HOSP_0052"                  # Victoria Hospital Trauma Center

print("=" * 80)
print(f"AMBULANCE ROUTE OPTIMIZATION — LIVE DEMONSTRATION")
print("=" * 80)
print(f"Origin: {g_di.nodes[origin_id].get('name')} ({origin_id})")
print(f"Hospital Target: Victoria Hospital ({hospital_id})")
print(f"Routing Objective: Minimum Estimated Travel Time (IRC:106 Calibrated)")
print("-" * 80)

# 3. Calculate Primary Route to Hospital
res = router.route_to_hospital(origin=origin_id, hospital_id_or_name=hospital_id, profile=PROFILE_MINIMUM_TIME)

print("\n--- 1. PRIMARY OPTIMAL ROUTE (Rank 1 - Minimum Travel Time) ---")
print(f"Status: {res['status']}")
print(f"Emergency Classification: {res['verification_status']} ({res['emergency_service_type']})")
print(f"Total Estimated Travel Time: {res['total_time_min']:.2f} minutes ({res['total_time_sec']:.0f} seconds)")
print(f"  └─ Road Network Travel Time: {res['road_travel_time_min']:.2f} min")
print(f"  └─ Hospital Campus Driveway Delay: {res['driveway_access_time_min']:.2f} min (15 km/h speed + 1.0 min gate delay)")
print(f"Total Road Distance: {res['total_distance_km']:.3f} km ({res['total_distance_m']:,.1f} meters)")
print(f"  └─ Road Network Distance: {res['road_distance_km']:.3f} km")
print(f"  └─ Driveway Access Distance: {res['driveway_access_distance_m']:,.1f} m")
print(f"Effective Average Speed: {res['average_speed_kmh']:.1f} km/h")
print(f"Number of Segments: {res['num_segments']} links across {len(res['path_nodes'])} junctions")
print(f"Polyline Geometry Coordinates: {len(res['route_geometry'])} waypoints following authentic OSM road curves")

print("\n--- 2. TURN-BY-TURN EMERGENCY NAVIGATION ITINERARY ---")
cum_dist = 0.0
cum_time = 0.0
for edge in res["path_edges"]:
    dist = edge["length_m"]
    time_s = edge["travel_time_sec"]
    cum_dist += dist
    cum_time += time_s
    geom = edge.get("geometry", [])
    heading = "Straight"
    if geom and len(geom) >= 2:
        b = calculate_bearing(geom[0][0], geom[0][1], geom[-1][0], geom[-1][1])
        heading = f"{bearing_to_cardinal(b)} ({b:.0f}°)"

    print(f"Step {edge['step']}: [{edge['from_name'][:25]}] -> [{edge['to_name'][:25]}]")
    print(f"       Road: {edge['road_name']} | Speed: {edge['speed_kmh']} km/h | Heading: {heading}")
    print(f"       Distance: {dist:,.0f} m | Time: {time_s:.0f}s | Cumulative: {cum_dist/1000:.2f} km, {cum_time/60:.1f} min")

# 4. Calculate Alternative Routes via Yen's Algorithm
snapped_junction = res["target_intersection_id"]
alts = router.find_k_alternative_routes(origin=origin_id, destination=snapped_junction, K=3)

print("\n--- 3. YEN'S K-SHORTEST LOOPLESS ALTERNATIVE ROUTES (K=3) ---")
for alt in alts:
    rk = alt["rank"]
    t_min = alt["total_time_min"]
    d_km = alt["total_distance_km"]
    v_kmh = alt["average_speed_kmh"]
    d_desc = alt["divergence_description"]
    delta_t = alt["time_delta_from_primary_min"]
    print(f"Option {rk} (Rank {rk}):")
    print(f"  - Travel Time: {t_min:.2f} min (Time Delta: +{delta_t:.2f} min)")
    print(f"  - Road Distance: {d_km:.2f} km")
    print(f"  - Average Speed: {v_kmh:.1f} km/h")
    print(f"  - Divergence Context: {d_desc}")

# 5. Distance vs Time Tradeoff Comparison
comp = router.compare_distance_vs_time_routes(origin=origin_id, destination=snapped_junction)
print("\n--- 4. TRAVEL TIME VS. SHORTEST DISTANCE BENCHMARK ---")
print(f"Minimum-Time Route: {comp['fastest_time_min']:.2f} min ({comp['fastest_distance_km']:.2f} km)")
print(f"Shortest-Distance Route: {comp['shortest_dist_time_min']:.2f} min ({comp['shortest_distance_km']:.2f} km)")
print(f"Time Saved by Min-Time Route: {comp['time_saved_min']:.2f} min ({comp['time_saved_percentage']}%)")
print(f"Distance Added by Min-Time Route: +{comp['delta_distance_km']:.2f} km")
print(f"Tradeoff Analysis: {comp['tradeoff_explanation']}")
print("=" * 80)
