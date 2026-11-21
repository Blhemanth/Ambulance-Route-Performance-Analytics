# Contributing to Ambulance Route Optimization

Thank you for your interest in contributing to the **Ambulance Route Optimization** platform! This document provides instructions for setting up a local development environment, executing the test suite, and adhering to architectural guidelines.

---

## 1. Prerequisites

- **Python**: Supported versions are **Python 3.9** through **Python 3.13** (64-bit).
- **Git**: Installed and available in your system `PATH`.
- **Operating System**: Cross-platform (Windows 10/11, Ubuntu 20.04+, or macOS 12+).

---

## 2. Local Development Setup

### 2.1 Clone the Repository
```bash
git clone https://github.com/Blhemanth/Ambulance-Route-Performance-Analytics.git
cd Ambulance-Route-Performance-Analytics
```

### 2.2 Create a Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2.3 Install Dependencies
Upgrade `pip` and install all required runtime, GIS, and testing dependencies:
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## 3. Running the Application Locally

Launch the Streamlit multi-page platform from the project root:
```bash
python -m streamlit run app.py
```
By default, the server initializes at `http://localhost:8501`.

---

## 4. Running the Automated Test Suite

Before submitting any code changes, ensure that all 98 unit tests pass cleanly:
```bash
python -m unittest discover -s tests -p "test_*.py"
```
The test suite validates:
- Graph construction and one-way link enforcement.
- Priority-Queue Dijkstra solver correctness and travel-time non-negativity.
- Yen's K-shortest loopless paths algorithm and detour factor metrics.
- Webster uniform signal delay computations.
- Bureau of Public Roads (BPR) volume-delay calibration functions.
- Hospital deduplication and geometric network snapping.
- Resilient Leaflet/Folium GIS map rendering pipelines.

---

## 5. Architectural & Code Contribution Guidelines

1. **Operations Research Integrity**:
   - Do not alter mathematical cost formulations, edge weight models, or graph data structures without providing formal academic references and comprehensive unit test verification.
   - All edge weights $w_{ij}$ must remain strictly positive ($w_{ij} > 0$) to preserve Dijkstra's optimality guarantee.

2. **Data & Privacy Protection**:
   - Never commit large raw `.osm.pbf` files to Git (they exceed GitHub's 100 MB file limit). Ensure they remain covered under `.gitignore`.
   - Never hardcode absolute system paths (e.g., `C:\Users\...` or `/home/...`); always utilize dynamic path resolution via `pathlib.Path` or `os.path`.

3. **GIS & UI Standards**:
   - All UI additions must adhere to the **Light Medical / Clinical GIS** theme:
     - Background: `#F8FAFC`
     - Cards and Panels: `#FFFFFF`
     - Primary Accent: `#0284C7` (Medical Blue)
     - Primary Typography: `#0F172A` (Navy / Slate)
     - Borders & Dividers: `#CBD5E1` / `#E2E8F0`

4. **Testing Requirements**:
   - Any new feature, algorithm, or utility module must include corresponding unit tests in `tests/test_*.py`.
   - 100% test pass rate is required for all contributions.

---

## 6. Pull Request Workflow

1. Fork the repository and create a descriptive feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Commit your changes with concise, standardized commit messages:
   ```bash
   git commit -m "feat(routing): add dynamic turn-penalty heuristic to Dijkstra solver"
   ```
3. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
4. Open a Pull Request against the `main` branch with a clear description of the problem solved, methodology, and test verification results.
