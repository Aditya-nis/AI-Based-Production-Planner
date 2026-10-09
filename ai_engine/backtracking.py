"""
Recursive Backtracking CSP Solver with MRV and Forward Checking.

Instruments:
- Variables count
- Initial domain sizes
- Assignments tried
- Backtracks count
- Constraints checked count
- Real-time execution tracing
- Conflict diagnostics on failure
"""

import time
from .heuristics import select_unassigned_variable_mrv, order_domain_values
from .constraints import check_all_constraints

class BacktrackingSolver:
    def __init__(self, variables, context, enable_forward_checking=True):
        """
        Parameters:
            variables: List of CSPVariable objects
            context: dict with {'machines_dict', 'workers_dict', 'materials_dict'}
            enable_forward_checking: bool
        """
        self.variables = variables
        self.context = context
        self.enable_forward_checking = enable_forward_checking

        # Statistics
        self.variables_count = len(variables)
        self.initial_domain_size = sum(len(v.domain) for v in variables)
        self.assignments_tried = 0
        self.backtracks = 0
        self.constraints_checked = 0
        self.solution_found = False
        self.execution_time_ms = 0.0

        # Detailed logs & diagnostics
        self.search_log = []
        self.conflict_reasons = {}  # {var_name: [list of failure reasons]}
        self.step_by_step_trace = []

    def solve(self):
        """Execute the backtracking search and return the solution mapping or None."""
        start_clock = time.perf_counter()
        current_assignments = {}

        self.search_log.append(
            f"Starting Backtracking Search for {self.variables_count} variables. "
            f"Total initial domain combinations: {self.initial_domain_size}."
        )

        solution = self._backtrack(current_assignments)

        self.execution_time_ms = round((time.perf_counter() - start_clock) * 1000, 2)
        self.solution_found = (solution is not None)

        if self.solution_found:
            self.search_log.append(
                f"Solution successfully found in {self.execution_time_ms} ms! "
                f"Tried {self.assignments_tried} assignments with {self.backtracks} backtracks."
            )
        else:
            self.search_log.append(
                f"Search exhausted after {self.assignments_tried} attempts and {self.backtracks} backtracks. "
                "No conflict-free schedule satisfies all constraints."
            )

        return solution

    def _backtrack(self, current_assignments):
        """Recursive backtracking core."""
        # 1. Base case: All variables assigned
        if len(current_assignments) == len(self.variables):
            return current_assignments

        # 2. Variable Selection using MRV (Minimum Remaining Values)
        unassigned_vars = [v for v in self.variables if v not in current_assignments]
        var, remaining_count = select_unassigned_variable_mrv(
            unassigned_vars, current_assignments, self.context, self._check_constraint_wrapper
        )

        if var is None:
            return None

        self.step_by_step_trace.append(
            f"MRV selected variable '{var.name}' (remaining valid options: {remaining_count})"
        )

        # 3. Order domain values (Earliest start time first)
        ordered_values = order_domain_values(var, current_assignments, self.context)

        # 4. Try each value in domain
        for value in ordered_values:
            self.assignments_tried += 1

            # Check all hard constraints
            is_valid, reason = self._check_constraint_wrapper(var, value, current_assignments, self.context)
            
            if is_valid:
                # Tentatively assign
                current_assignments[var] = value
                self.step_by_step_trace.append(
                    f"Tentatively assigned '{var.name}' -> Machine: {value['machine_name']}, "
                    f"Worker: {value['worker_name']}, Time: {value['start_time']}-{value['end_time']}"
                )

                # Forward Checking: ensure no remaining unassigned variable is left with 0 domain
                if self.enable_forward_checking:
                    failure_var = self._forward_check(current_assignments)
                    if failure_var is not None:
                        # Forward check detected domain wipeout! Backtrack early.
                        self.backtracks += 1
                        self.step_by_step_trace.append(
                            f"Forward check failed: assigning '{var.name}' wipes out domain for '{failure_var.name}'. Backtracking."
                        )
                        del current_assignments[var]
                        continue

                # Recurse
                result = self._backtrack(current_assignments)
                if result is not None:
                    return result

                # Backtrack if recursion failed
                self.backtracks += 1
                self.step_by_step_trace.append(
                    f"Backtracking from '{var.name}' (no downstream solution)."
                )
                del current_assignments[var]
            else:
                # Record conflict for AI diagnostic report
                if var.name not in self.conflict_reasons:
                    self.conflict_reasons[var.name] = []
                if reason not in self.conflict_reasons[var.name]:
                    self.conflict_reasons[var.name].append(reason)

        return None

    def _check_constraint_wrapper(self, var, value, current_assignments, context):
        """Wrapper to count constraint checks and validate."""
        self.constraints_checked += 1
        return check_all_constraints(var, value, current_assignments, context)

    def _forward_check(self, current_assignments):
        """
        Verify that all remaining unassigned variables still have at least 1 valid value.
        Returns the variable that has an empty domain, or None if all have >= 1.
        """
        for var in self.variables:
            if var not in current_assignments:
                has_valid = False
                for val in var.domain:
                    is_valid, _ = self._check_constraint_wrapper(var, val, current_assignments, self.context)
                    if is_valid:
                        has_valid = True
                        break
                if not has_valid:
                    return var
        return None

    def get_statistics(self):
        """Return execution statistics dictionary."""
        return {
            'variables_count': self.variables_count,
            'initial_domain_size': self.initial_domain_size,
            'assignments_tried': self.assignments_tried,
            'backtracks': self.backtracks,
            'constraints_checked': self.constraints_checked,
            'solution_found': self.solution_found,
            'execution_time_ms': self.execution_time_ms
        }
