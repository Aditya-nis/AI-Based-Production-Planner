from .dashboard import dashboard_bp
from .products import products_bp
from .machines import machines_bp
from .workers import workers_bp
from .materials import materials_bp
from .planner import planner_bp
from .auth import auth_bp
from .admin import admin_bp

__all__ = [
    'dashboard_bp',
    'products_bp',
    'machines_bp',
    'workers_bp',
    'materials_bp',
    'planner_bp',
    'auth_bp',
    'admin_bp'
]
