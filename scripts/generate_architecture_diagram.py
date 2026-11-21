"""
generate_architecture_diagram.py
Generates a professional, high-resolution System Architecture diagram for the
Ambulance Route Optimization Academic Project Report.
Uses Pillow to produce a clean, publication-grade diagram at 1800 x 1150 px.
"""

import os
from PIL import Image, ImageDraw, ImageFont

def create_system_architecture_diagram(output_path="assets/diagrams/system_architecture.png"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Canvas dimensions
    width = 1800
    height = 1150
    
    # Palette (Light Medical / Clinical GIS)
    bg_color = "#FFFFFF"
    card_bg = "#F8FAFC"
    border_color = "#CBD5E1"
    primary_color = "#0284C7"      # Medical Blue
    text_dark = "#0F172A"          # Navy / Slate
    text_muted = "#475569"         # Slate Grey
    accent_green = "#16A34A"       # Emerald / Success
    accent_amber = "#D97706"       # Amber / Warning
    accent_purple = "#7C3AED"      # Purple / Alternative
    
    im = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(im)
    
    # Fonts
    font_title = ImageFont.truetype("arialbd.ttf", 30)
    font_sub = ImageFont.truetype("arial.ttf", 16)
    font_tier = ImageFont.truetype("arialbd.ttf", 18)
    font_box_title = ImageFont.truetype("arialbd.ttf", 15)
    font_box_body = ImageFont.truetype("arial.ttf", 12)
    font_arrow = ImageFont.truetype("arialbd.ttf", 12)
    
    # Title Header Block
    draw.text((width // 2, 45), "BENGALURU AMBULANCE ROUTE OPTIMIZATION SYSTEM", fill=text_dark, font=font_title, anchor="mm")
    draw.text((width // 2, 75), "Operations Research Architecture: Data Integration, Graph Formulation, Dijkstra Solver & GIS Presentation", fill=text_muted, font=font_sub, anchor="mm")
    draw.line([(60, 95), (width - 60, 95)], fill="#E2E8F0", width=2)
    
    # Tiers setup: 5 horizontal bands
    tiers = [
        {
            "name": "TIER 1: DATA SOURCES & PROVENANCE",
            "y": 115, "h": 140, "color": "#0284C7",
            "boxes": [
                {"title": "OpenStreetMap Bengaluru", "lines": ["• Arterial road geometry", "• One-way & speed limits", "• PBF / XML vector feeds"], "color": "#0284C7"},
                {"title": "BTP Signal Drawings (118 PDFs)", "lines": ["• 114 CAD vector sheets", "• 4 Scanned raster sheets", "• Phase splits & cycle time"], "color": "#0284C7"},
                {"title": "Healthcare GIS Facilities", "lines": ["• 1,084 Raw OSM facilities", "• 103 Verified Level-1 Trauma", "• Emergency attributes"], "color": "#0284C7"},
                {"title": "BTP Traffic & Congestion Data", "lines": ["• Arterial volume/capacity", "• Historical peak speeds", "• Congestion tier profiles"], "color": "#0284C7"}
            ]
        },
        {
            "name": "TIER 2: PREPROCESSING, DELAY MODELING & SNAPPING",
            "y": 305, "h": 145, "color": "#D97706",
            "boxes": [
                {"title": "PDF Table Extractor & OCR", "lines": ["• pdfplumber tabular parser", "• Tesseract fallback pipeline", "• 259 Timing tables / 5,362 rows"], "color": "#D97706"},
                {"title": "Webster Signal Delay Engine", "lines": ["• Uniform delay approximation", "• d = R² / (2C) per movement", "• Finite edge penalty synthesis"], "color": "#D97706"},
                {"title": "Hospital Snapping Engine", "lines": ["• Haversine & orthogonal snap", "• 5000 m boundary limit", "• Nearest road edge injection"], "color": "#D97706"},
                {"title": "BPR Congestion Calibrator", "lines": ["• Volume-delay formulation", "• t = t₀ [1 + α(v/c)β]", "• α = 0.20, β = 4.0 (Indian arterials)"], "color": "#D97706"}
            ]
        },
        {
            "name": "TIER 3: NETWORK GRAPH CONSTRUCTION & TOPOLOGY",
            "y": 500, "h": 140, "color": "#16A34A",
            "boxes": [
                {"title": "Directed MultiDiGraph Builder", "lines": ["• 226 Signalized Intersections", "• 1,164 Directed Road Edges", "• 808.25 km Arterial Span"], "color": "#16A34A"},
                {"title": "Topological Validator", "lines": ["• Strongly connected: 1 component", "• One-way compliance checks", "• Turn-restriction enforcement"], "color": "#16A34A"},
                {"title": "Cost Metric Profiles", "lines": ["• Free-Flow / Distance (m)", "• BPR Congested Time (sec)", "• Combined Signal + Traffic (sec)"], "color": "#16A34A"}
            ]
        },
        {
            "name": "TIER 4: OPERATIONS RESEARCH ROUTING CORE",
            "y": 690, "h": 145, "color": "#7C3AED",
            "boxes": [
                {"title": "Priority-Queue Dijkstra Solver", "lines": ["• Min-heap implementation", "• O((|E| + |V|) log |V|) efficiency", "• Minimum travel time path P*"], "color": "#7C3AED"},
                {"title": "Yen's K-Shortest Paths Engine", "lines": ["• Loopless candidate generation", "• Spur-node & spur-path search", "• Detour factor % evaluation"], "color": "#7C3AED"},
                {"title": "Hospital Facility Selector", "lines": ["• Emergency eligibility filter", "• Dynamic multi-hospital ranking", "• Closest trauma unit matching"], "color": "#7C3AED"}
            ]
        },
        {
            "name": "TIER 5: PRESENTATION, GIS CARTOGRAPHY & ANALYTICS",
            "y": 885, "h": 145, "color": "#0284C7",
            "boxes": [
                {"title": "Streamlit Multi-Page Web App", "lines": ["• 8 Specialized sub-pages", "• Real-time parameter controls", "• Light Medical Clinical Theme"], "color": "#0284C7"},
                {"title": "Interactive Leaflet / Folium GIS", "lines": ["• Multi-tier fallback renderer", "• Route & signal polyline overlays", "• Hospital & junction telemetry"], "color": "#0284C7"},
                {"title": "Evaluation & Analytics Engine", "lines": ["• Scenario benchmarking suite", "• Signal vs baseline comparison", "• Plotly clinical metric panels"], "color": "#0284C7"}
            ]
        }
    ]
    
    # Helper to draw rounded box
    def draw_card(x1, y1, x2, y2, title, lines, accent_col):
        # Card body
        draw.rounded_rectangle([x1, y1, x2, y2], radius=8, fill="#FFFFFF", outline=border_color, width=2)
        # Top accent bar
        draw.rounded_rectangle([x1, y1, x2, y1 + 6], radius=3, fill=accent_col)
        # Title
        draw.text((x1 + 14, y1 + 18), title, fill=text_dark, font=font_box_title)
        # Content lines
        y_text = y1 + 46
        for line in lines:
            draw.text((x1 + 14, y_text), line, fill=text_muted, font=font_box_body)
            y_text += 20

    # Draw each tier
    for t_idx, tier in enumerate(tiers):
        ty = tier["y"]
        th = tier["h"]
        
        # Tier background strip
        draw.rounded_rectangle([40, ty, width - 40, ty + th], radius=10, fill=card_bg, outline="#E2E8F0", width=1)
        
        # Tier label banner
        draw.text((60, ty + 12), tier["name"], fill=tier["color"], font=font_tier)
        
        # Boxes layout
        boxes = tier["boxes"]
        n_boxes = len(boxes)
        avail_w = width - 120
        gap = 20
        box_w = (avail_w - (n_boxes - 1) * gap) // n_boxes
        
        for b_idx, box in enumerate(boxes):
            bx1 = 60 + b_idx * (box_w + gap)
            by1 = ty + 38
            bx2 = bx1 + box_w
            by2 = ty + th - 12
            draw_card(bx1, by1, bx2, by2, box["title"], box["lines"], box["color"])
            
        # Draw connecting vertical flow arrows to next tier
        if t_idx < len(tiers) - 1:
            next_ty = tiers[t_idx + 1]["y"]
            arrow_y1 = ty + th
            arrow_y2 = next_ty
            mid_y = (arrow_y1 + arrow_y2) // 2
            
            # Draw 3 vertical downward arrows
            arrow_x_positions = [width * 0.25, width * 0.50, width * 0.75]
            for ax in arrow_x_positions:
                draw.line([(ax, arrow_y1 + 2), (ax, arrow_y2 - 6)], fill="#94A3B8", width=3)
                # Arrowhead
                draw.polygon([(ax - 6, arrow_y2 - 8), (ax + 6, arrow_y2 - 8), (ax, arrow_y2 - 2)], fill="#0284C7")
                
    # Footer caption
    draw.text((width // 2, height - 25), "Figure 1: Complete End-to-End System Architecture of the Bengaluru Ambulance Route Optimization Platform", fill=text_muted, font=font_sub, anchor="mm")
    
    im.save(output_path, "PNG", quality=95)
    print(f"Architecture diagram successfully saved to: {output_path}")

if __name__ == "__main__":
    create_system_architecture_diagram()
