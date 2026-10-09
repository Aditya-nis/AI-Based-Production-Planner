"""
AI Production / Resource Planning Engine using Constraint Satisfaction Problem (CSP).

This module contains:
- CSPVariable: Production task representation
- Domain: Domain space generator for machine, worker, and time slot combinations
- Constraint: Formal constraint representation
- ProductionCSP: Full problem formulation
- CSPScheduler: End-to-end scheduler orchestrating data extraction, solving, logging, and explanation.
"""

from datetime import datetime
from .constraints import (
    time_to_hours,
    hours_to_time,
    check_all_constraints,
    check_machine_status,
    check_worker_status,
    check_machine_compatibility,
    check_worker_skill,
    check_deadline
)
from .backtracking import BacktrackingSolver

class CSPVariable:
    """Represents a production task to be scheduled as a CSP variable."""
    def __init__(self, var_id, product_id, product_name, product_code, task_index,
                 duration, priority, deadline, required_machine_type,
                 material_id=None, material_quantity=1.0, required_skill=None):
        self.id = var_id
        self.product_id = product_id
        self.product_name = product_name
        self.product_code = product_code
        self.task_index = task_index
        self.name = f"{product_name} [Task {task_index}]"
        self.duration = float(duration)
        self.priority = str(priority).capitalize()
        self.deadline = str(deadline)
        self.required_machine_type = required_machine_type
        self.required_skill = required_skill or required_machine_type
        self.material_id = material_id
        self.material_quantity = float(material_quantity)
        self.domain = []

    def __repr__(self):
        return f"<CSPVariable {self.name} (dur={self.duration}h, dline={self.deadline}, prio={self.priority})>"

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, CSPVariable):
            return False
        return self.id == other.id


class Domain:
    """Generates the Cartesian product domain space of (Machine, Worker, Start Time, End Time)."""
    @staticmethod
    def generate_domain_for_variable(variable, machines, workers, slot_step_hours=1.0):
        """
        Generate possible (machine, worker, start, end) tuples for the variable.
        Time slots are generated across 08:00 to 17:00 (standard industrial shift).
        """
        values = []
        var_duration = variable.duration
        deadline_hours = time_to_hours(variable.deadline)

        # Filter machines by compatibility & availability
        compatible_machines = [
            m for m in machines
            if check_machine_compatibility(variable, m)[0] and check_machine_status(m)[0]
        ]

        # Filter workers by skill & availability
        compatible_workers = [
            w for w in workers
            if check_worker_skill(variable, w)[0] and check_worker_status(w)[0]
        ]

        # If no compatible machine or worker, generate cross product anyway so
        # constraint checker can properly flag the incompatibility in diagnostic reports!
        candidate_machines = compatible_machines if compatible_machines else machines
        candidate_workers = compatible_workers if compatible_workers else workers

        for machine in candidate_machines:
            m_start = time_to_hours(machine.start_time)
            m_end = time_to_hours(machine.end_time)

            for worker in candidate_workers:
                w_start = time_to_hours(worker.start_time)
                w_end = time_to_hours(worker.end_time)

                # Active shared window
                window_start = max(m_start, w_start, 8.0)
                window_end = min(m_end, w_end, 18.0)

                # Generate time slots in step increments
                curr = window_start
                while curr + var_duration <= window_end:
                    slot_end = curr + var_duration

                    # Basic deadline pruning during domain generation
                    if slot_end <= deadline_hours + 1e-6:
                        values.append({
                            'machine_id': machine.id,
                            'machine_name': machine.name,
                            'machine_code': machine.machine_code,
                            'worker_id': worker.id,
                            'worker_name': worker.name,
                            'worker_code': worker.worker_code,
                            'start_time': hours_to_time(curr),
                            'end_time': hours_to_time(slot_end),
                            'duration': var_duration
                        })

                    curr += slot_step_hours

        return values


class Constraint:
    """Represents a formal constraint in the CSP system."""
    def __init__(self, name, description, category="HARD"):
        self.name = name
        self.description = description
        self.category = category

    def __repr__(self):
        return f"<Constraint [{self.category}] {self.name}>"


class ProductionCSP:
    """Full Constraint Satisfaction Problem formulation for Production Planning."""
    def __init__(self, variables, machines, workers, materials):
        self.variables = variables
        self.machines = machines
        self.workers = workers
        self.materials = materials

        self.machines_dict = {m.id: m for m in machines}
        self.workers_dict = {w.id: w for w in workers}
        self.materials_dict = {mat.id: mat for mat in materials}

        self.context = {
            'machines_dict': self.machines_dict,
            'workers_dict': self.workers_dict,
            'materials_dict': self.materials_dict
        }

        self.hard_constraints = [
            Constraint("No Machine Overlap", "A machine cannot process two tasks at the same time.", "HARD"),
            Constraint("No Worker Overlap", "A worker cannot work on two tasks at the same time.", "HARD"),
            Constraint("Machine Compatibility", "A product can only be assigned to a compatible machine.", "HARD"),
            Constraint("Worker Skill", "A worker must have the skill required by the task.", "HARD"),
            Constraint("Machine Hours Limit", "Machine working hours cannot exceed its daily available capacity.", "HARD"),
            Constraint("Worker Hours Limit", "Worker working hours cannot exceed their daily available capacity.", "HARD"),
            Constraint("Raw Material Availability", "Required raw material stock must be sufficient before scheduling.", "HARD"),
            Constraint("Production Deadline", "Task completion time must be earlier than or equal to deadline.", "HARD"),
            Constraint("Machine Active Status", "Unavailable or maintenance machines cannot be assigned.", "HARD"),
            Constraint("Worker Active Status", "Unavailable or on-leave workers cannot be assigned.", "HARD"),
        ]

        self.initialize_domains()

    def initialize_domains(self):
        """Populate domains for each variable."""
        for var in self.variables:
            var.domain = Domain.generate_domain_for_variable(
                var, self.machines, self.workers, slot_step_hours=1.0
            )


class CSPScheduler:
    """Production Scheduler that interfaces with SQLite Database and runs the CSP Backtracking Solver."""

    def __init__(self, db_session):
        self.db_session = db_session
        self.solver = None
        self.csp = None
        self.solution = None
        self.statistics = {}
        self.diagnostics = {}
        self.decision_explanations = []

    def build_problem(self, products, machines, workers, materials):
        """Convert database entities into CSP variables and domain structure."""
        variables = []
        for prod in products:
            # If quantity > 1, create individual task variables (or per unit/batch)
            units = max(1, int(prod.quantity))
            for i in range(1, units + 1):
                var_id = f"P{prod.id}_T{i}"
                var = CSPVariable(
                    var_id=var_id,
                    product_id=prod.id,
                    product_name=prod.name,
                    product_code=prod.code,
                    task_index=i,
                    duration=prod.production_time,
                    priority=prod.priority,
                    deadline=prod.deadline,
                    required_machine_type=prod.machine_type,
                    material_id=prod.material_id,
                    material_quantity=prod.material_quantity,
                    required_skill=prod.machine_type
                )
                variables.append(var)

        self.csp = ProductionCSP(variables, machines, workers, materials)
        return self.csp

    def run_scheduler(self, products, machines, workers, materials):
        """
        Execute full scheduling pipeline:
        1. Build CSP
        2. Execute Backtracking Search with MRV
        3. Analyze results and generate explanations/diagnostics
        """
        self.build_problem(products, machines, workers, materials)

        if not self.csp.variables:
            return {
                'success': False,
                'message': 'No production tasks or products found to schedule.',
                'statistics': {},
                'diagnostics': {'error': 'No products provided'}
            }

        self.solver = BacktrackingSolver(
            variables=self.csp.variables,
            context=self.csp.context,
            enable_forward_checking=True
        )

        raw_solution = self.solver.solve()
        self.statistics = self.solver.get_statistics()

        if raw_solution is not None:
            self.solution = self._format_solution(raw_solution)
            self._generate_decision_explanations(raw_solution)
            return {
                'success': True,
                'message': 'Optimal conflict-free production schedule generated successfully.',
                'solution': self.solution,
                'statistics': self.statistics,
                'explanations': self.decision_explanations,
                'search_log': self.solver.search_log,
                'trace': self.solver.step_by_step_trace[:30]  # top trace samples
            }
        else:
            self.solution = None
            self._generate_failure_diagnostics(products, machines, workers, materials)
            return {
                'success': False,
                'message': 'Production plan could not be generated due to conflicting constraints.',
                'statistics': self.statistics,
                'diagnostics': self.diagnostics,
                'search_log': self.solver.search_log,
                'trace': self.solver.step_by_step_trace[:30]
            }

    def _format_solution(self, raw_solution):
        """Format raw assignments into ordered list of schedule records."""
        formatted = []
        for var, val in raw_solution.items():
            formatted.append({
                'var_id': var.id,
                'task_name': var.name,
                'product_id': var.product_id,
                'product_name': var.product_name,
                'product_code': var.product_code,
                'priority': var.priority,
                'machine_id': val['machine_id'],
                'machine_name': val['machine_name'],
                'machine_code': val['machine_code'],
                'worker_id': val['worker_id'],
                'worker_name': val['worker_name'],
                'worker_code': val['worker_code'],
                'start_time': val['start_time'],
                'end_time': val['end_time'],
                'duration': val['duration'],
                'deadline': var.deadline,
                'material_id': var.material_id,
                'material_quantity': var.material_quantity
            })
        
        # Sort chronologically by start time, then priority
        def sort_schedule(item):
            return (time_to_hours(item['start_time']), item['machine_id'])

        return sorted(formatted, key=sort_schedule)

    def _generate_decision_explanations(self, raw_solution):
        """Generate human-readable AI justification for each variable's assignment."""
        self.decision_explanations = []
        for var, val in raw_solution.items():
            exp = {
                'task_name': var.name,
                'product_name': var.product_name,
                'assigned_machine': val['machine_name'],
                'assigned_worker': val['worker_name'],
                'time_slot': f"{val['start_time']} – {val['end_time']}",
                'reasons': [
                    f"Machine '{val['machine_name']}' is compatible with type '{var.required_machine_type}' and is in Available status.",
                    f"Worker '{val['worker_name']}' holds the required skill '{var.required_skill}' and is in Available status.",
                    f"Resource time interval ({val['start_time']} – {val['end_time']}) is strictly conflict-free with all other tasks.",
                    f"Daily working hours limits for both machine and worker were verified and not exceeded.",
                    f"Production completion ({val['end_time']}) satisfies deadline requirement (≤ {var.deadline})."
                ]
            }
            if var.material_id:
                mat = self.csp.materials_dict.get(var.material_id)
                mat_name = mat.name if mat else f"ID {var.material_id}"
                exp['reasons'].append(f"Required raw material '{mat_name}' ({var.material_quantity}) was reserved from inventory.")

            self.decision_explanations.append(exp)

    def _generate_failure_diagnostics(self, products, machines, workers, materials):
        """Analyze root causes of unsatisfiable scheduling and provide corrective suggestions."""
        conflicts = []
        suggestions = []

        # 1. Check material availability totals
        material_totals = {}
        for p in products:
            if p.material_id:
                material_totals[p.material_id] = material_totals.get(p.material_id, 0.0) + (float(p.material_quantity) * max(1, p.quantity))

        mat_dict = {m.id: m for m in materials}
        for mat_id, needed in material_totals.items():
            mat = mat_dict.get(mat_id)
            if not mat:
                conflicts.append(f"Product references non-existent raw material ID {mat_id}.")
                suggestions.append(f"Ensure all required raw materials are registered.")
            elif needed > float(mat.quantity):
                conflicts.append(f"Raw material '{mat.name}' shortage: need {needed} {mat.unit}, but only {mat.quantity} {mat.unit} available.")
                suggestions.append(f"Restock '{mat.name}' or reduce production quantity.")

        # 2. Check machine compatibility & status
        active_machines = [m for m in machines if m.status.lower() == 'available']
        if not active_machines:
            conflicts.append("No active machines are currently in 'Available' status.")
            suggestions.append("Check machine maintenance statuses and mark at least one machine as Available.")

        required_machine_types = {p.machine_type.lower() for p in products}
        available_machine_types = {m.machine_type.lower() for m in active_machines}
        missing_types = required_machine_types - available_machine_types
        for mt in missing_types:
            conflicts.append(f"No available machine found of required type '{mt.capitalize()}'.")
            suggestions.append(f"Add or restore a machine with type '{mt.capitalize()}'.")

        # 3. Check worker skills & status
        active_workers = [w for w in workers if w.status.lower() == 'available']
        if not active_workers:
            conflicts.append("No active workers are currently in 'Available' status.")
            suggestions.append("Check worker leaves and ensure at least one worker is Available.")

        available_skills = {w.skill.lower() for w in active_workers}
        missing_skills = required_machine_types - available_skills
        for sk in missing_skills:
            conflicts.append(f"No available worker possesses required skill '{sk.capitalize()}'.")
            suggestions.append(f"Assign or hire a worker with skill '{sk.capitalize()}'.")

        # 4. Check total required duration vs available hours
        total_needed_hours = sum(p.production_time * max(1, p.quantity) for p in products)
        total_machine_hours = sum(m.available_hours for m in active_machines)
        total_worker_hours = sum(w.available_hours for w in active_workers)

        if total_needed_hours > total_machine_hours:
            conflicts.append(f"Total production time ({total_needed_hours}h) exceeds aggregate machine capacity ({total_machine_hours}h).")
            suggestions.append("Increase machine operating hours or add more machines.")

        if total_needed_hours > total_worker_hours:
            conflicts.append(f"Total production time ({total_needed_hours}h) exceeds aggregate worker shift capacity ({total_worker_hours}h).")
            suggestions.append("Increase worker shift hours or assign additional personnel.")

        # 5. Check deadlines
        for p in products:
            p_end = 8.0 + float(p.production_time)
            d_hours = time_to_hours(p.deadline)
            if p_end > d_hours:
                conflicts.append(f"Product '{p.name}' requires {p.production_time}h starting at earliest 08:00, which exceeds deadline {p.deadline}.")
                suggestions.append(f"Extend deadline for '{p.name}' to at least {hours_to_time(p_end)}.")

        # 6. Fallback if no simple heuristic caught it
        if not conflicts:
            for var_name, reasons in self.solver.conflict_reasons.items():
                for r in reasons[:2]:
                    conflicts.append(f"{var_name}: {r}")
            if not conflicts:
                conflicts.append("Mutual time slot collision: Multiple tasks compete for overlapping resource windows.")
            suggestions.append("Try relaxing task deadlines, adding workers, or staggering production quantities.")

        self.diagnostics = {
            'conflicting_constraints': list(dict.fromkeys(conflicts)),
            'suggestions': list(dict.fromkeys(suggestions))
        }

    def save_schedule_to_db(self, ScheduleModel, ConstraintLogModel, ProductModel):
        """Save the generated schedule and constraint audit logs into the SQLite database."""
        if not self.solution:
            return False

        # Clear existing schedules
        ScheduleModel.query.delete()
        ConstraintLogModel.query.delete()

        # Update product status to 'Scheduled'
        for item in self.solution:
            prod = self.db_session.get(ProductModel, item['product_id'])
            if prod:
                prod.status = 'Scheduled'

            sched = ScheduleModel(
                product_id=item['product_id'],
                machine_id=item['machine_id'],
                worker_id=item['worker_id'],
                start_time=item['start_time'],
                end_time=item['end_time'],
                status='Scheduled',
                created_at=datetime.now()
            )
            self.db_session.add(sched)
            self.db_session.flush()

            # Record audit constraints log
            for hard_c in self.csp.hard_constraints:
                log_entry = ConstraintLogModel(
                    schedule_id=sched.id,
                    constraint_name=hard_c.name,
                    result='PASS',
                    explanation=f"Constraint '{hard_c.name}' satisfied: {hard_c.description}"
                )
                self.db_session.add(log_entry)

        self.db_session.commit()
        return True
