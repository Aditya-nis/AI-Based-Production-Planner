from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.models import db, Material

materials_bp = Blueprint('materials', __name__)

@materials_bp.route('/materials', methods=['GET'])
def list_materials():
    materials = Material.query.order_by(Material.id.asc()).all()
    return render_template('materials.html', materials=materials)

@materials_bp.route('/materials/add', methods=['POST'])
def add_material():
    try:
        name = request.form.get('name', '').strip()
        code = request.form.get('material_code', '').strip().upper()
        quantity = float(request.form.get('quantity', 0.0))
        unit = request.form.get('unit', 'units').strip()
        min_qty = float(request.form.get('minimum_quantity', 0.0))

        if not name or not code:
            flash('Material Name and Code are required.', 'danger')
            return redirect(url_for('materials.list_materials'))

        if Material.query.filter_by(material_code=code).first():
            flash(f'Material Code {code} already exists.', 'warning')
            return redirect(url_for('materials.list_materials'))

        mat = Material(
            name=name,
            material_code=code,
            quantity=max(0.0, quantity),
            unit=unit,
            minimum_quantity=max(0.0, min_qty)
        )
        db.session.add(mat)
        db.session.commit()
        flash(f'Raw material "{name}" added successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding material: {str(e)}', 'danger')

    return redirect(url_for('materials.list_materials'))

@materials_bp.route('/materials/edit/<int:material_id>', methods=['POST'])
def edit_material(material_id):
    mat = db.get_or_404(Material, material_id)
    try:
        mat.name = request.form.get('name', mat.name).strip()
        mat.material_code = request.form.get('material_code', mat.material_code).strip().upper()
        mat.quantity = max(0.0, float(request.form.get('quantity', mat.quantity)))
        mat.unit = request.form.get('unit', mat.unit).strip()
        mat.minimum_quantity = max(0.0, float(request.form.get('minimum_quantity', mat.minimum_quantity)))
        db.session.commit()
        flash(f'Raw material "{mat.name}" updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating material: {str(e)}', 'danger')

    return redirect(url_for('materials.list_materials'))

@materials_bp.route('/materials/delete/<int:material_id>', methods=['POST', 'GET'])
def delete_material(material_id):
    mat = db.get_or_404(Material, material_id)
    try:
        db.session.delete(mat)
        db.session.commit()
        flash(f'Raw material "{mat.name}" deleted successfully.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting material: {str(e)}', 'danger')

    return redirect(url_for('materials.list_materials'))
