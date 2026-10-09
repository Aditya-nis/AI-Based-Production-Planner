from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.models import db, Product, Material

products_bp = Blueprint('products', __name__)

@products_bp.route('/products', methods=['GET'])
def list_products():
    products = Product.query.order_by(Product.id.desc()).all()
    materials = Material.query.all()
    return render_template('products.html', products=products, materials=materials)

@products_bp.route('/products/add', methods=['POST'])
def add_product():
    try:
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip().upper()
        quantity = int(request.form.get('quantity', 1))
        production_time = float(request.form.get('production_time', 2.0))
        priority = request.form.get('priority', 'Medium')
        deadline = request.form.get('deadline', '17:00').strip()
        machine_type = request.form.get('machine_type', 'Assembly').strip()
        material_id = request.form.get('material_id')
        material_quantity = float(request.form.get('material_quantity', 1.0))

        if not name or not code:
            flash('Product Name and Code are required.', 'danger')
            return redirect(url_for('products.list_products'))

        if Product.query.filter_by(code=code).first():
            flash(f'Product Code {code} already exists.', 'warning')
            return redirect(url_for('products.list_products'))

        prod = Product(
            name=name,
            code=code,
            quantity=max(1, quantity),
            production_time=max(0.5, production_time),
            priority=priority,
            deadline=deadline,
            machine_type=machine_type,
            material_id=int(material_id) if material_id and material_id != '' else None,
            material_quantity=max(0.0, material_quantity),
            status='Pending'
        )
        db.session.add(prod)
        db.session.commit()
        flash(f'Product "{name}" added successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding product: {str(e)}', 'danger')

    return redirect(url_for('products.list_products'))

@products_bp.route('/products/edit/<int:product_id>', methods=['POST'])
def edit_product(product_id):
    prod = db.get_or_404(Product, product_id)
    try:
        prod.name = request.form.get('name', prod.name).strip()
        prod.code = request.form.get('code', prod.code).strip().upper()
        prod.quantity = max(1, int(request.form.get('quantity', prod.quantity)))
        prod.production_time = max(0.5, float(request.form.get('production_time', prod.production_time)))
        prod.priority = request.form.get('priority', prod.priority)
        prod.deadline = request.form.get('deadline', prod.deadline).strip()
        prod.machine_type = request.form.get('machine_type', prod.machine_type).strip()
        
        mat_id = request.form.get('material_id')
        prod.material_id = int(mat_id) if mat_id and mat_id != '' else None
        prod.material_quantity = max(0.0, float(request.form.get('material_quantity', prod.material_quantity)))
        
        db.session.commit()
        flash(f'Product "{prod.name}" updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating product: {str(e)}', 'danger')

    return redirect(url_for('products.list_products'))

@products_bp.route('/products/delete/<int:product_id>', methods=['POST', 'GET'])
def delete_product(product_id):
    prod = db.get_or_404(Product, product_id)
    try:
        db.session.delete(prod)
        db.session.commit()
        flash(f'Product "{prod.name}" deleted successfully.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}', 'danger')

    return redirect(url_for('products.list_products'))
