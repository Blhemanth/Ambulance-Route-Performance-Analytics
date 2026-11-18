"""
Page 10: Operations Research Methodology & Academic Formulation.
Comprehensive theoretical derivations, primal-dual formulations, optimality criteria,
feedback coupling proofs, assumptions, and scholarly references.
"""

import streamlit as st
import pandas as pd
from components.ui_helpers import (
    load_custom_css,
    render_header
)

st.set_page_config(page_title="Methodology | Bengaluru Smart Traffic", page_icon="📜", layout="wide")
load_custom_css()

render_header(
    title="Operations Research Methodology & Mathematical Formulations",
    subtitle="Theoretical Rigor, Primal-Dual Network Formulations, Coupling Feedback Proofs & Academic Defense",
    badge_text="Operations Research Theory"
)

st.markdown("""
### 🏛️ Theoretical Foundations & Research Scope

The Bengaluru Smart Traffic Optimizer operates strictly within the domain of **Operations Research (OR)**, 
employing **Network Models** and **Linear Programming (LP)** to analyze and optimize metropolitan vehicular flow.

The central thesis demonstrates that isolated signal timing optimizations are mathematically suboptimal 
unless coupled with network-level flow equilibrium and capacity constraints.
""")

tab_m1, tab_m2, tab_m3, tab_m4, tab_coupling, tab_refs = st.tabs([
    "1️⃣ Model 1: Max Flow Theory",
    "2️⃣ Model 2: Min Cost Flow Theory",
    "3️⃣ Model 3: Shortest Path Theory",
    "4️⃣ Model 4: Signal LP Theory",
    "🔄 Four-Model Coupling Loop",
    "📚 References & Standards"
])

with tab_m1:
    st.markdown("### Model 1: Maximum Flow & Bottleneck Cut Duality")
    st.latex(r"""
    \begin{aligned}
    \textbf{Primal Max-Flow LP:} & \quad \max F \\
    \text{Subject to:} & \quad \sum_{j:(i,j) \in E} x_{ij} - \sum_{j:(j,i) \in E} x_{ji} = 
    \begin{cases} 
    F & i = s \\
    -F & i = t \\
    0 & \forall i \in V \setminus \{s, t\} 
    \end{cases} \\
    & \quad 0 \le x_{ij} \le u_{ij} \quad \forall (i, j) \in E
    \end{aligned}
    """)
    st.markdown("---")
    st.markdown("#### Dual Cut Formulation & Strong Duality:")
    st.latex(r"""
    \begin{aligned}
    \textbf{Dual Cut Problem:} & \quad \min \sum_{(i,j) \in E} u_{ij} \cdot y_{ij} \\
    \text{Subject to:} & \quad p_i - p_j + y_{ij} \ge 0 \quad \forall (i, j) \in E \\
    & \quad p_s = 1, \quad p_t = 0 \\
    & \quad y_{ij} \ge 0, \quad p_i \in \{0, 1\}
    \end{aligned}
    """)
    st.markdown(r"""
    **Max-Flow Min-Cut Theorem (Ford & Fulkerson, 1956):**  
    At optimality, $F^* = \sum_{(i,j) \in (S, T)^*} u_{ij}$.  
    Edges spanning the minimum cut $(S, T)^*$ are precisely the physical road connections operating at $100\%$ capacity saturation ($x_{ij}^* = u_{ij}$). 
    These edges represent the true network-wide structural bottlenecks.
    """)

with tab_m2:
    st.markdown("### Model 2: Minimum Cost Flow & Network Simplex")
    st.latex(r"""
    \begin{aligned}
    \textbf{Primal Minimum Cost Flow Problem:} & \quad \min Z = \sum_{(i,j) \in E} c_{ij} \cdot x_{ij} \\
    \text{Subject to:} & \quad \sum_{j:(i,j) \in E} x_{ij} - \sum_{j:(j,i) \in E} x_{ji} = b_i \quad \forall i \in V \quad \text{(Flow Conservation)} \\
    & \quad 0 \le x_{ij} \le u_{ij} \quad \forall (i, j) \in E \quad \text{(Capacity Bounds)} \\
    & \quad \sum_{i \in V} b_i = 0 \quad \text{(Feasibility Condition)}
    \end{aligned}
    """)
    st.markdown("---")
    st.markdown("#### Optimality Conditions & Node Potentials:")
    st.latex(r"""
    c_{ij}^{\pi} = c_{ij} - \pi_i + \pi_j
    """)
    st.markdown(r"""
    A feasible flow $x$ is optimal if and only if there exist node potentials $\pi_i$ such that for all edges $(i, j) \in E$:
    1. If $c_{ij}^{\pi} > 0$, then $x_{ij} = 0$.
    2. If $c_{ij}^{\pi} < 0$, then $x_{ij} = u_{ij}$.
    3. If $0 < x_{ij} < u_{ij}$, then $c_{ij}^{\pi} = 0$.
    
    The algorithm terminates at the global minimum-delay flow equilibrium across all transshipment intersections.
    """)

with tab_m3:
    st.markdown("### Model 3: Shortest Path Optimization (Dijkstra)")
    st.latex(r"""
    \begin{aligned}
    \textbf{Shortest Path 0-1 Integer Program:} & \quad \min \sum_{(i,j) \in E} t_{ij} \cdot y_{ij} \\
    \text{Subject to:} & \quad \sum_{j:(i,j) \in E} y_{ij} - \sum_{j:(j,i) \in E} y_{ji} = 
    \begin{cases}
    1 & i = s \\
    -1 & i = t \\
    0 & \forall i \neq s, t
    \end{cases} \\
    & \quad y_{ij} \in \{0, 1\} \quad \forall (i, j) \in E
    \end{aligned}
    """)
    st.markdown("""
    **Total Link Impedance Function:**
    $$t_{ij} = t_{ij}^{\\text{free}} + d_{ij}^{\\text{Webster}}$$
    Where $t_{ij}^{\\text{free}} = \\frac{L_{ij}}{v_{\\text{free}}}$ and $d_{ij}^{\\text{Webster}}$ is the signal delay computed from the signal timing model.
    Because the node-arc incidence matrix of a directed graph is **totally unimodular (TUM)**, the linear programming relaxation yields an integer optimal solution directly solvable in $O(|E| + |V| \\log |V|)$ using Dijkstra's algorithm.
    """)

with tab_m4:
    st.markdown("### Model 4: Traffic Signal Timing Linear Programming")
    st.latex(r"""
    \begin{aligned}
    \textbf{Queue-Minimizing LP:} & \quad \min Z = \sum_{p=1}^P w_p \cdot Q_{p}^{\text{next}} - \epsilon \sum_{p=1}^P \left(\frac{q_p}{\sum q_k}\right) g_p \\
    \text{Subject to:} & \quad \sum_{p=1}^{P_{\text{veh}}} g_p + L_j + g_{\text{ped}} = C_j \quad \text{(Cycle Conservation)} \\
    & \quad Q_p^{\text{next}} + D_p = Q_p^{\text{curr}} + A_p \quad \forall p \in \{1,\dots,P_{\text{veh}}\} \quad \text{(Queue Mass Balance)} \\
    & \quad D_p \le \left(\frac{s_p}{3600}\right) g_p \quad \forall p \in \{1,\dots,P_{\text{veh}}\} \quad \text{(Discharge Upper Bound)} \\
    & \quad g_{\min} \le g_p \le g_{\max} \quad \forall p \in \{1,\dots,P_{\text{veh}}\} \\
    & \quad Q_p^{\text{next}} \ge 0, \quad D_p \ge 0
    \end{aligned}
    """)
    st.markdown(r"""
    **Webster's Classical Delay Equation (Webster, 1958):**
    $$d_p = \frac{C(1 - \lambda_p)^2}{2(1 - \lambda_p x_p)} + \frac{x_p^2}{2q_p(1 - x_p)} - 0.65\left(\frac{C}{q_p^2}\right)^{1/3} x_p^{(2 + 5\lambda_p)}$$
    Where $\lambda_p = g_p / C$ is the green ratio and $x_p = q_p / (s_p \lambda_p)$ is the degree of saturation.
    """)

with tab_coupling:
    st.markdown("### 🔄 Complete Four-Model Feedback Coupling Loop")
    st.markdown("""
    The four models are not treated as independent demonstrations. They form a closed-loop mathematical feedback framework:
    """)

    coupling_steps = pd.DataFrame([
        {"Step": "1. Topology", "Action": "Construct directed road graph G = (V, E) from 118 PDF geocoded intersections.", "Math Object": "G = (V, E)"},
        {"Step": "2. Baseline State", "Action": "Load BEL timing plans (C_j, g_jp) and calculate baseline capacities and Webster delays.", "Math Object": "u_ij^0, c_ij^0"},
        {"Step": "3. Baseline Network Models", "Action": "Execute Models 1 (Max Flow), 2 (Min Cost Flow), and 3 (Shortest Path) on baseline network.", "Math Object": "F_0^*, Z_0^*, t_{s,t}^0"},
        {"Step": "4. Signal Timing LP (Model 4)", "Action": "Solve HiGHS LP to compute optimal green splits g_jp^* minimizing residual queues.", "Math Object": "g_jp^*"},
        {"Step": "5. Capacity Recalculation", "Action": "Update effective movement capacity: u_ij^{new} = s_i * (g_jp^* / C_j).", "Math Object": "u_ij^{new}"},
        {"Step": "6. Delay Recalculation", "Action": "Recalculate Webster delay impedance: c_ij^{new} = t_free + d_Webster(g_jp^*).", "Math Object": "c_ij^{new}"},
        {"Step": "7. Re-Execute Network Models", "Action": "Re-run Models 1, 2, and 3 under updated capacities and costs.", "Math Object": "F_opt^*, Z_opt^*, t_{s,t}^{opt}"},
        {"Step": "8. Comparative Analytics", "Action": "Quantify throughput expansion, travel time savings, and bottleneck relief.", "Math Object": "Delta F*, Delta Z*, Delta t"}
    ])
    st.dataframe(coupling_steps, use_container_width=True)

with tab_refs:
    st.markdown("### 📚 Academic Standards & References")
    st.markdown("""
    1. **Ahuja, R. K., Magnanti, T. L., & Orlin, J. B. (1993).**  
       *Network Flows: Theory, Algorithms, and Applications.* Prentice Hall, Englewood Cliffs, NJ.
    
    2. **Ford, L. R., & Fulkerson, D. R. (1956).**  
       *Maximal Flow Through a Network.* Canadian Journal of Mathematics, 8, 399-404.
    
    3. **Dijkstra, E. W. (1959).**  
       *A Note on Two Problems in Connexion with Graphs.* Numerische Mathematik, 1(1), 269-271.
    
    4. **Webster, F. V. (1958).**  
       *Traffic Signal Settings.* Road Research Technical Paper No. 39, HMSO, London.
    
    5. **Indian Roads Congress (IRC:106-1990).**  
       *Guidelines for Capacity of Urban Roads in Plain Areas.* New Delhi, India.
    
    6. **Transportation Research Board (TRB). (2010).**  
       *Highway Capacity Manual (HCM 2010).* National Research Council, Washington, D.C.
    """)
