# GIS DEPENDENCY & ENVIRONMENT RESOLUTION REPORT
**Project:** Ambulance Route Optimization (Bengaluru, Karnataka)  
**Date:** 2026-11-21  
**Author:** Senior Python & Streamlit Application Systems Engineer  
**Status:** FULLY RESOLVED, TESTED & VERIFIED ACROSS ALL RUNTIMES  

---

## 1. Executive Summary & Root Cause Analysis

### The Reported Issue
The application intermittently displayed the warning:
```
Interactive GIS Map Component Disabled – folium is not installed in the currently active Python environment.
```

### Root Cause 1: Multi-Python PATH Resolution Collision on Windows
The Windows workstation hosts two concurrent Python installations:
1. **Python 3.9 (Microsoft Store):** Located at `C:\Users\heman\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.9_qbz5n2kfra8p0\...`
2. **Python 3.13 (Microsoft Store):** Located at `C:\Users\heman\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\...`

When typing `streamlit run app.py` in PowerShell or Command Prompt, Windows PATH prioritized the Python 3.9 `Scripts` directory:
```
C:\...\Python39\Scripts\streamlit.cmd
C:\...\Python39\Scripts\streamlit.exe
C:\...\Python313\Scripts\streamlit.exe
```
Consequently, terminal launches of `streamlit` executed under **Python 3.9**, which initially lacked `folium`, `geopandas`, and `osmnx`.

### Root Cause 2: Incomplete Dependency Manifest
`requirements.txt` previously contained core mathematical libraries (`networkx`, `scipy`, `pulp`, `pandas`, `numpy`, `plotly`, `streamlit`) but **completely omitted** the interactive GIS cartography stack (`folium`, `streamlit-folium`, `geopandas`, `osmnx`, `shapely`, `pyproj`, `pyogrio`). No `pyproject.toml` existed.

### Root Cause 3: Overly Broad Fallback Logic in `components/gis_map.py`
In `render_gis_map_in_streamlit()`, line 452 formerly evaluated:
```python
if not HAS_FOLIUM or m is None:
    st.warning("folium is not installed in the currently active Python environment.")
```
If `m` was `None` (for instance, during initial component mounting or boundary checks), the component falsely claimed `folium` was uninstalled even when `folium` was present. Furthermore, if `streamlit-folium` had bridging issues, the component previously halted rather than falling back to Folium's native Leaflet HTML renderer.

---

## 2. Technical Modifications & Implemented Solutions

### 2.1 Manifest Modernization (`requirements.txt` & `pyproject.toml`)
Updated [`requirements.txt`](file:///B:/Ambulance%20Route%20Optimization/requirements.txt) and authored a standard [`pyproject.toml`](file:///B:/Ambulance%20Route%20Optimization/pyproject.toml) declaring all required GIS packages:
- `folium>=0.17.0`
- `streamlit-folium>=0.20.0`
- `geopandas>=1.0.0`
- `osmnx>=2.0.0`
- `networkx>=3.2.1`
- `shapely>=2.0.0`
- `pyproj>=3.6.0`
- `pyogrio>=0.7.0`

### 2.2 Dual-Environment Package Synchronization
Installed and verified identical packages across both active environments:
- **Python 3.9 Environment:**
  - `folium == 0.20.0`
  - `streamlit-folium == 0.25.3`
  - `geopandas == 1.0.1`
  - `osmnx == 2.0.7`
  - `networkx == 3.2.1`
- **Python 3.13 Environment:**
  - `folium == 1.0.0`
  - `streamlit-folium == 0.27.4`
  - `geopandas == 1.2.0`
  - `osmnx == 2.2.0`
  - `networkx == 3.7`

### 2.3 Startup Dependency Diagnostic Module (`components/dependency_checker.py`)
Created an automated environment auditor that inspects the active runtime at startup:
- Dynamically queries `sys.executable` and `sys.version`.
- Audits import availability for `folium`, `streamlit_folium`, `geopandas`, `osmnx`, and `networkx`.
- If any package is missing, renders a diagnostic banner with the **exact terminal remediation command** targeting the active interpreter (`"{sys.executable}" -m pip install ...`).
- Integrated into [`components/ui_helpers.py`](file:///B:/Ambulance%20Route%20Optimization/components/ui_helpers.py#L44).

### 2.4 Multi-Tier Resilient GIS Map Renderer (`components/gis_map.py`)
Refactored `render_gis_map_in_streamlit()` with a two-tier execution pipeline:
- **Separated Checks:** Decoupled `not HAS_FOLIUM` from `m is None`.
- **Tier 1 (Preferred):** Bi-directional interactive Leaflet widget via `streamlit_folium`.
- **Tier 2 (Resilient Fallback):** Direct Leaflet HTML iframe rendering via `st.components.v1.html(m._repr_html_(), height=height)`.
- **Guarantee:** As long as Folium is present, the interactive map **never disables** even if component bridges encounter transient stream serialization issues.

---

## 3. Verification & Test Results

### 3.1 Direct Python Runtime Verification
```powershell
# Python 3.9 Validation
Py3.9 audit satisfied: True
Py3.9 HAS_FOLIUM: True
Py3.9 HAS_STREAMLIT_FOLIUM: True
Py3.9 Map generated successfully: True

# Python 3.13 Validation
Py3.13 audit satisfied: True
Py3.13 HAS_FOLIUM: True
Py3.13 HAS_STREAMLIT_FOLIUM: True
Py3.13 Map generated successfully: True
```

### 3.2 Automated Unit Test Suite
Ran full test discovery across the test suite:
```
----------------------------------------------------------------------
Ran 98 tests in 32.512s

OK (100% pass rate, zero regressions)
```

### 3.3 Server Execution
- Streamlit application active on `http://localhost:8501`.
- Verified city-wide overview map on the Operations Dashboard (`app.py`), Road Network Explorer (`Page 1`), Hospital Finder (`Page 2`), and Ambulance Route Optimizer (`Page 3`) render full interactive OpenStreetMap & Leaflet tiles with live layer controls.
