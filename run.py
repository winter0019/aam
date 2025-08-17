import os
from flask_migrate import MigrateCommand
from flask_script import Manager

from app import create_app, db

# The app factory is used to create the Flask app instance
app = create_app()

# Initialize Flask-Migrate and Flask-Script for managing migrations
manager = Manager(app)
manager.add_command('db', MigrateCommand)

if __name__ == "__main__":
    # In a production environment like Render, you can use the 'gunicorn' command.
    # We will use this check to run migrations automatically on startup.
    # This is useful for environments that don't have a manual way to run 'flask db upgrade'.
    if 'upgrade' in sys.argv:
        print("Running automatic database upgrade on startup.")
        try:
            from flask_migrate import upgrade
            with app.app_context():
                upgrade()
            print("Database upgrade completed successfully.")
        except Exception as e:
            print(f"Error during database upgrade: {e}")

    # For local development, we run the app using the Flask dev server.
    app.run(debug=True)
