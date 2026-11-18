# MATHEMATICAL MODEL SPECIFICATION: OPERATIONS RESEARCH NETWORK OPTIMIZATION
## Bengaluru Smart Traffic Optimizer

---

## 1. Mathematical Framework Overview
The Bengaluru Smart Traffic Optimizer formulates urban traffic management as a unified system of **Operations Research Network Models**. 

Rather than treating signal timing in isolation or running arbitrary network flows, this framework formally couples:
1. **Network Flow Models** (Maximum Flow, Minimum Cost Flow, Shortest Path) operating on a directed road graph $G = (V, E)$, with
2. **Signal Timing Linear Programming (LP)** at individual intersections $j \in V$, which directly dictates the **effective capacities** $u_{ij}$ and **travel costs** $c_{ij}$ of the network edges.

```
+-------------------------------------------------------------------------+
|                          DIRECTED ROAD GRAPH                            |
|                               G = (V, E)                                |
|  Nodes V: Intersections & External Centroids                           |
|  Edges E: Physical Road Links & Permitted Turning Movements             |
+-------------------------------------------------------------------------+
                                    |
          +-------------------------+-------------------------+
          |                                                   |
          v                                                   v
+-----------------------+                           +-------------------+
|     MODEL 1:          |                           |     MODEL 2:      |
|   MAXIMUM FLOW        |                           | MINIMUM COST FLOW |
| Maximize Throughput F |                           | Minimize Cost Z   |
| Subject to Capacities |                           | Subject to Supply |
|  & Flow Conservation  |                           |     and Demand    |
+-----------------------+                           +-------------------+
          |                                                   |
          +-------------------------+-------------------------+
                                    |
                                    v
                        +-----------------------+
                        |       MODEL 3:        |
                        |     SHORTEST PATH     |
                        | Dijkstra Formulation  |
                        |  Minimum Delay Routes |
                        +-----------------------+
                                    ^
                                    |
          +-------------------------+-------------------------+
          |         LINKED NETWORK FEEDBACK COUPLING          |
          |  Signal green split (g_p / C) determines edge     |
          |  capacities u_ij and Webster delay costs c_ij     |
          +---------------------------------------------------+
                                    |
                                    v
                        +-----------------------+
                        |       MODEL 4:        |
                        |     SIGNAL TIMING     |
                        |      LP OPTIMIZER     |
                        | Minimize Queues &     |
                        | Delay Across Cycles   |
                        +-----------------------+
```

---

## 2. Model 1: Maximum Flow Formulation

### 2.1 Purpose
Determine the absolute upper bound of vehicular throughput that the Bengaluru road network can sustain between selected origin centroids (sources $S \subset V$) and destination centroids (sinks $T \subset V$) without exceeding road link and movement capacities.

### 2.2 Graph Representation
Let $G = (V, E)$ be a directed network where:
- $V$: Set of nodes representing intersections and perimeter entry/exit centroids.
- $E$: Set of directed edges $(i, j)$ representing physical road links and turning movements.
- $u_{ij} \in \mathbb{R}^+$: Maximum vehicular capacity of link $(i, j)$ in vehicles per hour (PCU/hr).
- $x_{ij} \in \mathbb{R}^+$: Vehicular flow assigned to link $(i, j)$.
- $s$: Super-source node aggregating traffic supply.
- $t$: Super-sink node absorbing traffic demand.

### 2.3 Primal Linear Program
$$\max \quad F$$

Subject to:
1. **Flow Conservation Constraints**:
   $$\sum_{j: (i,j) \in E} x_{ij} - \sum_{k: (k,i) \in E} x_{ki} = \begin{cases} 
   F, & \text{if } i = s \\
   0, & \forall i \in V \setminus \{s, t\} \\
   -F, & \text{if } i = t 
   \end{cases}$$

2. **Capacity Constraints**:
   $$0 \le x_{ij} \le u_{ij}, \quad \forall (i, j) \in E$$

### 2.4 Max-Flow Min-Cut Theorem & Bottleneck Identification
By the **Max-Flow Min-Cut Theorem** (Ford & Fulkerson, 1956):
$$\max(F) = \min_{(S, T)} \text{Capacity}(S, T)$$
Where $(S, T)$ partitions $V$ such that $s \in S$ and $t \in T$.
- **Bottleneck Edges**: Any directed edge $(i, j) \in E$ with $i \in S$ and $j \in T$ whose flow reaches full saturation:
  $$x_{ij} = u_{ij}$$
  These saturated cut-edges represent the critical operational bottlenecks of the Bengaluru corridor.

---

## 3. Model 2: Minimum Cost Flow Formulation

### 3.1 Purpose
Determine the optimal vehicular flow distribution across the road network that satisfies specified origin supplies and destination demands at minimum total system transportation cost (generalized travel time and delay).

### 3.2 Decision Variables & Parameters
- $x_{ij}$: Vehicular flow on edge $(i, j)$.
- $c_{ij}$: Unit transportation cost per vehicle traversing edge $(i, j)$ (minutes per vehicle or generalized rupee cost).
- $u_{ij}$: Upper bound capacity of edge $(i, j)$.
- $b_i$: Net traffic balance at node $i$:
  $$b_i > 0 \implies \text{Traffic Origin (Supply)}$$
  $$b_i < 0 \implies \text{Traffic Destination (Demand)}$$
  $$b_i = 0 \implies \text{Intermediate Transshipment Intersection}$$

### 3.3 Linear Programming Formulation
$$\min \quad Z = \sum_{(i,j) \in E} c_{ij} \cdot x_{ij}$$

Subject to:
1. **Node Mass Balance Equations**:
   $$\sum_{j: (i,j) \in E} x_{ij} - \sum_{k: (k,i) \in E} x_{ki} = b_i, \quad \forall i \in V$$

2. **Network Feasibility Condition**:
   $$\sum_{i \in V} b_i = 0$$

3. **Capacity & Non-Negativity Bounds**:
   $$0 \le x_{ij} \le u_{ij}, \quad \forall (i, j) \in E$$

### 3.4 Transportation Cost Metric Definition
The edge cost $c_{ij}$ is defined using generalized travel time combining free-flow traversal and signalized intersection impedance:
$$c_{ij} = t_{ij}^{\text{free}} + d_{ij}^{\text{signal}}$$
Where:
- $t_{ij}^{\text{free}} = \frac{L_{ij}}{v_{ij}^{\text{free}}} \cdot 60$ (free-flow travel time in minutes, with link length $L_{ij}$ in km and speed $v_{ij}^{\text{free}}$ in km/h).
- $d_{ij}^{\text{signal}}$: Average intersection approach delay per vehicle in minutes.

---

## 4. Model 3: Shortest Path Formulation

### 4.1 Purpose
Identify the minimum-impedance path between specific origin-destination pairs $(o, d)$ under both existing and signal-optimized traffic network conditions.

### 4.2 Integer Linear Program Formulation
Let binary decision variable $y_{ij} \in \{0, 1\}$ equal $1$ if edge $(i, j)$ is traversed in the shortest path, and $0$ otherwise.

$$\min \quad Z_{od} = \sum_{(i,j) \in E} c_{ij} \cdot y_{ij}$$

Subject to:
$$\sum_{j: (i,j) \in E} y_{ij} - \sum_{k: (k,i) \in E} y_{ki} = \begin{cases}
1, & \text{if } i = o \\
-1, & \text{if } i = d \\
0, & \forall i \in V \setminus \{o, d\}
\end{cases}$$
$$y_{ij} \in \{0, 1\}, \quad \forall (i, j) \in E$$

### 4.3 Algorithmic Implementation
Solved using **Dijkstra's Algorithm** with Fibonacci / binary priority heaps for non-negative edge weights $c_{ij} \ge 0$, maintaining $O(|E| + |V| \log |V|)$ complexity. Route costs are benchmarked between baseline PDF signal timings and post-LP optimized timings.

---

## 5. Model 4: Signal Timing Optimization (LP / Queue Dynamics)

### 5.1 Purpose
Optimize the green phase durations $g_{jp}$ across all signal phases $p \in P_j$ at each intersection $j$ to minimize residual vehicular queues, prevent intersection spillback, and balance delay under strict cycle and safety bounds.

### 5.2 Decision Variables
- $g_{jp} \in \mathbb{R}^+$: Green duration (seconds) allocated to phase $p$ at intersection $j$.
- $Q_{jp}^{\text{next}} \in \mathbb{R}^+$: Projected residual vehicular queue at phase $p$ at the end of the next cycle.
- $D_{jp} \in \mathbb{R}^+$: Vehicular departures during phase $p$ in one cycle.

### 5.3 Parameters from Bengaluru Dataset & Traffic Models
- $C_j$: Stated cycle length for intersection $j$ from the BEL timing plan.
- $L_j$: Total lost time per cycle:
  $$L_j = \sum_{p \in P_j} l_p + \sum_{p \in P_j} (\text{yellow}_p + \text{all\_red}_p)$$
- $g_{jp}^{\min}$: Safety minimum green duration (e.g., $10\text{ s}$ for vehicular phases, or pedestrian clearance time).
- $g_{jp}^{\max}$: Operational maximum green cap to prevent excessive cross-street delay.
- $A_{jp}$: Expected vehicle arrivals during cycle $C_j$ for approach movements controlled by phase $p$:
  $$A_{jp} = \frac{q_{jp} \cdot C_j}{3600}$$
- $s_{jp}$: Saturation flow rate of the approach in vehicles per hour of green (typically 1,800 to 2,000 PCU/hr/lane).
- $Q_{jp}^{\text{current}}$: Initial queue length at the start of the optimization interval.

### 5.4 Linear Programming Formulation
$$\min \quad Z_{\text{signal}} = \sum_{j \in V} \sum_{p \in P_j} w_{jp} \cdot Q_{jp}^{\text{next}}$$

Subject to:
1. **Cycle Duration Equality Constraint**:
   $$\sum_{p \in P_j} g_{jp} + g_{j, \text{ped}} + L_j = C_j, \quad \forall j \in V$$
   *(Baseline evaluation keeps cycle length $C_j$ fixed to the documented BEL timing for valid before-and-after comparison).*

2. **Green Time Bounds**:
   $$g_{jp}^{\min} \le g_{jp} \le g_{jp}^{\max}, \quad \forall p \in P_j$$

3. **Pedestrian Safety Duration**:
   $$g_{j, \text{ped}} \ge g_{j, \text{ped}}^{\text{doc}}, \quad \text{where } g_{j, \text{ped}}^{\text{doc}} \text{ is extracted from the PDF plan}$$

4. **Queue Balance Law**:
   $$Q_{jp}^{\text{next}} = Q_{jp}^{\text{current}} + A_{jp} - D_{jp}, \quad \forall p \in P_j$$

5. **Departure Capacity Constraints**:
   $$D_{jp} \le Q_{jp}^{\text{current}} + A_{jp}, \quad \forall p \in P_j$$
   $$D_{jp} \le \frac{s_{jp} \cdot g_{jp}}{3600}, \quad \forall p \in P_j$$

6. **Non-Negativity**:
   $$Q_{jp}^{\text{next}} \ge 0, \quad D_{jp} \ge 0, \quad g_{jp} \ge 0$$

---

## 6. Mathematical Coupling & Network Feedback Integration

### 6.1 Coupling Mechanism
Operations Research network models must not operate with static unlinked inputs. In this architecture:
1. Signal timing decision variables $g_{jp}$ directly determine the **Effective Edge Capacity** $u_{ij}^{\text{eff}}$ of road approach $(i, j)$:
   $$u_{ij}^{\text{eff}} = \min\left(u_{ij}^{\text{physical}}, \; \sum_{p \in P(i,j)} \frac{g_{jp}}{C_j} \cdot s_{ij}\right)$$

2. Signal green ratios directly dictate the **Webster Delay Impedance** $d_{ij}$ and resulting link cost $c_{ij}$:
   $$d_{ij} = \frac{C_j (1 - \lambda_{ij})^2}{2 (1 - \lambda_{ij} X_{ij})} + \frac{X_{ij}^2}{2 q_{ij} (1 - X_{ij})}$$
   Where:
   - $\lambda_{ij} = \frac{g_{ij}}{C_j}$ (Green ratio).
   - $X_{ij} = \frac{q_{ij}}{u_{ij}^{\text{eff}}}$ (Degree of saturation).

3. When Model 4 optimizes green allocations $g_{jp}^*$:
   - Capacities $u_{ij}$ update across the directed graph $G$.
   - Link travel costs $c_{ij}$ update.
   - Models 1, 2, and 3 are re-executed with updated parameters $(u^*, c^*)$.
   - The delta in maximum flow throughput $\Delta F$, total transportation cost $\Delta Z$, and corridor travel times $\Delta t$ proves the system-level benefit of signal optimization under network constraints.
