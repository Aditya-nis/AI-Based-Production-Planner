"""
Constraint Checking Functions for AI Production Planning.

Implements Hard Constraints for the Constraint Satisfaction Problem (CSP):
1. No Machine Overlap: A machine cannot process two tasks at the same time.
2. No Worker Overlap: A worker cannot work on two tasks at the same time.
3. Machine Compatibility: Product can only be assigned to a compatible machine.
4. Worker Skill Compatibility: Worker must have the skill required by the task.
5. Machine Working Hours: Machine available hours / shift limits cannot be exceeded.
6. Worker Working Hours: Worker available hours / shift limits cannot be exceeded.
7. Raw Material Availability: Required raw materials must be in stock.
8. Production Deadline: Task must be completed before the specified deadline.
9. Machine Status: Unavailable/Maintenance machines cannot be assigned.
10. Worker Status: Unavailable/On-leave workers cannot be assigned.
"""

def time_to_hours(time_str):
    """Convert 'HH:MM' string to decimal hours (e.g., '09:30' -> 9.5)."""
    if isinstance(time_str, (int, float)):
        return float(time_str)
    try:
        parts = str(time_str).strip().split(':')
        h = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 else 0
        return h + m / 60.0
    except (ValueError, IndexError):
        return 0.0

def hours_to_time(hours_val):
    """Convert decimal hours to 'HH:MM' string."""
    h = int(hours_val)
    m = int(round((hours_val - h) * 60))
    if m >= 60:
        h += 1
        m = 0
    return f"{h:02d}:{m:02d}"

def is_overlapping(start1, end1, start2, end2):
    """Check if two time intervals [start1, end1) and [start2, end2) overlap."""
    s1, e1 = time_to_hours(start1), time_to_hours(end1)
    s2, e2 = time_to_hours(start2), time_to_hours(end2)
    return max(s1, s2) < min(e1, e2)


def check_machine_conflict(assignment_value, existing_assignments):
    """
    Check if the assigned machine has a time conflict with any existing assignment.
    Hard Constraint 1: A machine cannot process two tasks at the same time.
    """
    machine_id = assignment_value['machine_id']
    start = assignment_value['start_time']
    end = assignment_value['end_time']

    for var, val in existing_assignments.items():
        if val['machine_id'] == machine_id:
            if is_overlapping(start, end, val['start_time'], val['end_time']):
                return False, f"Machine '{val['machine_name']}' is already assigned to {var.name} during {val['start_time']}-{val['end_time']}."
    return True, "No machine conflict."


def check_worker_conflict(assignment_value, existing_assignments):
    """
    Check if the assigned worker has a time conflict with any existing assignment.
    Hard Constraint 2: A worker cannot work on two tasks at the same time.
    """
    worker_id = assignment_value['worker_id']
    start = assignment_value['start_time']
    end = assignment_value['end_time']

    for var, val in existing_assignments.items():
        if val['worker_id'] == worker_id:
            if is_overlapping(start, end, val['start_time'], val['end_time']):
                return False, f"Worker '{val['worker_name']}' is already assigned to {var.name} during {val['start_time']}-{val['end_time']}."
    return True, "No worker conflict."


def check_machine_compatibility(task, machine):
    """
    Check if machine type matches task's required machine type.
    Hard Constraint 3: A product can only be assigned to a compatible machine.
    """
    req_type = str(task.required_machine_type).strip().lower()
    mach_type = str(machine.machine_type).strip().lower()
    if req_type != mach_type and req_type != 'all' and req_type != 'any':
        return False, f"Machine '{machine.name}' type ({machine.machine_type}) does not match required ({task.required_machine_type})."
    return True, "Machine is compatible."


def check_worker_skill(task, worker):
    """
    Check if worker's skill matches task requirements.
    Hard Constraint 4: Worker must have the required skill.
    """
    req_skill = str(task.required_skill or task.required_machine_type).strip().lower()
    w_skill = str(worker.skill).strip().lower()
    if req_skill != w_skill and w_skill != 'all' and w_skill != 'general':
        return False, f"Worker '{worker.name}' skill ({worker.skill}) does not match required skill ({req_skill})."
    return True, "Worker has required skill."


def check_machine_capacity(machine, assigned_hours, new_hours):
    """
    Check if total assigned hours on machine exceed available hours.
    Hard Constraint 5: Machine working hours cannot be exceeded.
    """
    if (assigned_hours + new_hours) > float(machine.available_hours) + 1e-6:
        return False, f"Machine '{machine.name}' maximum daily hours ({machine.available_hours}h) would be exceeded by {new_hours}h."
    return True, "Machine capacity satisfied."


def check_worker_hours(worker, assigned_hours, new_hours):
    """
    Check if total assigned hours for worker exceed available hours.
    Hard Constraint 6: Worker working hours cannot be exceeded.
    """
    if (assigned_hours + new_hours) > float(worker.available_hours) + 1e-6:
        return False, f"Worker '{worker.name}' maximum shift hours ({worker.available_hours}h) would be exceeded by {new_hours}h."
    return True, "Worker working hours satisfied."


def check_material_availability(task, allocated_materials, raw_materials_dict):
    """
    Check if sufficient raw materials exist in inventory for this task.
    Hard Constraint 7: Required raw material must be available.
    """
    if not task.material_id:
        return True, "No raw material required."
    
    mat = raw_materials_dict.get(task.material_id)
    if not mat:
        return False, f"Required raw material (ID {task.material_id}) not found in inventory."
    
    already_used = allocated_materials.get(task.material_id, 0.0)
    needed = float(task.material_quantity)
    available = float(mat.quantity)

    if (already_used + needed) > available:
        return False, f"Insufficient material '{mat.name}'. Available: {available} {mat.unit}, Required total: {already_used + needed} {mat.unit}."
    return True, "Material available."


def check_deadline(assignment_value, task):
    """
    Check if the task's end time is within or before the deadline.
    Hard Constraint 8: Production must be completed before the deadline.
    """
    end_h = time_to_hours(assignment_value['end_time'])
    deadline_h = time_to_hours(task.deadline)
    if end_h > deadline_h + 1e-6:
        return False, f"Task {task.name} ends at {assignment_value['end_time']}, which is past deadline {task.deadline}."
    return True, "Deadline satisfied."


def check_machine_status(machine):
    """
    Check if machine status is 'Available'.
    Hard Constraint 9: Unavailable or maintenance machines cannot be assigned.
    """
    if str(machine.status).strip().lower() != 'available':
        return False, f"Machine '{machine.name}' is currently {machine.status}."
    return True, "Machine is available."


def check_worker_status(worker):
    """
    Check if worker status is 'Available'.
    Hard Constraint 10: Unavailable or on-leave workers cannot be assigned.
    """
    if str(worker.status).strip().lower() != 'available':
        return False, f"Worker '{worker.name}' is currently {worker.status}."
    return True, "Worker is available."


def check_all_constraints(var, value, current_assignments, context):
    """
    Central function to validate all 10 hard constraints for assigning 'value' to 'var'.
    
    Parameters:
        var: CSPVariable instance
        value: dict with keys {'machine_id', 'machine_name', 'worker_id', 'worker_name', 'start_time', 'end_time'}
        current_assignments: dict mapping CSPVariable -> assigned value dict
        context: dict containing machines_dict, workers_dict, materials_dict

    Returns:
        (bool, str): (True, "VALID") or (False, "INVALID: <reason>")
    """
    machine = context['machines_dict'].get(value['machine_id'])
    worker = context['workers_dict'].get(value['worker_id'])
    materials_dict = context.get('materials_dict', {})

    if not machine:
        return False, f"INVALID: Machine ID {value['machine_id']} not found."
    if not worker:
        return False, f"INVALID: Worker ID {value['worker_id']} not found."

    # 1. Machine Status
    ok, reason = check_machine_status(machine)
    if not ok:
        return False, f"INVALID: {reason}"

    # 2. Worker Status
    ok, reason = check_worker_status(worker)
    if not ok:
        return False, f"INVALID: {reason}"

    # 3. Machine Compatibility
    ok, reason = check_machine_compatibility(var, machine)
    if not ok:
        return False, f"INVALID: {reason}"

    # 4. Worker Skill
    ok, reason = check_worker_skill(var, worker)
    if not ok:
        return False, f"INVALID: {reason}"

    # 5. Machine Time Overlap Conflict
    ok, reason = check_machine_conflict(value, current_assignments)
    if not ok:
        return False, f"INVALID: {reason}"

    # 6. Worker Time Overlap Conflict
    ok, reason = check_worker_conflict(value, current_assignments)
    if not ok:
        return False, f"INVALID: {reason}"

    # 7. Machine Daily Working Hours
    # Calculate machine's currently assigned total hours
    task_duration = time_to_hours(value['end_time']) - time_to_hours(value['start_time'])
    assigned_machine_hours = sum(
        time_to_hours(val['end_time']) - time_to_hours(val['start_time'])
        for v, val in current_assignments.items()
        if val['machine_id'] == value['machine_id']
    )
    ok, reason = check_machine_capacity(machine, assigned_machine_hours, task_duration)
    if not ok:
        return False, f"INVALID: {reason}"

    # 8. Worker Daily Working Hours
    assigned_worker_hours = sum(
        time_to_hours(val['end_time']) - time_to_hours(val['start_time'])
        for v, val in current_assignments.items()
        if val['worker_id'] == value['worker_id']
    )
    ok, reason = check_worker_hours(worker, assigned_worker_hours, task_duration)
    if not ok:
        return False, f"INVALID: {reason}"

    # 9. Raw Material Availability
    allocated_materials = {}
    for v, val in current_assignments.items():
        if v.material_id:
            allocated_materials[v.material_id] = allocated_materials.get(v.material_id, 0.0) + float(v.material_quantity)
    ok, reason = check_material_availability(var, allocated_materials, materials_dict)
    if not ok:
        return False, f"INVALID: {reason}"

    # 10. Deadline
    ok, reason = check_deadline(value, var)
    if not ok:
        return False, f"INVALID: {reason}"

    return True, "VALID"
