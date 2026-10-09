from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.models import db, Machine

machines_bp = Blueprint('machines', __name__)

@machines_bp.route('/machines', methods=['GET'])
def list_machines():
    machines = Machine.query.order_by(Machine.id.asc()).all()
    return render_template('machines.html', machines=machines)

@machines_bp.route('/machines/add', methods=['POST'])
def add_machine():
    try:
        name = request.form.get('name', '').strip()
        code = request.form.get('machine_code', '').strip().upper()
        m_type = request.form.get('machine_type', 'Assembly').strip()
        capacity = int(request.form.get('capacity', 1))
        hours = float(request.form.get('available_hours', 8.0))
        start = request.form.get('start_time', '08:00').strip()
        end = request.form.get('end_time', '17:00').strip()
        status = request.form.get('status', 'Available')

        if not name or not code:
            flash('Machine Name and Code are required.', 'danger')
            return redirect(url_for('machines.list_machines'))

        if Machine.query.filter_by(machine_code=code).first():
            flash(f'Machine Code {code} already exists.', 'warning')
            return redirect(url_for('machines.list_machines'))

        mach = Machine(
            name=name,
            machine_code=code,
            machine_type=m_type,
            capacity=max(1, capacity),
            available_hours=max(1.0, hours),
            start_time=start,
            end_time=end,
            status=status
        )
        db.session.add(mach)
        db.session.commit()
        flash(f'Machine "{name}" added successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding machine: {str(e)}', 'danger')

    return redirect(url_for('machines.list_machines'))

@machines_bp.route('/machines/edit/<int:machine_id>', methods=['POST'])
def edit_machine(machine_id):
    mach = db.get_or_404(Machine, machine_id)
    try:
        mach.name = request.form.get('name', mach.name).strip()
        mach.machine_code = request.form.get('machine_code', mach.machine_code).strip().upper()
        mach.machine_type = request.form.get('machine_type', mach.machine_type).strip()
        mach.capacity = max(1, int(request.form.get('capacity', mach.capacity)))
        mach.available_hours = max(1.0, float(request.form.get('available_hours', mach.available_hours)))
        mach.start_time = request.form.get('start_time', mach.start_time).strip()
        mach.end_time = request.form.get('end_time', mach.end_time).strip()
        mach.status = request.form.get('status', mach.status)
        db.session.commit()
        flash(f'Machine "{mach.name}" updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating machine: {str(e)}', 'danger')

    return redirect(url_for('machines.list_machines'))

@machines_bp.route('/machines/toggle-status/<int:machine_id>', methods=['POST'])
def toggle_status(machine_id):
    mach = db.get_or_404(Machine, machine_id)
    new_status = request.form.get('status', 'Maintenance')
    mach.status = new_status
    db.session.commit()
    flash(f'Machine "{mach.name}" status updated to {new_status}. You can now test rescheduling.', 'info')
    return redirect(url_for('machines.list_machines'))

@machines_bp.route('/machines/delete/<int:machine_id>', methods=['POST', 'GET'])
def delete_machine(machine_id):
    mach = db.get_or_404(Machine, machine_id)
    try:
        db.session.delete(mach)
        db.session.commit()
        flash(f'Machine "{mach.name}" deleted successfully.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting machine: {str(e)}', 'danger')

    return redirect(url_for('machines.list_machines'))
