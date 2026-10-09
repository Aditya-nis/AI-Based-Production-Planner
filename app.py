import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from config import Config
from models.models import db, Product, User
from models.demo_data import load_demo_data, ensure_default_admin
from routes import (
    dashboard_bp,
    products_bp,
    machines_bp,
    workers_bp,
    materials_bp,
    planner_bp,
    auth_bp,
    admin_bp
)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure database folder exists when running locally
    if not Config.is_vercel:
        os.makedirs(os.path.join(app.root_path, 'database'), exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(planner_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(machines_bp)
    app.register_blueprint(workers_bp)
    app.register_blueprint(materials_bp)

    # Global Authentication Protection Hook
    # Gating the entire site: no one can access the landing page or any resource without login
    @app.before_request
    def enforce_authentication():
        # Allowed unauthenticated endpoints
        allowed_endpoints = {'auth.login', 'static'}

        if request.endpoint is None:
            return

        if request.endpoint.startswith('static'):
            return

        if request.endpoint not in allowed_endpoints:
            if 'user_id' not in session:
                if request.path.startswith('/api/') or request.is_json:
                    return jsonify({'error': 'Unauthorized', 'message': 'Authentication required. Please login.'}), 401
                return redirect(url_for('auth.login', next=request.path))

    # Inject current user into all Jinja templates
    @app.context_processor
    def inject_current_user():
        current_user = None
        if 'user_id' in session:
            current_user = db.session.get(User, session['user_id'])
        return {'current_user': current_user}

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('base.html', content_error="404 - Page Not Found"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('base.html', content_error="500 - Internal Server Error"), 500

    # Auto initialize DB and load demo data if fresh
    with app.app_context():
        db.create_all()
        ensure_default_admin()
        # Seed demo data if database has no products yet
        if Product.query.count() == 0:
            load_demo_data()

    return app

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print(" AI-Based Production/Resource Planning using CSP ")
    print(" Running on: http://127.0.0.1:5000 ")
    print(" Admin Login: Username: 'admin' | Default Password: 'admin123' ")
    print(" Admin Portal: http://127.0.0.1:5000/admin ")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=5000)
