import os
from datetime import datetime, timedelta
from app import create_app
from models import db, User, Task, TaskProof

def seed_database():
    app = create_app()
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Check if users already exist to avoid duplicate seeding
        if User.query.first():
            print("Database already contains data. Seeding skipped.")
            return

        print("Seeding database...")
        
        # 1. Create standard users
        users_data = [
            # Admins
            {"name": "System Admin", "email": "admin@luxeops.com", "password": "admin123", "role": "Admin", "department": "Administration"},
            # Managers
            {"name": "Sarah Connor", "email": "manager@luxeops.com", "password": "manager123", "role": "Manager", "department": "Operations"},
            # HODs
            {"name": "Elena Rostova", "email": "housekeeping_hod@luxeops.com", "password": "hod123", "role": "HOD", "department": "Housekeeping"},
            {"name": "Arthur Pendragon", "email": "maintenance_hod@luxeops.com", "password": "hod123", "role": "HOD", "department": "Maintenance"},
            {"name": "Chef Marco", "email": "kitchen_hod@luxeops.com", "password": "hod123", "role": "HOD", "department": "Kitchen"},
            # Employees
            {"name": "Rahul Kumar", "email": "rahul@luxeops.com", "password": "emp123", "role": "Employee", "department": "Housekeeping"},
            {"name": "Priya Sharma", "email": "priya@luxeops.com", "password": "emp123", "role": "Employee", "department": "Housekeeping"},
            {"name": "Vikram Singh", "email": "vikram@luxeops.com", "password": "emp123", "role": "Employee", "department": "Maintenance"},
            {"name": "Amit Patel", "email": "amit@luxeops.com", "password": "emp123", "role": "Employee", "department": "Kitchen"}
        ]
        
        seeded_users = {}
        for ud in users_data:
            user = User(
                name=ud["name"],
                email=ud["email"],
                role=ud["role"],
                department=ud["department"]
            )
            user.set_password(ud["password"])
            db.session.add(user)
            db.session.commit()
            seeded_users[ud["email"]] = user
            
        print(f"Seeded {len(users_data)} users.")

        # 2. Seed some standard tasks
        manager = seeded_users["manager@luxeops.com"]
        hk_hod = seeded_users["housekeeping_hod@luxeops.com"]
        maint_hod = seeded_users["maintenance_hod@luxeops.com"]
        
        rahul = seeded_users["rahul@luxeops.com"]
        priya = seeded_users["priya@luxeops.com"]
        vikram = seeded_users["vikram@luxeops.com"]
        
        now = datetime.utcnow()
        
        tasks_data = [
            {
                "title": "Clean Suite 402",
                "description": "Thorough deep clean of the presidential suite. Restock luxury bath amenities, replace bed linen, and polish mirrors.",
                "category": "Room Cleaning",
                "location": "Suite 402",
                "assigned_to_id": rahul.id,
                "assigned_by_id": hk_hod.id,
                "priority": "High",
                "status": "Pending",
                "deadline": now + timedelta(hours=2)
            },
            {
                "title": "Fix AC leak in Room 205",
                "description": "Guest reported a minor water leak from the ceiling AC unit. Inspect and fix internal pipe blockages.",
                "category": "Maintenance",
                "location": "Room 205",
                "assigned_to_id": vikram.id,
                "assigned_by_id": maint_hod.id,
                "priority": "High",
                "status": "In Progress",
                "deadline": now + timedelta(hours=4)
            },
            {
                "title": "Restock Linen Closet - 3rd Floor",
                "description": "Transport fresh towel sets and bed linens from laundry warehouse and organize them cleanly in the 3rd-floor closet.",
                "category": "Laundry",
                "location": "3rd Floor Linen Closet",
                "assigned_to_id": priya.id,
                "assigned_by_id": hk_hod.id,
                "priority": "Medium",
                "status": "Pending",
                "deadline": now + timedelta(hours=6)
            },
            {
                "title": "Replace corridor light bulbs (5th floor)",
                "description": "Replace 3 burnt-out LED ceiling spotlights in the central hallway of the fifth floor.",
                "category": "Maintenance",
                "location": "5th Floor Corridor",
                "assigned_to_id": vikram.id,
                "assigned_by_id": manager.id,
                "priority": "Low",
                "status": "Completed",
                "deadline": now - timedelta(hours=1) # Overdue/completed earlier
            }
        ]
        
        for td in tasks_data:
            task = Task(**td)
            db.session.add(task)
            
        db.session.commit()
        print("Seeded sample tasks.")
        print("Database initialization completed successfully.")

if __name__ == "__main__":
    # Ensure static/uploads folder exists
    os.makedirs(os.path.join('static', 'uploads'), exist_ok=True)
    seed_database()
