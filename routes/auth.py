from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.models import db, User

auth_bp = Blueprint('auth', __name__)

def is_safe_url(target):
    """Ensure redirect target is local and not an open redirect vulnerability."""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Authentication login endpoint. Strictly login only, no signup."""
    # If already logged in, redirect to home
    if session.get('user_id'):
        return redirect(url_for('planner.home'))

    next_url = request.args.get('next') or request.form.get('next') or ''

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template('login.html', username=username, next=next_url)

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash("Invalid credentials. Please verify your username and password.", "danger")
            return render_template('login.html', username=username, next=next_url)

        # Login successful
        session.clear()
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role

        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        flash(f"Welcome back, {user.username}! Access granted.", "success")

        if next_url and is_safe_url(next_url):
            return redirect(next_url)
        return redirect(url_for('planner.home'))

    return render_template('login.html', next=next_url)

@auth_bp.route('/logout')
def logout():
    """Terminate user session safely."""
    username = session.get('username', 'User')
    session.clear()
    flash(f"You have been safely logged out, {username}.", "info")
    return redirect(url_for('auth.login'))
