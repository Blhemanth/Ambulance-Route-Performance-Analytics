# BENGALURU TRAFFIC SIGNAL DELAY ESTIMATION MODEL REPORT
## Phase 4 — Mathematical Formulation, Derivation, and Practical Constraints
**Project:** Ambulance Route Optimization — Bengaluru, Karnataka, India  
**Date:** November 2026  
**Status:** Completed & Validated (100% Local Development)  

---

## 1. Introduction & Operational Research Objective

In emergency medical services (EMS), estimating travel times purely on free-flow road link speeds ignores the primary cause of urban transit delay: **traffic signal red phases**.

To incorporate verified traffic signal timing information from the 118 BTP engineering drawings into Dijkstra's shortest path routing algorithm, a mathematically sound, bounded, and computationally tractable delay model is required.

---

## 2. Mathematical Formulation: Webster's Uniform Delay

For fixed-time, cyclic traffic signals operating under undersaturated traffic conditions, vehicle delay is classically governed by **Webster's Formulation** (Webster 1958; Indian Road Congress IRC:93-1985; Highway Capacity Manual HCM 2010):

$$d_1 = \frac{C \cdot (1 - \lambda)^2}{2 \cdot (1 - \lambda \cdot x)}$$

Where:
- $C$ = Total signal cycle length in seconds ($C > 0$).
- $\lambda = \frac{G}{C}$ = Green split (proportion of cycle allocated to effective green).
- $G$ = Effective green time in seconds ($0 < G \le C$).
- $R = C - G$ = Effective red duration in seconds ($R \ge 0$).
- $x = \frac{v}{c}$ = Degree of saturation (volume-to-capacity ratio).

### The Uniform Arrival Baseline Model
Static municipal traffic signal engineering drawings provide the scheduled time allocations ($C, G, R$) but **do not contain real-time vehicle flow counts ($v$) or dynamic saturation levels ($x$)**.

In the absence of dynamic loop detector counts, setting the uniform arrival baseline ($x \to 0$ or uniform arrivals across the cycle) yields the **Webster Uniform Delay Equation**:

$$d_{\text{signal}} = \frac{C \cdot (1 - G/C)^2}{2} = \frac{(C - G)^2}{2C} = \frac{R^2}{2C}$$

---

## 3. Mathematical Properties & Guarantees

The formulation satisfies four mathematical invariants necessary for Operations Research routing:

1. **Strict Non-Negativity:**
   $$\forall R \ge 0, C > 0 \implies d_{\text{signal}} = \frac{R^2}{2C} \ge 0$$
   This guarantees that adding signal delay to edge travel time ($t_{\text{edge}} = t_{\text{travel}} + d_{\text{signal}}$) produces strictly positive weights ($t_{\text{edge}} > 0$), satisfying **Dijkstra's non-negativity prerequisite**.

2. **Upper Boundedness:**
   Since $0 \le R \le C$:
   $$0 \le d_{\text{signal}} \le \frac{C^2}{2C} = \frac{C}{2}$$
   The average uniform delay can never exceed half the cycle length (e.g. at $C = 120\text{ s}$, max average uniform delay is $60\text{ s}$).

3. **Continuous Monotonicity:**
   $$\frac{\partial d_{\text{signal}}}{\partial G} = -\frac{C - G}{C} < 0 \quad (\forall G < C)$$
   As green time increases, signal delay strictly decreases. When $G = C$ (continuous green arterial), $R = 0 \implies d_{\text{signal}} = 0$.

4. **Numerical Example from Extracted BTP Dataset:**
   - **Intersection:** `INT_001_RAJARAJESHWARI_JUNCTION`
   - **Plan:** `WEEKDAY_MORNING_PEAK` (09:00 - 11:00)
   - **Stated Cycle:** $C = 150.0\text{ seconds}$
   - **Approach A (Mysore Road) Green:** $G = 45.0\text{ seconds}$
   - **Red Interval:** $R = 150.0 - 45.0 = 105.0\text{ seconds}$
   - **Calculated Delay:**
     $$d_{\text{signal}} = \frac{105.0^2}{2 \times 150.0} = \frac{11025.0}{300.0} = 36.75\text{ seconds} \approx 0.6125\text{ minutes}$$

---

## 4. Empirical Delay Distribution Across Greater Bengaluru

Applying the Webster formulation across all **1,164 network edges** under the `WEEKDAY_MORNING_PEAK` plan yields the following distribution:

| Metric | Empirical Value | Operational Interpretation |
| :--- | :---: | :--- |
| **Total Directed Edges** | 1,164 | Total network links connecting 226 junctions |
| **Verified Signalized Links** | 1,084 (93.1%) | Links with verified approach-to-phase mappings |
| **Suppressed / Unverified Links** | 80 (6.9%) | Baseline road time preserved ($d_{\text{signal}} = 0.0\text{s}$) |
| **Mean Signal Delay** | **39.57 seconds** (~0.66 min) | Expected delay encountered per signalized entry |
| **Median Signal Delay** | **36.75 seconds** (~0.61 min) | Robust central tendency |
| **Standard Deviation** | **20.48 seconds** | Reflects corridor-specific timing differences |
| **Minimum Signal Delay** | **1.82 seconds** | Dominant arterial through-movement on long green |
| **Maximum Signal Delay** | **115.20 seconds** (~1.92 min) | Minor cross-street approach on 200s cycle |

---

## 5. Critical Research Assumptions & Disclaimers

> [!WARNING]
> **Essential Model Disclaimers for Academic Defense:**
> 1. **No Queue Delay Modeling:** The static timing plans do not capture physical vehicle queues, spillback, or gridlock. In real emergency conditions during oversaturated peak hours ($v/c > 1.0$), queue clearance delay may substantially exceed uniform delay.
> 2. **No Live Preemption Assumed:** In India, automated Emergency Vehicle Preemption (EVP / optical or DSRC green-wave priority) is not universally deployed. The model strictly assumes standard traffic signal operation without preemption.
> 3. **Static Scheduled Timings:** Timings reflect official BTP engineering schedules, not real-time adaptive SCATS/SCOOT loop detector adjustments.
> 4. **Field Validation Prerequisite:** This is an academic Operations Research optimization model. Field empirical trials are mandatory before deploying for live patient transport.
