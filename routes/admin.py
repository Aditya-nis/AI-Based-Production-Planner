from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.models import db, User, Product, Machine, Worker, Material, Schedule

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required():
    """Verify session has an active admin user."""
    user_id = session.get('user_id')
    if not user_id:
        return False, redirect(url_for('auth.login', next=request.path))
    user = db.session.get(User, user_id)
    if not user or user.role != 'admin':
        flash("Admin privileges required to access the admin portal.", "danger")
        return False, redirect(url_for('planner.home'))
    return True, user

@admin_bp.route('/')
def admin_panel():
    """Django-style Admin Portal & Credential Management."""
    is_ok, result = admin_required()
    if not is_ok:
        return result
    current_admin = result

    # Fetch all system users
    users = User.query.order_by(User.id.asc()).all()

    # System counts for administrative audit
    stats = {
        'user_count': User.query.count(),
        'product_count': Product.query.count(),
        'machine_count': Machine.query.count(),
        'worker_count': Worker.query.count(),
        'material_count': Material.query.count(),
        'schedule_count': Schedule.query.count(),
    }

    return render_template(
        'admin.html',
        current_admin=current_admin,
        users=users,
        stats=stats
    )

@admin_bp.route('/credentials', methods=['POST'])
def update_credentials():
    """Update current logged-in administrator's username and/or password."""
    is_ok, result = admin_required()
    if not is_ok:
        return result
    current_admin = result

    new_username = request.form.get('username', '').strip()
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    # Current password verification is mandatory for security
    if not current_password or not current_admin.check_password(current_password):
        flash("Security verification failed: Current password is incorrect.", "danger")
        return redirect(url_for('admin.admin_panel'))

    # Handle username update
    if new_username and new_username != current_admin.username:
        existing = User.query.filter_by(username=new_username).first()
        if existing and existing.id != current_admin.id:
            flash(f"Username '{new_username}' is already in use by another account.", "danger")
            return redirect(url_for('admin.admin_panel'))
        current_admin.username = new_username
        session['username'] = new_username

    # Handle password update
    if new_password:
        if len(new_password) < 4:
            flash("New password must be at least 4 characters long.", "warning")
            return redirect(url_for('admin.admin_panel'))
        if new_password != confirm_password:
            flash("New password and confirm password do not match.", "danger")
            return redirect(url_for('admin.admin_panel'))
        current_admin.set_password(new_password)

    db.session.commit()
    flash("Admin credentials successfully updated! Use your new credentials for future logins.", "success")
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/users/create', methods=['POST'])
def create_user():
    """Create a new system user from the Admin Panel."""
    is_ok, result = admin_required()
    if not is_ok:
        return result

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    role = request.form.get('role', 'admin').strip()

    if not username or not password:
        flash("Username and password are required.", "danger")
        return redirect(url_for('admin.admin_panel'))

    if len(password) < 4:
        flash("Password must be at least 4 characters long.", "warning")
        return redirect(url_for('admin.admin_panel'))

    if password != confirm_password:
        flash("Password and confirmation do not match.", "danger")
        return redirect(url_for('admin.admin_panel'))

    if User.query.filter_by(username=username).first():
        flash(f"User '{username}' already exists.", "danger")
        return redirect(url_for('admin.admin_panel'))

    new_user = User(username=username, role=role)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    flash(f"Admin user '{username}' successfully created.", "success")
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    """Safely delete an admin user."""
    is_ok, result = admin_required()
    if not is_ok:
        return result
    current_admin = result

    if user_id == current_admin.id:
        flash("You cannot delete your own active administrator account.", "danger")
        return redirect(url_for('admin.admin_panel'))

    user_to_delete = db.session.get(User, user_id)
    if not user_to_delete:
        flash("User not found.", "warning")
        return redirect(url_for('admin.admin_panel'))

    if User.query.count() <= 1:
        flash("Cannot delete the only remaining user in the system.", "danger")
        return redirect(url_for('admin.admin_panel'))

    db.session.delete(user_to_delete)
    db.session.commit()
    flash(f"User '{user_to_delete.username}' was deleted.", "info")
    return redirect(url_for('admin.admin_panel'))
