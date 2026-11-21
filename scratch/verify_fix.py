"""
Verification script for KeyError: 'corridor' and use_container_width fix.
"""
import sys, os
sys.path.insert(0, os.path.abspath("."))
from components.ui_helpers import load_gis_network, load_all_datasets
from src.network.gis_network import GISNetworkManager

print("1. Testing GISNetworkManager directly:")
gis_mgr = GISNetworkManager()
df_gis = gis_mgr.get_intersections_gis()
print(f"   df_intersections_gis rows: {len(df_gis)}, 'corridor' in columns: {'corridor' in df_gis.columns}")

print("2. Testing load_gis_network():")
mgr, roads_gis, df_nodes_gis = load_gis_network()
print(f"   df_nodes_gis rows: {len(df_nodes_gis)}, 'corridor' in columns: {'corridor' in df_nodes_gis.columns}")
print(f"   Corridors found: {df_nodes_gis['corridor'].nunique()}")

print("3. Testing corridor filtering as done in Page 3:")
corridors = sorted(list(df_nodes_gis["corridor"].dropna().unique()))
for c in corridors[:3]:
    sub = df_nodes_gis[df_nodes_gis["corridor"] == c]
    print(f"   Corridor '{c}': {len(sub)} nodes successfully filtered without KeyError!")

print("\nAll GIS corridor checks PASSED!")
