# create_user.py
import sys
from getpass import getpass
from app import create_app, db
from app.models import User

# Create a Flask application instance and an application context.
# This is necessary to interact with the database.
app = create_app()

with app.app_context():
    # Prompt for the username and password for the new admin user.
    username = input("Enter a username for the new admin user: ")
    password = getpass("Enter a password for the new admin user: ")

    # Check if a user with the same username already exists.
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        print(f"Error: A user with the username '{username}' already exists.")
        sys.exit()

    # Create a new user instance.
    new_user = User(
        username=username,
        role='admin'
    )
    # This correctly uses the password setter to hash and store the password.
    new_user.password = password

    # Add the new user to the database and commit the changes.
    db.session.add(new_user)
    db.session.commit()

    print(f"Successfully created a new admin user: '{username}'")

