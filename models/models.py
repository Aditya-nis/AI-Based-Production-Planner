from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    production_time = db.Column(db.Float, default=2.0, nullable=False)  # hours needed
    priority = db.Column(db.String(20), default='Medium', nullable=False)  # High, Medium, Low
    deadline = db.Column(db.String(20), default='17:00', nullable=False)  # e.g., '16:00'
    machine_type = db.Column(db.String(50), nullable=False)  # Assembly, Cutting, Drilling, etc.
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=True)
    material_quantity = db.Column(db.Float, default=1.0, nullable=False)
    status = db.Column(db.String(20), default='Pending', nullable=False)  # Pending, Scheduled, Completed

    # Relationship
    material = db.relationship('Material', backref=db.backref('products', lazy=True))
    schedules = db.relationship('Schedule', backref='product', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'quantity': self.quantity,
            'production_time': self.production_time,
            'priority': self.priority,
            'deadline': self.deadline,
            'machine_type': self.machine_type,
            'material_id': self.material_id,
            'material_name': self.material.name if self.material else 'None',
            'material_quantity': self.material_quantity,
            'status': self.status
        }


class Machine(db.Model):
    __tablename__ = 'machines'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    machine_code = db.Column(db.String(50), unique=True, nullable=False)
    machine_type = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.Integer, default=1, nullable=False)
    available_hours = db.Column(db.Float, default=8.0, nullable=False)
    start_time = db.Column(db.String(20), default='08:00', nullable=False)
    end_time = db.Column(db.String(20), default='17:00', nullable=False)
    status = db.Column(db.String(20), default='Available', nullable=False)  # Available, Maintenance, Unavailable

    schedules = db.relationship('Schedule', backref='machine', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'machine_code': self.machine_code,
            'machine_type': self.machine_type,
            'capacity': self.capacity,
            'available_hours': self.available_hours,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'status': self.status
        }


class Worker(db.Model):
    __tablename__ = 'workers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    worker_code = db.Column(db.String(50), unique=True, nullable=False)
    skill = db.Column(db.String(50), nullable=False)  # e.g., Assembly, Cutting, Drilling
    available_hours = db.Column(db.Float, default=8.0, nullable=False)
    start_time = db.Column(db.String(20), default='08:00', nullable=False)
    end_time = db.Column(db.String(20), default='17:00', nullable=False)
    status = db.Column(db.String(20), default='Available', nullable=False)  # Available, Leave, Unavailable

    schedules = db.relationship('Schedule', backref='worker', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'worker_code': self.worker_code,
            'skill': self.skill,
            'available_hours': self.available_hours,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'status': self.status
        }


class Material(db.Model):
    __tablename__ = 'materials'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    material_code = db.Column(db.String(50), unique=True, nullable=False)
    quantity = db.Column(db.Float, default=100.0, nullable=False)
    unit = db.Column(db.String(20), default='units', nullable=False)
    minimum_quantity = db.Column(db.Float, default=10.0, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'material_code': self.material_code,
            'quantity': self.quantity,
            'unit': self.unit,
            'minimum_quantity': self.minimum_quantity
        }


class Schedule(db.Model):
    __tablename__ = 'schedules'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    machine_id = db.Column(db.Integer, db.ForeignKey('machines.id'), nullable=False)
    worker_id = db.Column(db.Integer, db.ForeignKey('workers.id'), nullable=False)
    start_time = db.Column(db.String(20), nullable=False)
    end_time = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='Scheduled', nullable=False)  # Scheduled, Completed, Cancelled
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    constraints_logs = db.relationship('ConstraintLog', backref='schedule', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else 'Unknown',
            'product_code': self.product.code if self.product else '',
            'priority': self.product.priority if self.product else 'Normal',
            'quantity': self.product.quantity if self.product else 1,
            'machine_id': self.machine_id,
            'machine_name': self.machine.name if self.machine else 'Unknown',
            'machine_code': self.machine.machine_code if self.machine else '',
            'worker_id': self.worker_id,
            'worker_name': self.worker.name if self.worker else 'Unknown',
            'worker_code': self.worker.worker_code if self.worker else '',
            'start_time': self.start_time,
            'end_time': self.end_time,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class ConstraintLog(db.Model):
    __tablename__ = 'constraints_log'

    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=True)
    constraint_name = db.Column(db.String(100), nullable=False)
    result = db.Column(db.String(20), nullable=False)  # PASS, FAIL
    explanation = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'schedule_id': self.schedule_id,
            'constraint_name': self.constraint_name,
            'result': self.result,
            'explanation': self.explanation
        }


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='admin', nullable=False)  # admin, manager
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M:%S') if self.last_login else 'Never'
        }

