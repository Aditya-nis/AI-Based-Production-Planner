"""
Demo Data Seeder for AI Production Planning.
"""

from models.models import db, Product, Machine, Worker, Material, Schedule, ConstraintLog, User

def load_demo_data():
    """Populate database with clean, realistic production planning demo data."""
    # Clear existing data
    ConstraintLog.query.delete()
    Schedule.query.delete()
    Product.query.delete()
    Worker.query.delete()
    Machine.query.delete()
    Material.query.delete()
    db.session.commit()

    # 1. Raw Materials (4 items)
    mat1 = Material(name="Microcontroller ICs", material_code="MAT-IC01", quantity=50.0, unit="units", minimum_quantity=5.0)
    mat2 = Material(name="Teak Wood Planks", material_code="MAT-WD02", quantity=80.0, unit="pcs", minimum_quantity=10.0)
    mat3 = Material(name="Aluminum Alloy Sheets", material_code="MAT-AL03", quantity=100.0, unit="kg", minimum_quantity=15.0)
    mat4 = Material(name="Industrial Fasteners", material_code="MAT-FS04", quantity=500.0, unit="pcs", minimum_quantity=50.0)
    
    db.session.add_all([mat1, mat2, mat3, mat4])
    db.session.commit()

    # 2. Machines (3 machines)
    m1 = Machine(
        name="Precision Assembly Station",
        machine_code="MAC-ASM-01",
        machine_type="Assembly",
        capacity=1,
        available_hours=8.0,
        start_time="08:00",
        end_time="17:00",
        status="Available"
    )
    m2 = Machine(
        name="High-Speed CNC Cutter",
        machine_code="MAC-CUT-02",
        machine_type="Cutting",
        capacity=1,
        available_hours=8.0,
        start_time="08:00",
        end_time="17:00",
        status="Available"
    )
    m3 = Machine(
        name="Automated Drilling Unit",
        machine_code="MAC-DRL-03",
        machine_type="Drilling",
        capacity=1,
        available_hours=8.0,
        start_time="08:00",
        end_time="17:00",
        status="Available"
    )
    db.session.add_all([m1, m2, m3])
    db.session.commit()

    # 3. Workers (4 workers)
    w1 = Worker(
        name="Worker A (Alice Johnson)",
        worker_code="WRK-001",
        skill="Assembly",
        available_hours=8.0,
        start_time="08:00",
        end_time="17:00",
        status="Available"
    )
    w2 = Worker(
        name="Worker B (Bob Smith)",
        worker_code="WRK-002",
        skill="Cutting",
        available_hours=8.0,
        start_time="08:00",
        end_time="17:00",
        status="Available"
    )
    w3 = Worker(
        name="Worker C (Charlie Davis)",
        worker_code="WRK-003",
        skill="Drilling",
        available_hours=8.0,
        start_time="08:00",
        end_time="17:00",
        status="Available"
    )
    w4 = Worker(
        name="Worker D (Diana Prince)",
        worker_code="WRK-004",
        skill="Assembly",
        available_hours=8.0,
        start_time="08:00",
        end_time="17:00",
        status="Available"
    )
    db.session.add_all([w1, w2, w3, w4])
    db.session.commit()

    # 4. Products (4 products)
    p1 = Product(
        name="Laptop Assembly",
        code="PRD-LAPTOP",
        quantity=1,
        production_time=2.0,
        priority="High",
        deadline="13:00",
        machine_type="Assembly",
        material_id=mat1.id,
        material_quantity=2.0,
        status="Pending"
    )
    p2 = Product(
        name="Chair Manufacturing",
        code="PRD-CHAIR",
        quantity=1,
        production_time=2.0,
        priority="Medium",
        deadline="15:00",
        machine_type="Cutting",
        material_id=mat2.id,
        material_quantity=4.0,
        status="Pending"
    )
    p3 = Product(
        name="Table Manufacturing",
        code="PRD-TABLE",
        quantity=1,
        production_time=3.0,
        priority="Medium",
        deadline="17:00",
        machine_type="Drilling",
        material_id=mat2.id,
        material_quantity=6.0,
        status="Pending"
    )
    p4 = Product(
        name="Electronic Controller",
        code="PRD-CTRL",
        quantity=1,
        production_time=2.0,
        priority="Low",
        deadline="17:00",
        machine_type="Assembly",
        material_id=mat1.id,
        material_quantity=1.0,
        status="Pending"
    )
    db.session.add_all([p1, p2, p3, p4])
    db.session.commit()

    ensure_default_admin()

    return True


def ensure_default_admin():
    """Ensure at least one admin user exists with default credentials."""
    admin = User.query.filter_by(username='admin').first()
    if not admin and User.query.count() == 0:
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
    return admin

