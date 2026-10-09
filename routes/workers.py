from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.models import db, Worker

workers_bp = Blueprint('workers', __name__)

@workers_bp.route('/workers', methods=['GET'])
def list_workers():
    workers = Worker.query.order_by(Worker.id.asc()).all()
    return render_template('workers.html', workers=workers)

@workers_bp.route('/workers/add', methods=['POST'])
def add_worker():
    try:
        name = request.form.get('name', '').strip()
        code = request.form.get('worker_code', '').strip().upper()
        skill = request.form.get('skill', 'Assembly').strip()
        hours = float(request.form.get('available_hours', 8.0))
        start = request.form.get('start_time', '08:00').strip()
        end = request.form.get('end_time', '17:00').strip()
        status = request.form.get('status', 'Available')

        if not name or not code:
            flash('Worker Name and Code are required.', 'danger')
            return redirect(url_for('workers.list_workers'))

        if Worker.query.filter_by(worker_code=code).first():
            flash(f'Worker Code {code} already exists.', 'warning')
            return redirect(url_for('workers.list_workers'))

        w = Worker(
            name=name,
            worker_code=code,
            skill=skill,
            available_hours=max(1.0, hours),
            start_time=start,
            end_time=end,
            status=status
        )
        db.session.add(w)
        db.session.commit()
        flash(f'Worker "{name}" added successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding worker: {str(e)}', 'danger')

    return redirect(url_for('workers.list_workers'))

@workers_bp.route('/workers/edit/<int:worker_id>', methods=['POST'])
def edit_worker(worker_id):
    w = db.get_or_404(Worker, worker_id)
    try:
        w.name = request.form.get('name', w.name).strip()
        w.worker_code = request.form.get('worker_code', w.worker_code).strip().upper()
        w.skill = request.form.get('skill', w.skill).strip()
        w.available_hours = max(1.0, float(request.form.get('available_hours', w.available_hours)))
        w.start_time = request.form.get('start_time', w.start_time).strip()
        w.end_time = request.form.get('end_time', w.end_time).strip()
        w.status = request.form.get('status', w.status)
        db.session.commit()
        flash(f'Worker "{w.name}" updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating worker: {str(e)}', 'danger')

    return redirect(url_for('workers.list_workers'))

@workers_bp.route('/workers/toggle-status/<int:worker_id>', methods=['POST'])
def toggle_status(worker_id):
    w = db.get_or_404(Worker, worker_id)
    new_status = request.form.get('status', 'Leave')
    w.status = new_status
    db.session.commit()
    flash(f'Worker "{w.name}" status updated to {new_status}.', 'info')
    return redirect(url_for('workers.list_workers'))

@workers_bp.route('/workers/delete/<int:worker_id>', methods=['POST', 'GET'])
def delete_worker(worker_id):
    w = db.get_or_404(Worker, worker_id)
    try:
        db.session.delete(w)
        db.session.commit()
        flash(f'Worker "{w.name}" deleted successfully.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting worker: {str(e)}', 'danger')

    return redirect(url_for('workers.list_workers'))
