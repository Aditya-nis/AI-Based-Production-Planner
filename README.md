# AI-Based Production/Resource Planning using Constraint Satisfaction

An Artificial Intelligence mini-project that models industrial manufacturing as a formal **Constraint Satisfaction Problem (CSP)** and derives conflict-free production schedules using **Recursive Backtracking Search**, the **Minimum Remaining Values (MRV) Heuristic**, **Forward Checking**, and **10 Hard Constraints**.

---

## 1. Problem Statement

In modern manufacturing facilities, production planning involves assigning machines, operators, time slots, and raw materials to competing product orders. Traditional manual scheduling suffers from the **combinatorial explosion problem** ($O(D^N)$), where the search space grows exponentially with the number of tasks $N$ and resource combinations $D$.

Without algorithmic planning, common factory failures occur:
- **Resource Overlap Conflicts:** Two products simultaneously assigned to the same machine or worker.
- **Skill Incompatibility:** Tasks assigned to operators lacking technical qualifications.
- **Capacity Bottlenecks:** Machine or worker daily shift hours exceeded.
- **Inventory Stockouts:** Products scheduled without sufficient raw materials.
- **Missed Deadlines:** Tasks completing after delivery cutoffs.

---

## 2. Objective

This system automates factory production planning using AI constraint reasoning:
1. Translates factory database assets into formal CSP variables and domain spaces.
2. Applies strict constraint filtering and forward checking to eliminate invalid schedules.
3. Uses the **MRV (Minimum Remaining Values)** heuristic to prioritize the most constrained tasks first (Fail-First principle).
4. Generates an optimal, zero-conflict schedule saved directly into SQLite.
5. Provides **transparent AI decision explanations** for every assignment and actionable conflict diagnostics when conditions cannot be satisfied.
6. Enables **dynamic rescheduling** when machines enter maintenance or workers take leave.

---

## 3. AI Technique & CSP Formulation

The production planning engine is modeled as a formal CSP triple $\langle X, D, C \rangle$:

### Variables ($X$)
Each discrete production task or batch unit is a CSP variable:
$$X = \{T_1, T_2, \dots, T_n\}$$
Where each variable carries metadata: `product_id`, `duration`, `priority` (High/Medium/Low), `deadline`, `required_machine_type`, `required_skill`, and `material_id`.

### Domains ($D$)
The domain for each variable is the set of valid combinations:
$$D(T_i) = \{(m, w, \text{start}, \text{end}) \mid m \in \text{Machines}, w \in \text{Workers}, [\text{start}, \text{end}] \in \text{ShiftWindow}\}$$
Discrete 1-hour step slots are generated across standard operational hours (08:00 – 17:00).

### 10 Hard Constraints ($C$)
1. **Machine Temporal Non-Overlap:** No machine can process two tasks simultaneously:
   $$\forall i \neq j, (M(T_i) = M(T_j)) \implies [\text{Start}(T_i), \text{End}(T_i)) \cap [\text{Start}(T_j), \text{End}(T_j)) = \emptyset$$
2. **Worker Temporal Non-Overlap:** No operator can work on two tasks simultaneously:
   $$\forall i \neq j, (W(T_i) = W(T_j)) \implies [\text{Start}(T_i), \text{End}(T_i)) \cap [\text{Start}(T_j), \text{End}(T_j)) = \emptyset$$
3. **Machine Technical Compatibility:** Machine type must match the product's required machine type.
4. **Worker Skill Qualification:** Assigned operator must possess the required skill.
5. **Machine Working Hours Capacity:** Total scheduled hours on machine $\le$ `machine.available_hours`.
6. **Worker Shift Limit:** Total scheduled hours for operator $\le$ `worker.available_hours`.
7. **Raw Material Inventory Availability:** Cumulative material demand across scheduled tasks $\le$ stock quantity.
8. **Production Delivery Deadline:** Task end time $\le$ deadline cutoff.
9. **Machine Active Status:** Machines under 'Maintenance' or 'Unavailable' cannot be scheduled.
10. **Worker Active Status:** Workers on 'Leave' or 'Unavailable' cannot be scheduled.

### MRV (Minimum Remaining Values) Heuristic
Before picking the next task to assign, the solver evaluates the remaining legal values for all unassigned variables:
$$\text{NextVar} = \arg\min_{V \in \text{Unassigned}} |\{val \in Domain(V) \mid \text{Valid}(V, val)\}|$$
*Tie-breaking:* Priority ranking ($\text{High} > \text{Medium} > \text{Low}$) followed by earliest deadline.

### Backtracking Search & Forward Checking
- **Recursive Search:** Incrementally commits variable assignments.
- **Forward Checking:** Immediately validates whether any remaining unassigned task has its valid domain wiped out ($Domain = \emptyset$). If so, backtracks early.
- **State Instrumentation:** Real-time counters record assignments tried, backtracks, constraints checked, and elapsed milliseconds.

---

## 4. Technologies Used

- **Language:** Python 3
- **Web Framework:** Flask 3
- **ORM & Database:** Flask-SQLAlchemy, SQLite (`database/production.db`)
- **Frontend:** HTML5, CSS3, JavaScript (ES6), Bootstrap 5, Chart.js 4, FontAwesome 6
- **Template Engine:** Jinja2

---

## 5. System Architecture & Directory Structure

```text
Project/
├── app.py                      # Flask application factory & database bootstrap
├── config.py                   # App configuration & SQLite URI
├── requirements.txt            # Python dependencies
│
├── models/
│   ├── __init__.py
│   ├── models.py               # SQLAlchemy models (Product, Machine, Worker, Material, Schedule, ConstraintLog)
│   └── demo_data.py            # Academic demo dataset seeder
│
├── ai_engine/
│   ├── __init__.py
│   ├── csp_scheduler.py        # Core CSP classes: CSPVariable, Domain, Constraint, ProductionCSP, CSPScheduler
│   ├── constraints.py          # 10 Hard Constraint validator functions & check_all_constraints()
│   ├── backtracking.py         # Recursive Backtracking solver with MRV & Forward Checking
│   └── heuristics.py           # MRV heuristic & priority/earliest-start domain ordering
│
├── routes/
│   ├── __init__.py
│   ├── dashboard.py            # Live metrics, utilization calculation, Chart.js feeds
│   ├── products.py             # Product CRUD routes & modal forms
│   ├── machines.py             # Machine CRUD & status toggle for maintenance
│   ├── workers.py              # Worker CRUD & status toggle for leave
│   ├── materials.py            # Raw material inventory management
│   └── planner.py              # AI CSP solver execution, Schedule view, CSV export, Clear
│
├── templates/
│   ├── base.html               # Responsive layout, sidebar navigation, AI loader overlay
│   ├── index.html              # Page 1: Home landing page & AI concepts
│   ├── dashboard.html          # Page 4: Operational KPI cards & utilization charts
│   ├── products.html           # Page 5: Product catalog management
│   ├── machines.html           # Page 6: Machinery & maintenance toggling
│   ├── workers.html            # Page 7: Worker personnel & skill tracking
│   ├── materials.html          # Page 8: Inventory stock levels & health
│   ├── constraints.html        # Page 9: 10 Hard constraints & audit logs
│   ├── planner.html            # Page 10: AI Production Planner & conflict diagnostics
│   ├── schedule.html           # Page 16: Dispatch schedule table, filters, print & CSV export
│   ├── utilization.html        # Page 17: Machine and worker utilization analytics
│   └── ai_explanation.html     # Page 21: Algorithmic flowchart & Viva defense guide
│
├── static/
│   ├── css/
│   │   └── style.css           # Modern AI tech theme & responsive design
│   └── js/
│       └── script.js           # AJAX triggers, animated spinner modal, print helper
│
├── tests/
│   ├── __init__.py
│   ├── test_csp.py             # 10 unit test cases for all CSP failure & success scenarios
│   └── test_routes.py          # End-to-end integration tests
│
└── README.md
```

---

## 6. How to Run (Step-by-Step Windows Instructions)

Open **PowerShell** or **Command Prompt** in the project directory:

### Step 1: Create Virtual Environment
```powershell
python -m venv venv
```

### Step 2: Activate Virtual Environment
In Windows PowerShell:
```powershell
venv\Scripts\Activate.ps1
```
*(If script execution is disabled in PowerShell, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` or activate in CMD via `venv\Scripts\activate.bat`)*

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Run the Application
```powershell
python app.py
```

### Step 5: Open in Web Browser
Navigate to:
```text
http://127.0.0.1:5000
```
*(Demo data is automatically initialized on first run).*

### Step 6: Authentication & Admin Control Panel

The system is enterprise-secured to ensure no unauthenticated users can access the system when hosted:
- **Global Auth Gate:** All pages require authentication. Unauthenticated requests are immediately redirected to `/login`.
- **Only Login (No Public Signup):** Prevents unauthorized visitors from registering accounts.
- **Default Admin Credentials:**
  - **Username:** `admin`
  - **Password:** `admin123`
- **Admin Panel (`/admin`):**
  - Django-style administration portal.
  - Allows the administrator to change their username and password anytime.
  - Allows creating new administrator or manager accounts.
  - Passwords are securely hashed with PBKDF2/SHA-256.

### Step 7: Run Automated Tests
```powershell
python -m unittest discover tests
```

### Step 8: Run via Docker & Docker Compose
You can run this entire application with a single command without installing Python or dependencies locally:

**Using Docker Compose (Recommended):**
```bash
docker compose up --build
```

**Using Standard Docker:**
```bash
docker build -t ai-production-planner .
docker run -d -p 5000:5000 -v ${PWD}/database:/app/database --name ai_planner ai-production-planner
```
Access the application at: `http://localhost:5000`

---

## 7. How to Push to GitHub

To publish this project to your GitHub profile:

1. **Verify Git Initialization & Commit:**
   ```bash
   git init
   git add .
   git commit -m "feat: AI-Based Production Planning using CSP with Enterprise Authentication & Docker"
   ```

2. **Create a GitHub Repository:**
   - Go to [github.com/new](https://github.com/new) and create a repository (e.g. `ai-production-planner-csp`).
   - Do **NOT** initialize with README or .gitignore (they are already included here).

3. **Link Remote and Push:**
   ```bash
   git branch -M main
   git remote add origin https://github.com/<YOUR-USERNAME>/<YOUR-REPO-NAME>.git
   git push -u origin main
   ```

---

## 8. Sample Test Case & Demonstration Walkthrough

### Scenario
A workshop manufacturing electronics and furniture:
- **Products:**
  1. *Laptop Assembly* (Duration: 2h, Priority: High, Deadline: 13:00, Machine: Assembly, Material: ICs)
  2. *Chair Manufacturing* (Duration: 2h, Priority: Medium, Deadline: 15:00, Machine: Cutting, Material: Wood)
  3. *Table Manufacturing* (Duration: 3h, Priority: Medium, Deadline: 17:00, Machine: Drilling, Material: Wood)
  4. *Electronic Controller* (Duration: 2h, Priority: Low, Deadline: 17:00, Machine: Assembly, Material: ICs)
- **Machines:**
  - Assembly Station A (`Assembly`, Available: 8h, 08:00–17:00)
  - CNC Cutting Station (`Cutting`, Available: 8h, 08:00–17:00)
  - Precision Drilling Rig (`Drilling`, Available: 8h, 08:00–17:00)
- **Workers:**
  - Worker A (Skill: `Assembly`)
  - Worker B (Skill: `Cutting`)
  - Worker C (Skill: `Drilling`)
  - Worker D (Skill: `Assembly`)

### Execution
1. Navigate to **AI Production Planner** (`/planner`).
2. Click **"Generate Production Plan"**.
3. The AI engine activates MRV:
   - High-priority *Laptop Assembly* is assigned to Assembly Station A with Worker A from `08:00 - 10:00`.
   - *Chair Manufacturing* is assigned to CNC Cutting Station with Worker B from `08:00 - 10:00`.
   - *Table Manufacturing* is assigned to Precision Drilling Rig with Worker C from `08:00 - 11:00`.
   - *Electronic Controller* also requires Assembly Station A. To prevent machine collision with *Laptop Assembly*, the solver assigns it from `10:00 - 12:00` with Worker D.
4. **Result:** Zero machine overlaps, zero worker overlaps, 100% deadline satisfaction.

### Rescheduling Test (Breakdown Simulation)
1. Go to **Machines** (`/machines`).
2. Click **"Set Maintenance"** for *Assembly Station A*.
3. Return to **AI Planner** and click **"Generate Plan"**.
4. The solver detects that no alternative `Assembly` machine exists, safely halting and displaying:
   - **Conflicting Constraint:** *"No available machine found of required type 'Assembly'."*
   - **Remediation Suggestion:** *"Check machine maintenance statuses and restore at least one machine to Available."*

---

## 8. Expected Output

### Generated Dispatch Schedule
| Product | Quantity | Machine | Worker | Start Time | End Time | Priority | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Laptop Assembly | 1 unit | Assembly Station A | Worker A | 08:00 | 10:00 | High | Scheduled |
| Chair Manufacturing | 1 unit | CNC Cutting Station | Worker B | 08:00 | 10:00 | Medium | Scheduled |
| Table Manufacturing | 1 unit | Precision Drilling Rig | Worker C | 08:00 | 11:00 | Medium | Scheduled |
| Electronic Controller | 1 unit | Assembly Station A | Worker D | 10:00 | 12:00 | Low | Scheduled |

### CSP Solver Statistics
```text
Variables: 4
Initial Domain Size: 44
Assignments Tried: 4
Backtracks: 0
Constraints Checked: 40
Solution Found: YES
Execution Time: ~2.5 ms
```

---

## 9. Limitations

1. **Deterministic Processing Times:** Task durations are assumed fixed rather than stochastic.
2. **Discrete Time Windows:** Uses fixed hourly step intervals rather than continuous floating timestamps.
3. **Single Shift Modeling:** Configured for single-day 08:00–17:00 shifts; multi-shift schedules span multiple daily cycles.
4. **Single Worker Per Machine:** Assumes 1:1 operator-machine coupling per task unit.

---

## 10. Future Scope

1. **Genetic Algorithms (GA):** Hybridization with evolutionary search for multi-objective optimization (minimizing makespan vs energy cost).
2. **Machine Learning / Predictive Maintenance:** Incorporate ML failure prediction models to adjust machine availability probabilities dynamically.
3. **IoT Real-Time Monitoring:** Connect real-time RFID/sensor feeds to trigger automated rescheduling when physical delays occur on the factory floor.
4. **Multi-Skill Matrix:** Extend skill matching to partial proficiency levels and team-based task assignments.
