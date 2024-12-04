from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_
from datetime import datetime
from app.models import User, Equipment, MaintenanceRecord
from app import db

# Create blueprints
main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)

# Authentication routes
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.equipment_list'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.update_last_login()
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('main.equipment_list'))
        flash('Invalid username or password')
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.equipment_list'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return render_template('register.html')
        
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

# Main routes
@main.route('/')
@login_required
def equipment_list():
    search_query = request.args.get('search', '').strip()
    
    if search_query:
        # Search in both public and personal equipment
        public_equipment = Equipment.query.filter(
            Equipment.is_public == True,
            Equipment.name.ilike(f'%{search_query}%')
        ).all()
        
        personal_equipment = Equipment.query.filter(
            Equipment.user_id == current_user.id,
            Equipment.is_public == False,
            Equipment.name.ilike(f'%{search_query}%')
        ).all()
    else:
        # If no search query, return all equipment
        public_equipment = Equipment.query.filter_by(is_public=True).all()
        personal_equipment = Equipment.query.filter_by(
            user_id=current_user.id,
            is_public=False
        ).all()
    
    return render_template('equipment_list.html',
                         public_equipment=public_equipment,
                         personal_equipment=personal_equipment,
                         search_query=search_query)

@main.route('/equipment/add', methods=['GET', 'POST'])
@login_required
def add_equipment():
    if request.method == 'POST':
        try:
            equipment = Equipment(
                name=request.form.get('name'),
                description=request.form.get('description'),
                serial_number=request.form.get('serial_number'),
                purchase_date=datetime.strptime(request.form.get('purchase_date'), '%Y-%m-%d') if request.form.get('purchase_date') else None,
                purchase_price=float(request.form.get('purchase_price')) if request.form.get('purchase_price') else None,
                condition=request.form.get('condition', 'New'),
                is_public=bool(request.form.get('is_public')),
                category=request.form.get('category'),
                location=request.form.get('location'),
                user_id=current_user.id
            )
            db.session.add(equipment)
            db.session.commit()
            flash('Equipment added successfully!')
            return redirect(url_for('main.equipment_list'))
        except Exception as e:
            flash(f'Error adding equipment: {str(e)}')
            db.session.rollback()
    return render_template('equipment_form.html')

@main.route('/equipment/<int:id>')
@login_required
def view_equipment(id):
    equipment = Equipment.query.get_or_404(id)
    if not equipment.is_public and equipment.user_id != current_user.id:
        flash('You do not have permission to view this equipment.')
        return redirect(url_for('main.equipment_list'))
    return render_template('equipment_detail.html', equipment=equipment)

@main.route('/equipment/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_equipment(id):
    equipment = Equipment.query.get_or_404(id)
    if equipment.user_id != current_user.id:
        flash('You do not have permission to edit this equipment.')
        return redirect(url_for('main.equipment_list'))
    
    if request.method == 'POST':
        try:
            equipment.name = request.form.get('name')
            equipment.description = request.form.get('description')
            equipment.serial_number = request.form.get('serial_number')
            equipment.purchase_date = datetime.strptime(request.form.get('purchase_date'), '%Y-%m-%d') if request.form.get('purchase_date') else None
            equipment.purchase_price = float(request.form.get('purchase_price')) if request.form.get('purchase_price') else None
            equipment.condition = request.form.get('condition')
            equipment.is_public = bool(request.form.get('is_public'))
            equipment.category = request.form.get('category')
            equipment.location = request.form.get('location')
            
            db.session.commit()
            flash('Equipment updated successfully!')
            return redirect(url_for('main.view_equipment', id=equipment.id))
        except Exception as e:
            flash(f'Error updating equipment: {str(e)}')
            db.session.rollback()
    return render_template('equipment_form.html', equipment=equipment)

@main.route('/equipment/<int:id>/delete', methods=['POST'])
@login_required
def delete_equipment(id):
    equipment = Equipment.query.get_or_404(id)
    if equipment.user_id != current_user.id:
        flash('You do not have permission to delete this equipment.')
        return redirect(url_for('main.equipment_list'))
    
    try:
        db.session.delete(equipment)
        db.session.commit()
        flash('Equipment deleted successfully!')
    except Exception as e:
        flash(f'Error deleting equipment: {str(e)}')
        db.session.rollback()
    return redirect(url_for('main.equipment_list'))

@main.route('/search')
@login_required
def advanced_search():
    query = request.args.get('query', '').strip()
    category = request.args.get('category', '').strip()
    condition = request.args.get('condition', '').strip()
    
    base_query = Equipment.query
    
    if query:
        base_query = base_query.filter(Equipment.name.ilike(f'%{query}%'))
    if category:
        base_query = base_query.filter(Equipment.category == category)
    if condition:
        base_query = base_query.filter(Equipment.condition == condition)
    
    # Filter for public equipment or user's own equipment
    results = base_query.filter(
        or_(
            Equipment.is_public == True,
            Equipment.user_id == current_user.id
        )
    ).order_by(Equipment.name).all()
    
    return render_template('search_results.html',
                         results=results,
                         query=query,
                         category=category,
                         condition=condition)

@main.route('/equipment/<int:id>/maintenance', methods=['GET', 'POST'])
@login_required
def add_maintenance(id):
    equipment = Equipment.query.get_or_404(id)
    if equipment.user_id != current_user.id:
        flash('You do not have permission to add maintenance records for this equipment.')
        return redirect(url_for('main.equipment_list'))
    
    if request.method == 'POST':
        try:
            maintenance = MaintenanceRecord(
                equipment_id=equipment.id,
                maintenance_type=request.form.get('maintenance_type'),
                description=request.form.get('description'),
                cost=float(request.form.get('cost')) if request.form.get('cost') else None,
                performed_by=request.form.get('performed_by'),
                next_maintenance_date=datetime.strptime(request.form.get('next_maintenance_date'), '%Y-%m-%d') if request.form.get('next_maintenance_date') else None
            )
            db.session.add(maintenance)
            db.session.commit()
            flash('Maintenance record added successfully!')
            return redirect(url_for('main.view_equipment', id=equipment.id))
        except Exception as e:
            flash(f'Error adding maintenance record: {str(e)}')
            db.session.rollback()
    return render_template('maintenance_form.html', equipment=equipment)



@main.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500