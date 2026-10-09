# Academic Mini-Project Report
# AI-Based Production/Resource Planning using Constraint Satisfaction

**Course:** Artificial Intelligence Mini-Project  
**Domain:** Constraint Satisfaction Problems (CSP), Intelligent Scheduling, Heuristic Search  
**Tech Stack:** Python 3, Flask, SQLite, HTML5, CSS3, JavaScript, Bootstrap 5  
**Academic Year:** 2026  

---

## Abstract
In manufacturing job shops, optimal resource scheduling is critical to preventing costly idle machinery, worker conflicts, and delayed deliveries. Traditional manual planning suffers from combinatorial explosion ($O(D^N)$), making manual scheduling intractable. This project formulates factory production planning as a formal **Constraint Satisfaction Problem (CSP)**, modeling tasks as variables, resource time slots as domains, and industrial operational rules as 10 hard constraints. 

A specialized AI engine was implemented in pure Python using **Recursive Backtracking Search**, the **Minimum Remaining Values (MRV)** heuristic, and **Forward Checking**. The application guarantees zero resource overlap, strict skill matching, shift compliance, and deadline satisfaction. Furthermore, the engine delivers Explainable AI (XAI) decision justifications and automated root-cause diagnostics when disruptions (e.g., machine maintenance) occur. The backend is integrated with Flask and SQLite, coupled with an interactive Bootstrap 5 frontend featuring live KPI dashboards and Chart.js utilization analytics.

---

## Chapter 1: Introduction

### 1.1 Background & Motivation
Modern manufacturing plants operate multiple specialized workstations (e.g., Assembly, CNC Cutting, Drilling) staffed by technicians with specific certifications. Orders arrive with varying priorities, deadlines, and raw material demands. Scheduling these tasks manually creates major operational vulnerabilities:
- Machines double-booked for concurrent operations.
- Operators assigned tasks exceeding their shift hours.
- Orders scheduled without sufficient raw materials in stock.
- High-priority orders delayed past customer deadlines.

### 1.2 Problem Statement
To design and implement a web-based automated production planning system that models industrial resources and tasks as a formal Constraint Satisfaction Problem, computing conflict-free schedules using AI search algorithms and enabling dynamic rescheduling during equipment disruptions.

### 1.3 Key Objectives
1. Formalize manufacturing operations as a mathematical CSP triple $\langle X, D, C \rangle$.
2. Implement 10 Hard Constraints covering machinery, operators, skills, capacity, inventory, and deadlines.
3. Construct a recursive Backtracking search engine with the MRV heuristic (Fail-First principle) and forward checking.
4. Provide transparent Explainable AI (XAI) justification trails for all scheduling decisions.
5. Provide dynamic rescheduling capabilities with automated root-cause conflict diagnostics.
6. Deliver a full-featured web interface with live KPI cards, resource utilization charts, and CSV export.

---

## Chapter 2: Theoretical Foundations of CSP

### 2.1 Constraint Satisfaction Problem Formulation
A CSP is formally defined as a triple:
$$\langle X, D, C \rangle$$

Where:
- **$X = \{X_1, X_2, \dots, X_n\}$**: Finite set of variables representing discrete tasks.
- **$D = \{D_1, D_2, \dots, D_n\}$**: Set of domains, where $D_i$ is the set of permissible values for variable $X_i$.
- **$C = \{C_1, C_2, \dots, C_m\}$**: Set of constraints restricting allowable simultaneous value combinations.

A state is **consistent** if it violates no constraints. A **solution** is a complete, consistent assignment to all variables.

### 2.2 Minimum Remaining Values (MRV) Heuristic
The MRV heuristic chooses the unassigned variable with the fewest remaining legal domain values:
$$\text{NextVariable} = \arg\min_{V \in \text{Unassigned}} |\{v \in D(V) \mid \text{Consistent}(V, v)\}|$$

**Why MRV?**
Also known as the **"Fail-First"** heuristic, choosing the most constrained variable prunes large subtrees high up in the search hierarchy, shrinking the effective branching factor and reducing search steps by several orders of magnitude.

### 2.3 Forward Checking
Whenever variable $X$ is tentatively assigned value $v$, forward checking inspects every unassigned variable $Y$ constrained by $X$. Any value in $D(Y)$ incompatible with $(X = v)$ is removed. If any domain becomes empty ($D(Y) = \emptyset$), the search backtracks immediately, avoiding futile deeper recursion.

---

## Chapter 3: Mathematical Model & The 10 Hard Constraints

### Variables ($X$)
Each batch task is modeled as an independent variable:
$$X = \{T_1, T_2, \dots, T_n\}$$
Attributes: Product ID, Task Duration (hours), Priority (High/Medium/Low), Deadline, Machine Type, Required Skill, Material ID, Material Quantity.

### Domains ($D$)
Cartesian product space of valid resource combinations:
$$D(T_i) = \{(m, w, \text{start}, \text{end}) \mid m \in \text{Machines}, w \in \text{Workers}, [\text{start}, \text{end}] \in [08:00, 17:00]\}$$

### The 10 Hard Constraints ($C$)
1. **Machine Temporal Non-Overlap:**  
   $$\forall i \neq j, (M(T_i) = M(T_j)) \implies [\text{Start}(T_i), \text{End}(T_i)) \cap [\text{Start}(T_j), \text{End}(T_j)) = \emptyset$$
2. **Worker Temporal Non-Overlap:**  
   $$\forall i \neq j, (W(T_i) = W(T_j)) \implies [\text{Start}(T_i), \text{End}(T_i)) \cap [\text{Start}(T_j), \text{End}(T_j)) = \emptyset$$
3. **Machine Technical Compatibility:**  
   $$\text{Type}(M(T_i)) = \text{RequiredType}(T_i)$$
4. **Worker Skill Qualification:**  
   $$\text{Skill}(W(T_i)) = \text{RequiredSkill}(T_i)$$
5. **Machine Working Hours Capacity:**  
   $$\sum_{T \in \text{Assigned}(M)} \text{Duration}(T) \le \text{AvailableHours}(M)$$
6. **Worker Shift Limit:**  
   $$\sum_{T \in \text{Assigned}(W)} \text{Duration}(T) \le \text{AvailableHours}(W)$$
7. **Raw Material Inventory Availability:**  
   $$\sum_{T \in \text{Scheduled}} \text{MaterialDemand}(T, R) \le \text{StockQuantity}(R)$$
8. **Production Delivery Deadline:**  
   $$\text{End}(T_i) \le \text{Deadline}(T_i)$$
9. **Machine Active Status:**  
   $$\text{Status}(M) = \text{'Available'}$$
10. **Worker Active Status:**  
    $$\text{Status}(W) = \text{'Available'}$$

---

## Chapter 4: System Architecture & Implementation

```text
Project/
├── app.py                      # Flask Application Entrypoint & Auto DB Bootstrap
├── config.py                   # Configuration & SQLite URI
├── requirements.txt            # Project Dependencies
├── models/
│   ├── models.py               # 6 SQLAlchemy Database Models
│   └── demo_data.py            # Academic Demo Dataset Seeder
├── ai_engine/
│   ├── csp_scheduler.py        # Core CSP Classes & Solver Coordinator
│   ├── constraints.py          # 10 Hard Constraint Functions & check_all_constraints()
│   ├── backtracking.py         # Recursive Backtracking Solver & Forward Checking
│   └── heuristics.py           # MRV Heuristic & Value Ordering
├── routes/
│   ├── dashboard.py            # KPI Cards & Chart.js Utilization Feeds
│   ├── products.py             # Products CRUD
│   ├── machines.py             # Machines CRUD & Maintenance Toggle
│   ├── workers.py              # Workers CRUD & Leave Toggle
│   ├── materials.py            # Raw Materials Inventory CRUD
│   └── planner.py              # AI Planner Run, Schedule View, CSV Export
├── templates/                  # 11 Jinja2 HTML5 Templates
├── static/                     # CSS Stylesheet & Interactive JS
└── tests/
    ├── test_csp.py             # 10 Unit Tests for all CSP Scenarios
    └── test_routes.py          # End-to-End Route Integration Tests
```

---

## Chapter 5: Experimental Results & Viva Verification

### 5.1 Standard Academic Scenario
- **Products:** Laptop Assembly (2h, High, Deadline: 13:00), Chair Manufacturing (2h, Med, 15:00), Table Manufacturing (3h, Med, 17:00), Electronic Controller (2h, Low, 17:00).
- **Machines:** Precision Assembly Station, High-Speed CNC Cutter, Automated Drilling Unit.
- **Workers:** Alice (Assembly), Bob (Cutting), Charlie (Drilling), Diana (Assembly).

### 5.2 Generated Production Schedule
| Product | Quantity | Machine | Worker | Time Window | Priority | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Laptop Assembly** | 1 | Precision Assembly Station | Alice | 08:00 – 10:00 | High | Scheduled |
| **Chair Manufacturing** | 1 | High-Speed CNC Cutter | Bob | 08:00 – 10:00 | Medium | Scheduled |
| **Table Manufacturing** | 1 | Automated Drilling Unit | Charlie | 08:00 – 11:00 | Medium | Scheduled |
| **Electronic Controller**| 1 | Precision Assembly Station | Diana | 10:00 – 12:00 | Low | Scheduled |

*Key Observation:* Electronic Controller was automatically staggered to start at 10:00 to prevent machine overlap with Laptop Assembly on the shared Precision Assembly Station.

### 5.3 CSP Statistics
- **Variables:** 4
- **Initial Domain Space:** 44 combinations
- **Assignments Tried:** 4
- **Backtracks:** 0
- **Constraints Checked:** 40
- **Execution Time:** ~2.5 milliseconds
- **Conflicts:** 0

### 5.4 Disruption Simulation (Dynamic Rescheduling)
Setting Precision Assembly Station to 'Maintenance' and clicking 'Regenerate Schedule' triggers:
- **Conflict Identified:** *"No available machine found of required type 'Assembly'."*
- **Remediation Advice:** *"Check machine maintenance statuses and restore at least one machine to Available."*

---

## Chapter 6: Conclusion & Future Scope

### 6.1 Conclusion
The project confirms that Constraint Satisfaction Problems (CSP) combined with recursive Backtracking Search, the Minimum Remaining Values (MRV) heuristic, and Forward Checking offer an optimal, scalable approach to industrial production planning. By formalizing operational constraints mathematically, zero resource overlap is guaranteed while providing complete explainability for viva examiners.

### 6.2 Future Scope
1. **Genetic Algorithms (GA):** Multi-objective optimization balancing makespan against factory energy costs.
2. **Machine Learning Predictive Maintenance:** Predicting asset failures to preemptively remove machines from domains.
3. **IoT Shopfloor Telemetry:** Live feedback from RFID/PLC sensors to trigger autonomous rescheduling.
4. **Multi-Skill Matrices:** Supporting team-based tasks and graded operator proficiencies.

---

## References
1. Russell, S., & Norvig, P. (2020). *Artificial Intelligence: A Modern Approach* (4th ed.). Pearson.
2. Dechter, R. (2003). *Constraint Processing*. Morgan Kaufmann.
3. Pinedo, M. L. (2016). *Scheduling: Theory, Algorithms, and Systems*. Springer.
4. Rossi, F., van Beek, P., & Walsh, T. (2006). *Handbook of Constraint Programming*. Elsevier.
