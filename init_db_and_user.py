import sqlite3
import os
from app import create_app, bcrypt

def init_db(app):
    """
    Initializes the database and creates the necessary tables.
    """
    instance_path = app.instance_path
    os.makedirs(instance_path, exist_ok=True)
    db_path = os.path.join(instance_path, 'alfurqa_academy.db')
    
    # Ensure a fresh database is created by deleting the old one
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Old database deleted.")

    conn = sqlite3.connect(db_path)
    # Use row_factory to get dictionary-like rows
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'official'))
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_number TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            dob TEXT,
            gender TEXT,
            address TEXT,
            phone TEXT,
            email TEXT,
            class TEXT,
            term TEXT,
            academic_year TEXT,
            admission_date TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_reg_number TEXT NOT NULL,
            amount_paid REAL NOT NULL,
            payment_date TEXT NOT NULL,
            term TEXT NOT NULL,
            academic_year TEXT NOT NULL,
            recorded_by TEXT NOT NULL,
            FOREIGN KEY (student_reg_number) REFERENCES students(reg_number)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            term TEXT NOT NULL,
            academic_year TEXT NOT NULL,
            due_date TEXT,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def create_admin_user(app):
    """
    Creates a default admin user if one doesn't exist.
    """
    db_path = os.path.join(app.instance_path, 'alfurqa_academy.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    admin_exists = cursor.execute("SELECT 1 FROM users WHERE role = 'admin'").fetchone()

    if not admin_exists:
        username = 'admin'
        password = 'password'
        # Use flask_bcrypt's own hashing function for consistency
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       (username, hashed_password, 'admin'))
        conn.commit()
        print("Default admin user created: username='admin', password='password'")
    
    conn.close()

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        init_db(app)
        create_admin_user(app)
    print("Database initialized and 'admin' user created successfully!")
