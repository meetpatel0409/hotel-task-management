from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # Admin, HOD, Manager, Employee
    department = db.Column(db.String(100), nullable=True)  # e.g., Housekeeping, Maintenance, Kitchen, Front Office, Laundry
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tasks_assigned = db.relationship('Task', backref='assignee', lazy=True, foreign_keys='Task.assigned_to_id')
    tasks_created = db.relationship('Task', backref='creator', lazy=True, foreign_keys='Task.assigned_by_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'department': self.department
        }

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)     # Room Cleaning, Maintenance, Restaurant Prep, Laundry, Guest Service, etc.
    location = db.Column(db.String(200), nullable=True)     # room number or location manually typed
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    priority = db.Column(db.String(50), default='Medium')  # Low, Medium, High
    status = db.Column(db.String(50), default='Pending')    # Pending, In Progress, Completed, Overdue, Approved, Rejected
    deadline = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    proofs = db.relationship('TaskProof', backref='task', lazy=True, cascade="all, delete-orphan")

    def is_overdue(self):
        return self.status not in ['Completed', 'Approved'] and self.deadline < datetime.utcnow()

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category or 'General',
            'location': self.location or 'N/A',
            'assigned_to': self.assignee.name if self.assignee else 'Unassigned',
            'assigned_to_id': self.assigned_to_id,
            'assigned_by': self.creator.name,
            'assigned_by_id': self.assigned_by_id,
            'priority': self.priority,
            'status': self.status,
            'deadline': self.deadline.strftime('%Y-%m-%d %H:%M:%S'),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_overdue': self.is_overdue()
        }

class TaskProof(db.Model):
    __tablename__ = 'task_proofs'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    before_image_path = db.Column(db.String(500), nullable=True)
    after_image_path = db.Column(db.String(500), nullable=True)
    progress_image_path = db.Column(db.String(500), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    approval_status = db.Column(db.String(50), default='Pending') # Pending, Approved, Rejected
    comments = db.Column(db.Text, nullable=True)                  # Rejection feedback
    employee_notes = db.Column(db.Text, nullable=True)            # Completion or handover notes
