"""
Dependency Diagnostic & Environment Checker.
Ambulance Route Optimization — Bengaluru.

Verifies critical GIS, mathematical, and cartographic packages in the currently
active Python runtime and provides precise environment telemetry and remediation commands.
"""

import sys
import os
import importlib
import importlib.metadata as importlib_metadata
from typing import Dict, List, Tuple, Any
import streamlit as st

# Required GIS and OR packages with their import names vs pip package names
CORE_GIS_PACKAGES = [
    ("folium", "folium", "Interactive OpenStreetMap & Leaflet rendering"),
    ("streamlit_folium", "streamlit-folium", "Bi-directional Folium integration in Streamlit"),
    ("geopandas", "geopandas", "Geospatial vector geometry & spatial queries"),
    ("osmnx", "osmnx", "OpenStreetMap road network retrieval & topology"),
    ("networkx", "networkx", "Graph algorithms & Dijkstra shortest-path engine"),
    ("scipy", "scipy", "Scientific optimization & distance matrices"),
    ("plotly", "plotly", "Interactive performance & speed analytics charts")
]

def audit_runtime_dependencies() -> Dict[str, Any]:
    """
    Audits the currently active Python interpreter for required packages.
    Returns status dictionary with version details and exact install command if missing.
    """
    installed = {}
    missing = []
    
    for import_name, pip_name, description in CORE_GIS_PACKAGES:
        try:
            mod = importlib.import_module(import_name)
            # Retrieve version safely
            version = "Installed"
            if hasattr(mod, "__version__"):
                version = str(mod.__version__)
            else:
                try:
                    version = importlib_metadata.version(pip_name)
                except Exception:
                    version = "Active"
            installed[pip_name] = {
                "version": version,
                "description": description,
                "status": "OK"
            }
        except ImportError:
            missing.append({
                "import_name": import_name,
                "pip_name": pip_name,
                "description": description
            })
            
    python_exe = sys.executable
    is_satisfied = len(missing) == 0
    
    missing_pip_names = [m["pip_name"] for m in missing]
    install_cmd = f'"{python_exe}" -m pip install ' + " ".join(missing_pip_names)
    
    return {
        "is_satisfied": is_satisfied,
        "missing": missing,
        "missing_names": missing_pip_names,
        "installed": installed,
        "python_executable": python_exe,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "install_command": install_cmd
    }

def render_dependency_diagnostic(expanded_if_missing: bool = True):
    """
    Renders an informative diagnostic banner in the Streamlit UI.
    If dependencies are missing, displays the active interpreter path and copy-paste install command.
    If all dependencies are present, renders a subtle green verification badge.
    """
    diag = audit_runtime_dependencies()
    
    if not diag["is_satisfied"]:
        st.error(f"""
        ### ⚠️ Missing GIS & Optimization Dependencies
        
        The currently active Python environment is missing critical GIS routing packages.
        
        - **Active Python Interpreter:** `{diag['python_executable']}`
        - **Python Version:** `{diag['python_version']}`
        - **Missing Packages:** {", ".join([f"`{m['pip_name']}`" for m in diag['missing']])}
        
        #### Recommended Remediation:
        Run the following command in your terminal targeting the exact active interpreter:
        ```bash
        {diag['install_command']}
        ```
        Or install the complete project manifest:
        ```bash
        "{diag['python_executable']}" -m pip install -r requirements.txt
        ```
        """)
    return diag
