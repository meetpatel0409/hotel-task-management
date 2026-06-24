from app import create_app
from models import db, User, Task, TaskProof
from init_db import seed_database

app = create_app()
with app.app_context():
    print("Clearing database tables...")
    db.session.query(TaskProof).delete()
    db.session.query(Task).delete()
    db.session.query(User).delete()
    db.session.commit()
    print("Database cleared.")

seed_database()
