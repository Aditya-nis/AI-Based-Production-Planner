from flask import Blueprint, render_template
from models.models import Product, Machine, Worker, Material, Schedule, ConstraintLog
from ai_engine.constraints import time_to_hours

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    products = Product.query.all()
    machines = Machine.query.all()
    workers = Worker.query.all()
    schedules = Schedule.query.all()
    failed_constraints = ConstraintLog.query.filter_by(result='FAIL').count()

    total_products = len(products)
    total_machines = len(machines)
    total_workers = len(workers)
    total_tasks = sum(p.quantity for p in products)
    scheduled_tasks = len(schedules)
    pending_tasks = max(0, total_tasks - scheduled_tasks)

    # Machine utilization calculation
    machine_utilization = {}
    for m in machines:
        used_hours = sum(
            time_to_hours(s.end_time) - time_to_hours(s.start_time)
            for s in schedules if s.machine_id == m.id
        )
        avail = float(m.available_hours) if float(m.available_hours) > 0 else 8.0
        pct = round((used_hours / avail) * 100, 1)
        machine_utilization[m.name] = {
            'used_hours': round(used_hours, 1),
            'available_hours': avail,
            'percentage': min(100.0, pct)
        }

    # Worker utilization calculation
    worker_utilization = {}
    for w in workers:
        used_hours = sum(
            time_to_hours(s.end_time) - time_to_hours(s.start_time)
            for s in schedules if s.worker_id == w.id
        )
        avail = float(w.available_hours) if float(w.available_hours) > 0 else 8.0
        pct = round((used_hours / avail) * 100, 1)
        worker_utilization[w.name] = {
            'used_hours': round(used_hours, 1),
            'available_hours': avail,
            'percentage': min(100.0, pct)
        }

    overall_utilization = 0.0
    if machine_utilization:
        overall_utilization = round(
            sum(v['percentage'] for v in machine_utilization.values()) / len(machine_utilization), 1
        )

    # Priority distribution for charts
    priority_counts = {'High': 0, 'Medium': 0, 'Low': 0}
    for p in products:
        p_name = p.priority.capitalize()
        if p_name in priority_counts:
            priority_counts[p_name] += 1

    return render_template(
        'dashboard.html',
        total_products=total_products,
        total_machines=total_machines,
        total_workers=total_workers,
        total_tasks=total_tasks,
        scheduled_tasks=scheduled_tasks,
        pending_tasks=pending_tasks,
        failed_constraints=failed_constraints,
        overall_utilization=overall_utilization,
        machine_utilization=machine_utilization,
        worker_utilization=worker_utilization,
        priority_counts=priority_counts,
        schedules=schedules[:5]  # recent 5 schedules
    )
