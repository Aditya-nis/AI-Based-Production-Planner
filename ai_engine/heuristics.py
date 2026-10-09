"""
Heuristics for CSP Search in AI Production Planning.

Implements:
1. MRV (Minimum Remaining Values) Heuristic:
   Selects the unassigned variable with the fewest remaining legal domain values.
2. Priority Tie-Breaking / Variable Ordering:
   High Priority > Medium Priority > Low Priority.
3. Value Ordering:
   Orders domain values by earliest start time and resource balance.
"""

PRIORITY_MAP = {
    'high': 3,
    'medium': 2,
    'low': 1
}

def get_remaining_valid_domain(var, current_assignments, context, constraint_checker):
    """
    Calculate the number of legal values remaining in the domain of 'var'
    given current assignments and constraints.
    """
    valid_values = []
    for val in var.domain:
        is_valid, _ = constraint_checker(var, val, current_assignments, context)
        if is_valid:
            valid_values.append(val)
    return valid_values


def select_unassigned_variable_mrv(unassigned_vars, current_assignments, context, constraint_checker):
    """
    MRV (Minimum Remaining Values) Heuristic:
    Select the unassigned variable with the smallest remaining legal domain.
    
    Tie-breaking:
    1. Highest Priority (High > Medium > Low)
    2. Earliest Deadline
    3. Smallest variable ID
    """
    best_var = None
    min_remaining_count = float('inf')
    best_priority_score = -1
    best_deadline = float('inf')

    from .constraints import time_to_hours

    for var in unassigned_vars:
        valid_values = get_remaining_valid_domain(var, current_assignments, context, constraint_checker)
        remaining_count = len(valid_values)

        p_score = PRIORITY_MAP.get(str(var.priority).strip().lower(), 1)
        d_score = time_to_hours(var.deadline)

        # Primary criterion: MRV (Minimum Remaining Values)
        if remaining_count < min_remaining_count:
            min_remaining_count = remaining_count
            best_var = var
            best_priority_score = p_score
            best_deadline = d_score
        elif remaining_count == min_remaining_count:
            # Tie breaker 1: Priority
            if p_score > best_priority_score:
                best_var = var
                best_priority_score = p_score
                best_deadline = d_score
            elif p_score == best_priority_score:
                # Tie breaker 2: Earliest Deadline
                if d_score < best_deadline:
                    best_var = var
                    best_deadline = d_score

    return best_var, min_remaining_count


def order_domain_values(var, current_assignments, context):
    """
    Order the domain values for variable 'var'.
    Preferred heuristic: Earliest start time first, to leave maximum time open for subsequent tasks.
    """
    from .constraints import time_to_hours

    # Sort primarily by start_time, then machine_id
    def sort_key(val):
        return (time_to_hours(val['start_time']), val['machine_id'], val['worker_id'])

    return sorted(var.domain, key=sort_key)
