# seed.py
from app import create_app, db
from app.models import User

# This script will automatically create a default admin user
# if one doesn't already exist in the database.

app = create_app()

def seed_database():
    """
    Creates a default admin user if the users table is empty.
    """
    with app.app_context():
        # Check if the users table has any users
        user_count = User.query.count()
        if user_count == 0:
            print("No users found. Creating a default admin user...")
            admin = User(username="admin", role="admin")
            admin.set_password("admin") # You can change this password
            db.session.add(admin)
            db.session.commit()
            print("Default admin user 'admin' created successfully!")
        else:
            print(f"Database contains {user_count} users. No new users created.")

if __name__ == "__main__":
    seed_database()

