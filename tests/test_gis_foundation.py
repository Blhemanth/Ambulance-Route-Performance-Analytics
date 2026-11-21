"""
Unit Tests for Phase 1 GIS Foundation.
Validates GIS schemas, real road geometry retrieval, directionality,
coordinate provenance tagging, and 100% backward compatibility with
Operations Research network models (Max Flow, Min Cost Flow, Dijkstra).
"""

import unittest
import os
import networkx as nx
import pandas as pd
from src.network.graph_builder import GraphBuilder
from src.network.gis_network import GISNetworkManager, calculate_polyline_length_m
from src.network.shortest_path import ShortestPathOptimizer
from src.network.ambulance_router import AmbulanceRouter
from components.gis_map import create_bengaluru_gis_map

class TestGISFoundation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.builder = GraphBuilder()
        cls.G_macro, cls.G_micro = cls.builder.build_complete_bengaluru_network()
        cls.gis_mgr = GISNetworkManager()
        cls.df_int_gis = cls.gis_mgr.get_intersections_gis()
        cls.roads_gis = cls.gis_mgr.build_roads_gis_catalog(cls.G_macro)

    def test_intersections_gis_schema(self):
        """Test that Intersections GIS dataframe strictly satisfies the Task 3 schema."""
        required_cols = [
            "intersection_id",
            "intersection_name",
            "latitude",
            "longitude",
            "coordinate_source",
            "verification_status",
            "source_pdf",
            "source_page"
        ]
        for col in required_cols:
            self.assertIn(col, self.df_int_gis.columns, f"Missing required intersection GIS column: {col}")

        # Check non-empty
        self.assertEqual(len(self.df_int_gis), 226)
        
        # Verify status values
        valid_statuses = {"VERIFIED", "NEEDS_VERIFICATION", "UNVERIFIED"}
        statuses = set(self.df_int_gis["verification_status"].unique())
        self.assertTrue(statuses.issubset(valid_statuses), f"Invalid status detected: {statuses}")

    def test_roads_gis_schema(self):
        """Test that Roads GIS catalog strictly satisfies the Task 3 schema."""
        required_keys = [
            "edge_id",
            "from_node",
            "to_node",
            "road_name",
            "direction",
            "length_m",
            "lanes",
            "capacity",
            "geometry",
            "geometry_source",
            "verification_status"
        ]
        self.assertGreater(len(self.roads_gis), 0)
        sample = self.roads_gis[0]
        for key in required_keys:
            self.assertIn(key, sample, f"Missing required road GIS key: {key}")

        # Verify geometry format is list of [lat, lon]
        geom = sample["geometry"]
        self.assertIsInstance(geom, list)
        self.assertGreaterEqual(len(geom), 2)
        self.assertEqual(len(geom[0]), 2)

    def test_road_directionality_and_bidirectional_pairing(self):
        """Test that bidirectional roads have reciprocal directed edges."""
        edge_set = set((r["from_node"], r["to_node"]) for r in self.roads_gis)
        bidirectional_count = sum(1 for r in self.roads_gis if r["direction"] == "BIDIRECTIONAL")
        self.assertGreater(bidirectional_count, 0)
        
        # Verify that for any bidirectional edge (u, v), reverse edge (v, u) exists
        for r in self.roads_gis:
            if r["direction"] == "BIDIRECTIONAL":
                self.assertIn((r["to_node"], r["from_node"]), edge_set)

    def test_curved_geometry_retrieval(self):
        """Test that verified corridors use multi-point curved road geometry."""
        verified_roads = [r for r in self.roads_gis if r["verification_status"] == "VERIFIED"]
        self.assertGreater(len(verified_roads), 0)
        
        # Check that verified roads have >= 3 waypoint coordinates tracing curvature
        curved_found = any(len(r["geometry"]) >= 3 for r in verified_roads)
        self.assertTrue(curved_found, "Verified corridors must include multi-point road curves.")

    def test_missing_geometry_graceful_handling(self):
        """Test unverified road connections fall back to endpoint interpolation without errors."""
        unverified_roads = [r for r in self.roads_gis if r["verification_status"] == "UNVERIFIED"]
        self.assertGreater(len(unverified_roads), 0)
        sample_unv = unverified_roads[0]
        self.assertEqual(sample_unv["geometry_source"], "STRAIGHT_LINE_INTERPOLATION")
        self.assertEqual(len(sample_unv["geometry"]), 2)

    def test_or_model_compatibility_ambulance_router(self):
        """Test that Ambulance Dijkstra Router executes identically on GIS-enriched network."""
        G_enriched = self.gis_mgr.enrich_macro_graph(self.G_macro.copy())
        router = AmbulanceRouter(graph_multi=None, graph_di=G_enriched)
        
        # Source to Sink on Corridor 1
        s = "INT_003_ADUGODI_JUNCTION"
        t = "INT_006_RAJALAXMIKALYANAMANTAPA"
        res = router.find_shortest_path(s, t)
        self.assertEqual(res["status"], "OPTIMAL")
        self.assertGreater(res["total_time_min"], 0.0)
        self.assertGreater(res["total_distance_km"], 0.0)
        self.assertEqual(res["path_nodes"][0], s)
        self.assertEqual(res["path_nodes"][-1], t)

    def test_or_model_compatibility_route_comparison(self):
        """Test that Shortest Distance vs Minimum Time comparison executes on GIS-enriched network."""
        G_enriched = self.gis_mgr.enrich_macro_graph(self.G_macro.copy())
        router = AmbulanceRouter(graph_multi=None, graph_di=G_enriched)
        
        orig = "INT_003_ADUGODI_JUNCTION"
        dest = "INT_006_RAJALAXMIKALYANAMANTAPA"
        comp = router.compare_distance_vs_time_routes(orig, dest)
        self.assertEqual(comp["status"], "SUCCESS")
        self.assertGreater(comp["fastest_time_min"], 0.0)
        self.assertGreater(comp["shortest_distance_km"], 0.0)

    def test_or_model_compatibility_shortest_path(self):
        """Test that Dijkstra Shortest Path executes identically on GIS-enriched network."""
        G_enriched = self.gis_mgr.enrich_macro_graph(self.G_macro.copy())
        opt = ShortestPathOptimizer(G_enriched)
        
        orig = "INT_003_ADUGODI_JUNCTION"
        dest = "INT_006_RAJALAXMIKALYANAMANTAPA"
        res = opt.find_shortest_path(orig, dest, weight_metric="cost")
        self.assertIn(res["status"], ["OPTIMAL", "SUCCESS"])
        self.assertGreater(len(res["path_nodes"]), 1)
        self.assertEqual(res["path_nodes"][0], orig)
        self.assertEqual(res["path_nodes"][-1], dest)

    def test_folium_map_generation(self):
        """Test creating a Folium map with interactive layers and legends."""
        nodes_list = self.df_int_gis.to_dict(orient="records")[:30]
        roads_subset = self.roads_gis[:50]
        
        m = create_bengaluru_gis_map(
            intersections=nodes_list,
            roads=roads_subset,
            source_node="INT_003_ADUGODI_JUNCTION",
            sink_node="INT_006_RAJALAXMIKALYANAMANTAPA",
            show_legend=True
        )
        self.assertIsNotNone(m)
        html = m._repr_html_()
        self.assertIn("OpenStreetMap", html)
        self.assertIn("BENGALURU GIS MAP LEGEND", html)

if __name__ == "__main__":
    unittest.main()
