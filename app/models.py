from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    """User model for storing user related data"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship with Equipment model
    equipment = db.relationship('Equipment', backref='owner', lazy='dynamic',
                              cascade='all, delete-orphan')

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)

    def set_password(self, password):
        """Create hashed password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """Update the last login timestamp."""
        self.last_login = datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        return f'<User {self.username}>'

class Equipment(db.Model):
    """Equipment model for storing equipment related data"""
    __tablename__ = 'equipment'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    serial_number = db.Column(db.String(50), unique=True)
    purchase_date = db.Column(db.DateTime)
    purchase_price = db.Column(db.Float)
    condition = db.Column(db.String(20))  # New, Good, Fair, Poor
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, onupdate=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=False)
    is_available = db.Column(db.Boolean, default=True)
    category = db.Column(db.String(50))
    location = db.Column(db.String(100))
    
    # Foreign key to User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Equipment maintenance history relationship
    maintenance_history = db.relationship('MaintenanceRecord', backref='equipment',
                                        lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, name, user_id, description=None, serial_number=None,
                 purchase_date=None, purchase_price=None, condition='New',
                 is_public=False, category=None, location=None):
        self.name = name
        self.user_id = user_id
        self.description = description
        self.serial_number = serial_number
        self.purchase_date = purchase_date
        self.purchase_price = purchase_price
        self.condition = condition
        self.is_public = is_public
        self.category = category
        self.location = location

    def update_condition(self, new_condition):
        """Update equipment condition and create maintenance record."""
        old_condition = self.condition
        self.condition = new_condition
        maintenance_record = MaintenanceRecord(
            equipment_id=self.id,
            maintenance_type='Condition Update',
            description=f'Condition updated from {old_condition} to {new_condition}'
        )
        db.session.add(maintenance_record)
        db.session.commit()

    def __repr__(self):
        return f'<Equipment {self.name}>'

class MaintenanceRecord(db.Model):
    """Model for storing equipment maintenance history"""
    __tablename__ = 'maintenance_records'

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    maintenance_date = db.Column(db.DateTime, default=datetime.utcnow)
    maintenance_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    cost = db.Column(db.Float)
    performed_by = db.Column(db.String(100))
    next_maintenance_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='Completed')  # Scheduled, In Progress, Completed

    def __init__(self, equipment_id, maintenance_type, description=None,
                 cost=None, performed_by=None, next_maintenance_date=None):
        self.equipment_id = equipment_id
        self.maintenance_type = maintenance_type
        self.description = description
        self.cost = cost
        self.performed_by = performed_by
        self.next_maintenance_date = next_maintenance_date

    def __repr__(self):
        return f'<MaintenanceRecord {self.maintenance_type} for Equipment {self.equipment_id}>'