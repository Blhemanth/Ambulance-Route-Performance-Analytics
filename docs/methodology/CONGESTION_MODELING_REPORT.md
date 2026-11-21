# Congestion Modeling & Formulations Report

**Project:** Ambulance Route Optimization — Bengaluru, Karnataka, India  
**Phase:** Phase 5 — Congestion Modeling and Dynamic Scenario Formulation  
**Module:** [`src/traffic/congestion_model.py`](file:///b:/Ambulance%20Route%20Optimization/src/traffic/congestion_model.py)  
**Date:** November 2026  

---

## 1. Operations Research Shortest Path Formulation under Congestion

In emergency ambulance routing, the goal is to find the minimum estimated travel-time path between dispatch origin $s \in V$ and receiving trauma hospital entry junction $t \in V$.

### Mathematical Formulation (Integer Program):
$$\begin{aligned}
\text{Minimize} \quad & Z = \sum_{(i,j) \in E} w_{ij} \cdot x_{ij} \\
\text{Subject to} \quad & \sum_{j:(i,j) \in E} x_{ij} - \sum_{j:(j,i) \in E} x_{ji} = 
\begin{cases}
1 & \text{if } i = s \text{ (Ambulance Origin)} \\
-1 & \text{if } i = t \text{ (Hospital Snapped Junction)} \\
0 & \forall i \in V \setminus \{s, t\} \text{ (Transshipment Junction)}
\end{cases} \\
& x_{ij} \in \{0, 1\} \quad \forall (i, j) \in E
\end{aligned}$$

Where $w_{ij}$ represents the scenario-specific directed edge weight.

---

## 2. Bureau of Public Roads (BPR) Volume-Delay Function

To model link velocity degradation under vehicular volume, we adopt the standard macroscopic Bureau of Public Roads (BPR) formulation:

$$t_{\text{link}}(v) = t_0 \cdot \left[1 + \alpha \cdot \left(\frac{v}{c}\right)^\beta\right]$$

### Parameter Calibration for Greater Bengaluru:
- **Free-flow travel time ($t_0$):**
  $$t_0 = \frac{L_{ij}}{v_0} \times 3600 \text{ seconds}$$
  where $L_{ij}$ is link length in km and $v_0$ is IRC:106 design speed in km/h ($30 \le v_0 \le 50\text{ km/h}$).
- **Alpha ($\alpha = 0.20$):** Calibrated to reflect Indian urban driving behavior, mixed vehicular composition (two-wheelers, auto-rickshaws, cars, buses), and lack of strict lane discipline, preventing the steep divergence common in highway-calibrated models ($\alpha = 0.15$).
- **Beta ($\beta = 4.0$):** Retains the standard quartic delay penalty curve when vehicular demand approaches and exceeds capacity.
- **Volume-to-Capacity Ratio ($v/c$):**
  - Moderate Inter-Peak: $v/c \in [0.55, 0.70]$
  - Peak Rush-Hour: $v/c \in [0.90, 1.15]$ (calibrated to match TomTom $13.9\text{ km/h}$ average crawl)

---

## 3. Strict Non-Double-Counting Invariant

A central risk in urban traffic modeling is double-counting delay when combining traffic volume slowdowns with intersection signal timing delays. In this project, a strict non-double-counting policy is enforced:

$$w_{ij}^{\text{combined}} = t_0 + \Delta t_{\text{traffic}} + d_{\text{signal}}$$

Where:
1. **$t_0$ (Free-Flow Cruising Time):** Speed-limit travel time over distance $L_{ij}$.
2. **$\Delta t_{\text{traffic}}$ (Mid-Link Congestion Delay):** Vehicular friction slowdown between junctions:
   $$\Delta t_{\text{traffic}} = t_0 \cdot \alpha \cdot \left(\frac{v}{c}\right)^\beta$$
3. **$d_{\text{signal}}$ (Terminal Intersection Red Delay):** Webster fixed-time uniform red delay experienced exclusively upon reaching junction $j$:
   $$d_{\text{signal}} = \frac{C \cdot (1 - \lambda)^2}{2 \cdot (1 - \lambda \cdot x)}$$
   where $C$ is the cycle time from verified BTP drawings, $\lambda = g / C$ is the green ratio, and $x = v/c$.

Because $\Delta t_{\text{traffic}}$ accounts for mid-block cruising friction and $d_{\text{signal}}$ accounts for stopping at the approach signal head, the two components are mutually exclusive and additive.

---

## 4. Shortest Path Solvability Guarantee

Dijkstra's Shortest Path Algorithm requires that all edge weights be strictly non-negative ($w_{ij} \ge 0$).
In our model:
- $t_0 > 0$ because all road segments have length $L_{ij} \ge 5.0\text{ m}$ and speed $v_0 \le 50\text{ km/h}$.
- $\Delta t_{\text{traffic}} \ge 0$ because $\alpha > 0$ and $v/c \ge 0$.
- $d_{\text{signal}} \ge 0$ because red time and cycle time are strictly non-negative.

Thus:
$$w_{ij} \ge t_0 > 0 \quad \forall (i, j) \in E$$
The graph contains zero negative cycles, guaranteeing that Dijkstra's algorithm finds the globally optimal minimum-time emergency route in polynomial time $\mathcal{O}(|E| + |V| \log |V|)$.
