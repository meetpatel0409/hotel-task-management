import unittest
import os

# Set database URL to in-memory SQLite for testing before importing the app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from datetime import datetime, timedelta
from app import create_app
from models import db, User, Task, TaskProof

class LuxeOpsTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Seed test data
            self.seed_test_data()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def seed_test_data(self):
        # Seed an admin, manager, HOD, and employee
        self.admin = User(name="Test Admin", email="admin@test.com", role="Admin", department="Admin")
        self.admin.set_password("admin123")
        
        self.manager = User(name="Test Manager", email="manager@test.com", role="Manager", department="Operations")
        self.manager.set_password("manager123")
        
        self.hod = User(name="Test HOD", email="hod@test.com", role="HOD", department="Housekeeping")
        self.hod.set_password("hod123")
        
        self.employee1 = User(name="Rahul", email="rahul@test.com", role="Employee", department="Housekeeping")
        self.employee1.set_password("emp123")

        self.employee2 = User(name="Vikram", email="vikram@test.com", role="Employee", department="Maintenance")
        self.employee2.set_password("emp123")
        
        db.session.add_all([self.admin, self.manager, self.hod, self.employee1, self.employee2])
        db.session.commit()
        
        # Save raw IDs to avoid DetachedInstanceError
        self.admin_id = self.admin.id
        self.manager_id = self.manager.id
        self.hod_id = self.hod.id
        self.employee1_id = self.employee1.id
        self.employee2_id = self.employee2.id

        # Seed an initial task
        self.task = Task(
            title="Clean Room 302",
            description="Deep clean suite 302",
            assigned_to_id=self.employee1_id,
            assigned_by_id=self.hod_id,
            priority="High",
            status="Pending",
            deadline=datetime.utcnow() + timedelta(hours=2)
        )
        db.session.add(self.task)
        db.session.commit()
        self.task_id = self.task.id

    def login(self, email, password, role=None):
        return self.client.post('/login', data=dict(
            email=email,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_login_logout(self):
        # Test successful login
        response = self.login("rahul@test.com", "emp123")
        self.assertIn(b"Welcome back, Rahul!", response.data)
        
        # Test failed login with invalid password
        self.logout()
        response = self.login("rahul@test.com", "wrongpassword")
        self.assertIn(b"Invalid email or password.", response.data)

    def test_routing_protection(self):
        # Try to access admin dashboard when not logged in
        response = self.client.get('/admin', follow_redirects=True)
        self.assertIn(b"Sign In - LuxeOps Portal", response.data)
        
        # Log in as Employee and try to access Admin and HOD dashboards
        self.login("rahul@test.com", "emp123")
        response = self.client.get('/admin', follow_redirects=True)
        self.assertIn(b"Access denied.", response.data)
        
        response = self.client.get('/hod', follow_redirects=True)
        self.assertIn(b"Access denied.", response.data)

    def test_task_creation_by_hod(self):
        self.login("hod@test.com", "hod123")
        
        deadline_str = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        response = self.client.post('/task/create', data=dict(
            title="Clean Lobby",
            description="Deep clean lobby floor",
            assigned_to=self.employee1_id,  # Same dept (Housekeeping)
            priority="Medium",
            deadline=deadline_str
        ), follow_redirects=True)
        
        self.assertIn(b"Task successfully created and assigned.", response.data)
        
        # HOD trying to assign to employee of another dept (Maintenance)
        response = self.client.post('/task/create', data=dict(
            title="Clean Pool",
            description="Lobby clean",
            assigned_to=self.employee2_id,  # Maintenance
            priority="Medium",
            deadline=deadline_str
        ), follow_redirects=True)
        self.assertIn(b"You can only assign tasks to employees within your department.", response.data)

    def test_task_creation_past_deadline(self):
        self.login("hod@test.com", "hod123")
        
        # Deadline in the past
        deadline_str = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        response = self.client.post('/task/create', data=dict(
            title="Past Task",
            description="Should fail",
            assigned_to=self.employee1_id,
            priority="Medium",
            deadline=deadline_str
        ), follow_redirects=True)
        
        self.assertIn(b"Deadline cannot be in the past.", response.data)

    def test_task_quick_complete(self):
        # Create a Low priority task
        self.login("hod@test.com", "hod123")
        deadline_str = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        self.client.post('/task/create', data=dict(
            title="Low Priority Clean",
            description="Dusting",
            assigned_to=self.employee1_id,
            priority="Low",
            deadline=deadline_str
        ))
        
        with self.app.app_context():
            low_task = Task.query.filter_by(priority="Low").first()
            self.assertIsNotNone(low_task)
            low_task_id = low_task.id
            
        # Log in as Employee and quick complete
        self.login("rahul@test.com", "emp123")
        response = self.client.post(f'/task/quick_complete/{low_task_id}', follow_redirects=True)
        self.assertIn(b"Task quick completed! Awaiting manager verification.", response.data)
        
        with self.app.app_context():
            completed_task = Task.query.get(low_task_id)
            self.assertEqual(completed_task.status, 'Completed')
            proof = TaskProof.query.filter_by(task_id=low_task_id).first()
            self.assertIsNotNone(proof)
            self.assertIsNotNone(proof.uploaded_at)

    def test_reports_api_metrics(self):
        # Create low priority task, quick complete it, and check reports api JSON response
        self.login("hod@test.com", "hod123")
        deadline_str = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        self.client.post('/task/create', data=dict(
            title="SLA Test Task",
            description="Testing SLA and resolution metrics",
            assigned_to=self.employee1_id,
            priority="Low",
            deadline=deadline_str
        ))
        
        with self.app.app_context():
            t = Task.query.filter_by(title="SLA Test Task").first()
            t_id = t.id
            
        # Quick complete
        self.login("rahul@test.com", "emp123")
        self.client.post(f'/task/quick_complete/{t_id}')
        
        # Access reports data as Admin
        self.login("admin@test.com", "admin123")
        response = self.client.get('/api/reports-data')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('sla_overview', data)
        self.assertIn('dept_avg_resolution', data)
        self.assertIn('Met', data['sla_overview'])
        self.assertIn('Breached', data['sla_overview'])

    def test_task_lifecycle_employee_workflow(self):
        # 1. Login as Employee
        self.login("rahul@test.com", "emp123")
        
        # 2. Check task exists in Employee checklist
        response = self.client.get('/employee')
        self.assertIn(b"Clean Room 302", response.data)
        self.assertIn(b"Not Started", response.data)
        
        # 3. Start Task
        response = self.client.post(f'/task/start/{self.task_id}', follow_redirects=True)
        self.assertIn(b"Task status updated to In Progress. Time to excel!", response.data)
        
        # Check status changed
        with self.app.app_context():
            task = Task.query.get(self.task_id)
            self.assertEqual(task.status, 'In Progress')

    def test_admin_onboarding_flow(self):
        self.login("admin@test.com", "admin123", "Admin")
        
        # Add new user
        response = self.client.post('/admin/user/create', data=dict(
            name="New Maid",
            email="maid@test.com",
            password="maidpassword",
            role="Employee",
            department="Housekeeping"
        ), follow_redirects=True)
        
        self.assertIn(b"User New Maid successfully created.", response.data)
        
        # Verify user created in DB
        with self.app.app_context():
            new_user = User.query.filter_by(email="maid@test.com").first()
            self.assertIsNotNone(new_user)
            self.assertEqual(new_user.name, "New Maid")
            self.assertEqual(new_user.role, "Employee")

if __name__ == '__main__':
    unittest.main()
