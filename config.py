import os
import tempfile

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ai-csp-production-planner-secret-key-2026')

    # Detect Vercel serverless environment (where root filesystem is read-only)
    is_vercel = os.environ.get('VERCEL') == '1' or os.environ.get('VERCEL_ENV') is not None

    if is_vercel:
        db_path = os.path.join(tempfile.gettempdir(), 'production.db')
    else:
        db_dir = os.path.join(BASE_DIR, 'database')
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, 'production.db')

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f"sqlite:///{db_path}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
