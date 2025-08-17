import sqlite3
import os
from werkzeug.security import generate_password_hash

# Define the database path relative to the script's location
DB_PATH = os.path.join('instance', 'alfurqa_academy.db')

def fix_admin_password():
    """
    Connects to the database and ensures the 'admin' user exists with a
    properly hashed password.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Generate a new hashed password for a default admin user
        # Password will be 'admin123'
        hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')

        # Check if the 'users' table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        table_exists = cursor.fetchone()

        if not table_exists:
            print("Error: The 'users' table does not exist. Please check your database schema.")
            conn.close()
            return

        # Check if the 'admin' user exists
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        admin_user = cursor.fetchone()

        if admin_user:
            # Update the password for the existing 'admin' user
            cursor.execute("UPDATE users SET password = ? WHERE username = 'admin'", (hashed_password,))
            print("Admin user password has been updated successfully.")
        else:
            # Create a new 'admin' user since one does not exist
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                           ('admin', hashed_password, 'admin'))
            print("Admin user created successfully.")

        conn.commit()
        conn.close()
        print("\nFix completed. You can now log in with username 'admin' and password 'admin123'.")

    except sqlite3.Error as e:
        print(f"A database error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    fix_admin_password()
