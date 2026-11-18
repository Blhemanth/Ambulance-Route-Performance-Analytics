# Bengaluru Smart Traffic Optimizer
## Traffic Signal Optimization Using Combined Network Models – Operations Research

---

## Academic Focus: Operations Research & Network Optimization
**Bengaluru Smart Traffic Optimizer** is a rigorous, mathematically validated Operations Research framework designed to optimize traffic flow, minimize transportation costs, identify arterial bottlenecks, and calculate optimal signal phase allocations across Greater Bengaluru's interconnected road network.

The central academic pillar is **NETWORK MODELS**. The system integrates four classical and modern OR formulations:
1. **Model 1: Maximum Flow** (Primal LP, Ford-Fulkerson / Dinic, Max-Flow Min-Cut bottleneck identification).
2. **Model 2: Minimum Cost Flow** (Network Simplex / LP formulation with strict node balance equations).
3. **Model 3: Shortest Path** (Dijkstra algorithm over dynamic signalized impedance functions).
4. **Model 4: Signal Timing Linear Programming** (Queue-balancing LP bounded by safety, cycle lengths, and pedestrian intervals).

These models are **interconnected via a mathematical feedback loop**: optimal signal splits modify downstream effective link capacities and travel times, which dynamically update network flows and shortest paths.

---

## System Architecture

```
bengaluru-smart-traffic-optimizer/
├── dataset/                     # 118 Original Bengaluru Traffic Signal PDFs
├── data/
│   ├── raw/                     # Cached extraction raw payloads
│   ├── processed/               # Extracted relational CSV datasets
│   │   ├── intersections.csv
│   │   ├── roads.csv
│   │   ├── signal_phases.csv
│   │   ├── signal_timings.csv
│   │   └── extraction_errors.csv
│   ├── validated/               # Mathematically certified network matrices
│   └── synthetic/               # Labelled benchmark traffic demand profiles
├── src/
│   ├── data_processing/         # PDF extraction, CAD text cleaning, table parsing
│   │   ├── pdf_extractor.py
│   │   ├── table_extractor.py
│   │   ├── ocr_processor.py
│   │   ├── data_cleaner.py
│   │   ├── data_validator.py
│   │   └── dataset_exporter.py
│   ├── network/                 # Network models & graph builder
│   │   ├── graph_builder.py
│   │   ├── maximum_flow.py
│   │   ├── minimum_cost_flow.py
│   │   ├── shortest_path.py
│   │   └── network_analyzer.py
│   ├── optimization/           # OR mathematical solvers
│   │   ├── linear_programming.py
│   │   ├── signal_optimizer.py
│   │   ├── constraints.py
│   │   ├── objective_functions.py
│   │   └── sensitivity_analysis.py
│   ├── simulation/              # Microscopic traffic simulation (SUMO & analytical)
│   ├── analytics/               # Scenario comparisons and reporting
│   └── database/                # Relational querying & persistence
├── pages/                       # 10 Professional Streamlit Multi-page App Views
├── components/                  # Custom UI elements, network visualizers, stats cards
├── assets/                      # Maps, diagrams, custom dark CSS stylesheets
├── tests/                       # Unit, integration, and mathematical test suites
├── reports/                     # Generated experimental and validation summaries
├── app.py                       # Main Streamlit intelligent traffic control interface
├── requirements.txt             # Project dependencies
├── PROJECT_DEVELOPMENT_LOG.md   # Continuous engineering diary
├── MATHEMATICAL_MODEL.md        # Comprehensive OR mathematical formulations
├── NETWORK_MODEL_DOCUMENTATION.md # Graph architecture and corridor topology
├── DATASET_DOCUMENTATION.md     # Data dictionary, CAD anomalies, extraction rules
├── TESTING_REPORT.md            # Test logs and validation records
└── EXPERIMENTAL_RESULTS.md      # Benchmark metrics for Scenarios A, B, and C
```

---

## Dataset Inventory
- **118 original PDF signal design plans** from Bharat Electronics Limited (BEL) and Bengaluru Traffic Police (BTP).
- Covers 259+ signal timing plans across major police stations: Adugodi, Ashok Nagar, Banashankari, Byatarayanapura, Frazer Town, Hebbal, High Grounds, Indiranagar, Jayanagar, K.S. Layout, Kamakshipalya, Mico Layout, Peenya, Rajajinagar, Ulsoor, Wilson Garden, Yelahanka.
- 114 Digital Vector CAD sheets + 4 Scanned sheets (3 unique intersections + 1 duplicate) with 100% data extraction and verification.

---

## Installation & Setup

```bash
# Clone or navigate to the workspace
cd "b:\operational research project"

# Install dependencies in Python 3.13
python -m pip install -r requirements.txt

# Run unit tests
python -m unittest discover tests

# Launch the Intelligent Urban Traffic Control Web Application
streamlit run app.py
```

---

## Web Application Theme & Aesthetic
- **Theme**: Intelligent Urban Traffic Control (Professional dark smart-city aesthetic).
- **Color Palette**:
  - Primary Background: `#0B1220`
  - Secondary Background: `#172235`
  - Traffic Green: `#22C55E`
  - Traffic Amber: `#F59E0B`
  - Traffic Red: `#EF4444`
  - Network Cyan: `#06B6D4`
  - Text: `#F1F5F9`


---

## Operations Research Multi-Page Application Views

Launch the application using:
```bash
streamlit run app.py
```

The application provides 10 dedicated multi-page views:
1. **01 Overview** (`pages/1_Overview.py`): High-level system KPIs, corpus breakdown (114 vector CAD vs 4 scanned drawings), Time-of-Day schedules, and data provenance classifications.
2. **02 Dataset Explorer** (`pages/2_Dataset_Explorer.py`): Searchable and filterable tables for 226 geocoded intersections, 652 road links, 879 signal phases, 5,362 timing records, and interactive manual plan correction.
3. **03 Network Visualization** (`pages/3_Network_Visualization.py`): Interactive Plotly dual-level graph explorer for Level 1 Macro corridors and Level 2 Micro turning movement rights, with betweenness and degree centrality rankings.
4. **04 Model 1: Maximum Flow** (`pages/4_Maximum_Flow.py`): Solves source-to-sink maximum vehicular throughput $F^*$, verifies the Ford-Fulkerson Max-Flow Min-Cut Theorem, and highlights saturated bottleneck cut edges in red.
5. **05 Model 2: Minimum Cost Flow** (`pages/5_Minimum_Cost_Flow.py`): Formulates and solves the network simplex mass-balance transshipment problem minimizing total vehicular delay, identifying road links exceeding $85\%$ capacity.
6. **06 Model 3: Shortest Path** (`pages/6_Shortest_Path.py`): Dijkstra algorithm computing minimum-impedance routes between intersections, providing turn-by-turn itineraries and comparing baseline vs. signal-optimized travel times.
7. **07 Model 4: Signal Timing Optimization** (`pages/7_Signal_Optimization.py`): Exact queue-minimizing Linear Program via SciPy HiGHS simplex/interior-point, subject to cycle conservation $\sum g_p + L = C$ and Webster delay analysis.
8. **08 Dynamic Simulation Centre** (`pages/8_Simulation_Centre.py`): Comparative dynamic meso-queue simulation tracking queue progression over time, waiting times, and throughput under equal stochastic demand.
9. **09 Analytics & Sensitivity Testing** (`pages/9_Analytics.py`): Full comparative benchmark matrix across Scenarios A, B, and C, with sensitivity curves (+10% to +30%) and bottleneck migration tracking.
10. **10 Operations Research Methodology** (`pages/10_Methodology.py`): Complete academic derivations, primal-dual mathematical formulations, total unimodularity, Webster formulas, coupling proofs, and scholarly citations.

---

## Test Verification
Run all 23 automated unit and integration tests:
```bash
python -m unittest discover tests
```
*Current Status: 23/23 tests passing (100% pass rate in 7.88s).*
