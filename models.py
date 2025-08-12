from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer, nullable=False)
    unit = db.Column(db.String(20), nullable=False)  # pcs, sets, pairs, etc.
    condition = db.Column(db.String(20), nullable=False)  # New, Good, Worn, Needs Repair, Damaged
    assigned_to = db.Column(db.String(100))
    location = db.Column(db.String(100))
    date_issued = db.Column(db.Date)
    last_inspected = db.Column(db.Date)
    remarks = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Equipment {self.name}>'