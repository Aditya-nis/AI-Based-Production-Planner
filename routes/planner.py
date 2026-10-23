import io
import csv
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response, current_app
from models.models import db, Product, Machine, Worker, Material, Schedule, ConstraintLog
from models.demo_data import load_demo_data
from ai_engine.csp_scheduler import CSPScheduler
from ai_engine.constraints import time_to_hours

planner_bp = Blueprint('planner', __name__)

# Global in-memory cache of latest AI run result for real-time explanations and statistics
latest_ai_run = {
    'executed': False,
    'success': False,
    'message': '',
    'statistics': {},
    'diagnostics': {},
    'explanations': [],
    'search_log': [],
    'trace': []
}

@planner_bp.route('/')
def home():
    """Page 1 — Home Landing Page"""
    products_count = Product.query.count()
    machines_count = Machine.query.count()
    workers_count = Worker.query.count()
    schedules_count = Schedule.query.count()
    return render_template(
        'index.html',
        products_count=products_count,
        machines_count=machines_count,
        workers_count=workers_count,
        schedules_count=schedules_count,
        latest_ai=latest_ai_run
    )

@planner_bp.route('/planner')
def planner_view():
    """Page 10 — AI Production Planner Page"""
    products = Product.query.all()
    machines = Machine.query.all()
    workers = Worker.query.all()
    materials = Material.query.all()
    active_schedule_count = Schedule.query.count()

    return render_template(
        'planner.html',
        products=products,
        machines=machines,
        workers=workers,
        materials=materials,
        active_schedule_count=active_schedule_count,
        latest_ai=latest_ai_run
    )

@planner_bp.route('/planner/generate', methods=['POST'])
def generate_plan():
    """
    Main AI CSP Execution:
    1. Fetch products, machines, workers, materials
    2. Build CSP variables and domains
    3. Run Backtracking Search with MRV and constraint checking
    4. Save generated schedule to SQLite if successful
    5. Return JSON or redirect with complete explanation
    """
    global latest_ai_run

    products = Product.query.all()
    machines = Machine.query.all()
    workers = Worker.query.all()
    materials = Material.query.all()

    scheduler = CSPScheduler(db_session=db.session)
    result = scheduler.run_scheduler(products, machines, workers, materials)

    latest_ai_run['executed'] = True
    latest_ai_run['success'] = result['success']
    latest_ai_run['message'] = result['message']
    latest_ai_run['statistics'] = result.get('statistics', {})
    latest_ai_run['diagnostics'] = result.get('diagnostics', {})
    latest_ai_run['explanations'] = result.get('explanations', [])
    latest_ai_run['search_log'] = result.get('search_log', [])
    latest_ai_run['trace'] = result.get('trace', [])

    if result['success']:
        # Persist schedule into SQLite
        scheduler.save_schedule_to_db(Schedule, ConstraintLog, Product)
        flash('AI Production Plan successfully generated and saved!', 'success')
    else:
        flash(result['message'], 'danger')

    # Return JSON if requested via AJAX, else redirect
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify(result)

    return redirect(url_for('planner.schedule_view'))


@planner_bp.route('/schedule')
def schedule_view():
    """Page 16 — Production Schedule Page"""
    # Filters
    product_filter = request.args.get('product')
    machine_filter = request.args.get('machine')
    worker_filter = request.args.get('worker')
    priority_filter = request.args.get('priority')
    status_filter = request.args.get('status')

    query = Schedule.query.join(Product).join(Machine).join(Worker)

    if product_filter and product_filter != 'all':
        query = query.filter(Product.id == int(product_filter))
    if machine_filter and machine_filter != 'all':
        query = query.filter(Machine.id == int(machine_filter))
    if worker_filter and worker_filter != 'all':
        query = query.filter(Worker.id == int(worker_filter))
    if priority_filter and priority_filter != 'all':
        query = query.filter(Product.priority == priority_filter)
    if status_filter and status_filter != 'all':
        query = query.filter(Schedule.status == status_filter)

    schedules = query.order_by(Schedule.start_time.asc()).all()

    products = Product.query.all()
    machines = Machine.query.all()
    workers = Worker.query.all()

    return render_template(
        'schedule.html',
        schedules=schedules,
        products=products,
        machines=machines,
        workers=workers,
        selected_product=product_filter,
        selected_machine=machine_filter,
        selected_worker=worker_filter,
        selected_priority=priority_filter,
        selected_status=status_filter,
        latest_ai=latest_ai_run
    )

@planner_bp.route('/schedule/clear', methods=['POST'])
def clear_schedule():
    """Clear all schedules and reset product statuses."""
    try:
        ConstraintLog.query.delete()
        Schedule.query.delete()
        for p in Product.query.all():
            p.status = 'Pending'
        db.session.commit()
        
        latest_ai_run['executed'] = False
        latest_ai_run['success'] = False
        latest_ai_run['explanations'] = []
        flash('Production schedule cleared successfully.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error clearing schedule: {str(e)}', 'danger')

    return redirect(url_for('planner.schedule_view'))


@planner_bp.route('/schedule/export')
def export_csv():
    """Export schedule as CSV."""
    schedules = Schedule.query.order_by(Schedule.start_time.asc()).all()

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Product', 'Product Code', 'Quantity', 'Machine', 'Worker', 'Start Time', 'End Time', 'Priority', 'Status'])

    for s in schedules:
        cw.writerow([
            s.product.name if s.product else '',
            s.product.code if s.product else '',
            s.product.quantity if s.product else '',
            s.machine.name if s.machine else '',
            s.worker.name if s.worker else '',
            s.start_time,
            s.end_time,
            s.product.priority if s.product else '',
            s.status
        ])

    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=production_schedule.csv"}
    )


@planner_bp.route('/utilization')
def utilization_view():
    """Page 17 — Resource Utilization Page"""
    machines = Machine.query.all()
    workers = Worker.query.all()
    schedules = Schedule.query.all()

    machine_stats = []
    for m in machines:
        used = sum(
            time_to_hours(s.end_time) - time_to_hours(s.start_time)
            for s in schedules if s.machine_id == m.id
        )
        avail = float(m.available_hours) if float(m.available_hours) > 0 else 8.0
        util_pct = round((used / avail) * 100, 1)
        machine_stats.append({
            'name': m.name,
            'code': m.machine_code,
            'type': m.machine_type,
            'status': m.status,
            'used_hours': round(used, 1),
            'available_hours': avail,
            'utilization': min(100.0, util_pct)
        })

    worker_stats = []
    for w in workers:
        used = sum(
            time_to_hours(s.end_time) - time_to_hours(s.start_time)
            for s in schedules if s.worker_id == w.id
        )
        avail = float(w.available_hours) if float(w.available_hours) > 0 else 8.0
        util_pct = round((used / avail) * 100, 1)
        worker_stats.append({
            'name': w.name,
            'code': w.worker_code,
            'skill': w.skill,
            'status': w.status,
            'used_hours': round(used, 1),
            'available_hours': avail,
            'utilization': min(100.0, util_pct)
        })

    # Distribution by product
    product_distribution = {}
    for s in schedules:
        p_name = s.product.name if s.product else "Unknown"
        product_distribution[p_name] = product_distribution.get(p_name, 0) + 1

    return render_template(
        'utilization.html',
        machine_stats=machine_stats,
        worker_stats=worker_stats,
        product_distribution=product_distribution
    )


@planner_bp.route('/constraints')
def constraints_view():
    """Page 9 — Constraints Information Page"""
    logs = ConstraintLog.query.order_by(ConstraintLog.id.desc()).limit(50).all()
    return render_template('constraints.html', logs=logs)


@planner_bp.route('/ai-explanation')
def ai_explanation_view():
    """Page 21 — How the AI Works & Viva Explanation Page"""
    return render_template('ai_explanation.html', latest_ai=latest_ai_run)


@planner_bp.route('/load-demo', methods=['POST', 'GET'])
def load_demo():
    """Load Demo Data endpoint."""
    try:
        load_demo_data()
        flash('Demo data loaded successfully! 4 products, 3 machines, 4 workers, and 4 raw materials added.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error loading demo data: {str(e)}', 'danger')

    return redirect(url_for('planner.planner_view'))
