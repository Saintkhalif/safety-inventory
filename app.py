from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, make_response
from flask_sqlalchemy import SQLAlchemy
from models import db, User, Equipment
from config import Config
from datetime import datetime
import pandas as pd
from io import BytesIO

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Create tables and default user
with app.app_context():
    db.create_all()
    # Create default user if not exists
    if not User.query.filter_by(email='admin@example.com').first():
        default_user = User(email='admin@example.com', is_active=True)
        default_user.set_password('admin123')
        db.session.add(default_user)
        db.session.commit()

# Login required decorator
from functools import wraps  # ✅ add this import

def login_required(f):
    @wraps(f)  # ✅ this line is the fix
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
@login_required
def dashboard():
    total_items = Equipment.query.count()
    assigned_items = Equipment.query.filter(Equipment.assigned_to.isnot(None)).count()
    needs_repair = Equipment.query.filter_by(condition='Needs Repair').count()
    
    return render_template('dashboard.html', 
                         total_items=total_items,
                         assigned_items=assigned_items,
                         needs_repair=needs_repair)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/equipment')
@login_required
def equipment_list():
    condition_filter = request.args.get('condition')
    location_filter = request.args.get('location')
    assigned_filter = request.args.get('assigned_to')
    
    query = Equipment.query
    
    if condition_filter:
        query = query.filter_by(condition=condition_filter)
    if location_filter:
        query = query.filter(Equipment.location.contains(location_filter))
    if assigned_filter:
        query = query.filter(Equipment.assigned_to.contains(assigned_filter))
    
    equipment = query.order_by(Equipment.name).all()
    return render_template('equipment/list.html', equipment=equipment)

@app.route('/equipment/add', methods=['GET', 'POST'])
@login_required
def add_equipment():
    if request.method == 'POST':
        try:
            equipment = Equipment(
                name=request.form.get('name'),
                description=request.form.get('description'),
                quantity=int(request.form.get('quantity')),
                unit=request.form.get('unit'),
                condition=request.form.get('condition'),
                assigned_to=request.form.get('assigned_to'),
                location=request.form.get('location'),
                date_issued=datetime.strptime(request.form.get('date_issued'), '%Y-%m-%d') if request.form.get('date_issued') else None,
                last_inspected=datetime.strptime(request.form.get('last_inspected'), '%Y-%m-%d') if request.form.get('last_inspected') else None,
                remarks=request.form.get('remarks')
            )
            db.session.add(equipment)
            db.session.commit()
            flash('Equipment added successfully!', 'success')
            return redirect(url_for('equipment_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding equipment: {str(e)}', 'danger')
    return render_template('equipment/add.html')

@app.route('/equipment/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_equipment(id):
    equipment = Equipment.query.get_or_404(id)
    if request.method == 'POST':
        try:
            equipment.name = request.form.get('name')
            equipment.description = request.form.get('description')
            equipment.quantity = int(request.form.get('quantity'))
            equipment.unit = request.form.get('unit')
            equipment.condition = request.form.get('condition')
            equipment.assigned_to = request.form.get('assigned_to')
            equipment.location = request.form.get('location')
            equipment.date_issued = datetime.strptime(request.form.get('date_issued'), '%Y-%m-%d') if request.form.get('date_issued') else None
            equipment.last_inspected = datetime.strptime(request.form.get('last_inspected'), '%Y-%m-%d') if request.form.get('last_inspected') else None
            equipment.remarks = request.form.get('remarks')
            
            db.session.commit()
            flash('Equipment updated successfully!', 'success')
            return redirect(url_for('equipment_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating equipment: {str(e)}', 'danger')
    return render_template('equipment/edit.html', equipment=equipment)

@app.route('/equipment/delete/<int:id>', methods=['POST'])
@login_required
def delete_equipment(id):
    equipment = Equipment.query.get_or_404(id)
    try:
        db.session.delete(equipment)
        db.session.commit()
        flash('Equipment deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting equipment: {str(e)}', 'danger')
    return redirect(url_for('equipment_list'))

@app.route('/export')
@login_required
def export_to_excel():
    equipment = Equipment.query.all()
    
    # Create a DataFrame from the equipment data
    data = []
    for item in equipment:
        data.append({
            'Name': item.name,
            'Description': item.description,
            'Quantity': item.quantity,
            'Unit': item.unit,
            'Condition': item.condition,
            'Assigned To': item.assigned_to,
            'Location': item.location,
            'Date Issued': item.date_issued.strftime('%Y-%m-%d') if item.date_issued else '',
            'Last Inspected': item.last_inspected.strftime('%Y-%m-%d') if item.last_inspected else '',
            'Remarks': item.remarks
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Inventory', index=False)
    writer.close()
    output.seek(0)
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=inventory.xlsx'
    response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return response

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
