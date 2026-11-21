# BENGALURU SIGNAL-AWARE ROUTING & ROUTE COMPARISON REPORT
## Phase 4 — Dijkstra Solver Integration & 10-Corridor Empirical Experiment
**Project:** Ambulance Route Optimization — Bengaluru, Karnataka, India  
**Date:** November 2026  
**Status:** Completed & Validated (100% Local Development)  

---

## 1. Executive Summary

This report documents the integration of verified traffic signal delays into the core Dijkstra shortest path optimization engine, and details the empirical findings from the **10-Corridor Route Comparison Experiment** comparing:
- **Scenario A:** Minimum estimated road travel time without signal delays (`PROFILE_MINIMUM_TIME`).
- **Scenario B:** Minimum estimated travel time with applicable Webster signal delays (`PROFILE_TIME_PLUS_SIGNAL`).

In **7 out of 10 corridors (70.0%)**, the signal-aware routing engine intelligently diverged to bypass high-delay signalized bottlenecks, saving up to **4.17 minutes (11.8% journey time reduction)** while adding minimal physical distance.

---

## 2. Solver Edge Weight Integration (Task 7)

The directed graph $G = (V, E)$ consists of $|V| = 226$ signalized intersections and $|E| = 1,164$ directed road links.

For each directed edge $e = (u, v) \in E$:
1. $u$ is the upstream node; $v$ is the target signalized junction.
2. The vehicle traverses road segment $(u, v)$ with length $L_e$ and IRC:106 regulated speed $v_e$, incurring baseline road travel time:
   $$t_{\text{travel}, e} = \frac{L_e}{v_e} \times 3600 \text{ seconds}$$
3. As the vehicle reaches node $v$, it approaches along approach arm $A_e$, which is governed by signal phase $P_e$.
4. The signal delay model assigns Webster uniform delay $d_{\text{signal}, e} \ge 0$.
5. The combined edge weight is strictly positive:
   $$t_{\text{edge}, e} = t_{\text{travel}, e} + d_{\text{signal}, e} \ge t_{\text{travel}, e} > 0$$

### Three Independent Routing Profiles Supported:
1. `PROFILE_SHORTEST_DISTANCE`: Minimizes $\sum L_e$ (meters).
2. `PROFILE_MINIMUM_TIME`: Minimizes $\sum t_{\text{travel}, e}$ (free-flow road seconds).
3. `PROFILE_TIME_PLUS_SIGNAL`: Minimizes $\sum (t_{\text{travel}, e} + d_{\text{signal}, e})$ (signal-aware seconds).

---

## 3. Systematic 10-Corridor Route Comparison Experiment (Task 8)

The experiment evaluated 10 canonical emergency origin-destination corridors across Greater Bengaluru during morning peak operations (`WEEKDAY_MORNING_PEAK`):

| # | Corridor & OD Pair | Baseline Dist (km) | Baseline Time (min) | Baseline Signal Delay | Total Baseline Journey Time | Signal-Aware Dist (km) | Signal-Aware Time (min) | Divergent? | Divergence Junction | Net Time Delta |
| :-: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| **1** | **Mysore Rd &rarr; Adugodi Central** | 9.026 | 13.54 | 4.85 min | 18.39 min | 9.031 | 17.36 min | **Yes** | PRASANNA JUNCTION | **-1.03 min (-5.6%)** |
| **2** | **South-West &rarr; Anandrao Circle** | 7.328 | 10.99 | 3.36 min | 14.35 min | 7.328 | 14.35 min | **No** | None (Identical) | **0.00 min (0.0%)** |
| **3** | **City Center &rarr; Indiranagar** | 7.152 | 10.01 | 8.53 min | 18.54 min | 7.157 | 16.65 min | **Yes** | LALBAGH WEST GATE | **-1.89 min (-10.2%)** |
| **4** | **Magadi Rd &rarr; Adugodi** | 2.264 | 3.40 | 3.88 min | 7.28 min | 2.269 | 6.25 min | **Yes** | PRASANNA JUNCTION | **-1.03 min (-14.1%)** |
| **5** | **Adugodi West &rarr; Kimco Mysore Rd** | 8.698 | 14.41 | 2.20 min | 16.61 min | 8.698 | 16.58 min | **Yes** | PUTTANNA JUNCTION | **-0.03 min (-0.2%)** |
| **6** | **Sony World &rarr; City Center** | 7.761 | 11.72 | 8.25 min | 19.97 min | 7.797 | 17.46 min | **Yes** | TOWNHALL JUNCTION | **-2.51 min (-12.6%)** |
| **7** | **Sony World &rarr; Old Madras Rd** | 1.237 | 1.86 | 0.72 min | 2.58 min | 1.237 | 2.58 min | **No** | None (Identical) | **0.00 min (0.0%)** |
| **8** | **Kengeri &rarr; Anandrao Circle** | 8.472 | 12.71 | 3.81 min | 16.52 min | 8.472 | 16.52 min | **No** | None (Identical) | **0.00 min (0.0%)** |
| **9** | **Satellite Bus Stand &rarr; South-Central** | 10.797 | 16.20 | 6.40 min | 22.60 min | 11.053 | 21.20 min | **Yes** | SATELLITE BUS STAND | **-1.40 min (-6.2%)** |
| **10** | **Mysore Rd &rarr; Sony World Koramangala** | 15.160 | 22.82 | 12.65 min | 35.47 min | 15.165 | 31.30 min | **Yes** | PRASANNA JUNCTION | **-4.17 min (-11.8%)** |

### Complete Experiment Dataset:
- [`data/processed/signal_route_comparison_results.csv`](file:///b:/Ambulance%20Route%20Optimization/data/processed/signal_route_comparison_results.csv)

---

## 4. Key Behavioral Findings & Insights

1. **The Signal Delay Trade-Off Phenomenon:**
   In Corridor 10 (Mysore Road Industrial to Sony World Koramangala):
   - **Baseline Scenario A** chose the corridor with the absolute lowest road travel time (22.82 min), but encountered **15 signalized intersections** with heavy red times totaling **12.65 minutes** of signal delay, producing a total journey time of **35.47 minutes**.
   - **Signal-Aware Scenario B** diverged at **Prasanna Junction**, adding a mere **5 meters (+0.005 km)** of road length and **0.01 min** of road travel time, but completely bypassed two severe 90-second red-phase intersections. This slashed signal delay from **12.65 min down to 8.46 min**, reducing the overall ambulance transit time to **31.30 minutes** (saving **4.17 minutes**).

2. **Corridor Convergence (Zero Divergence):**
   In Corridors 2, 7, and 8, the physical arterial geometry between the origin and destination offers no viable alternative parallel corridors without imposing extreme geometric detours. In such cases, the signal-aware route naturally converges to the baseline trajectory while accurately reporting the expected signal delay component.

3. **Academic Disclaimer:**
   These findings demonstrate mathematical optimality under fixed-time uniform delay. In live urban operations, physical queues, non-uniform vehicle platooning, and sudden intersection blockages require real-time empirical validation before operational deployment.
