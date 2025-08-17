import io
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, User, Student, Payment, get_current_school_period, FEE_STRUCTURE

# For PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# Define a Blueprint for the main application routes
main = Blueprint('main', __name__)

def get_fee_status(student_reg_number, academic_year_check, term_check):
    """(Removed for now, will be re-added with the 'students' routes)"""
    return 'N/A'

@main.route('/create_first_admin')
def create_first_admin():
    try:
        existing_user = User.query.filter_by(username='admin').first()
        if existing_user:
            flash('Admin user already exists. You can log in.', 'info')
            return redirect(url_for('main.login'))

        hashed_password = generate_password_hash('admin')
        first_admin = User(username='admin', password=hashed_password, role='admin')
        db.session.add(first_admin)
        db.session.commit()
        
        flash('First admin user created successfully. You can now log in.', 'success')
        return redirect(url_for('main.login'))
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('main.login'))

@main.route('/')
def home():
    return redirect(url_for('main.dashboard'))

@main.route('/dashboard')
@login_required
def dashboard():
    # Fetch a simple count for the dashboard
    total_students = Student.query.count()
    total_fees_paid = db.session.query(db.func.sum(Payment.amount_paid)).scalar() or 0.0
    total_officers = User.query.filter_by(role='officer').count()
    
    # We will pass an empty list for students for now to keep it minimal
    students_with_status = []

    return render_template(
        'dashboard.html',
        students=students_with_status,
        total_students=total_students,
        total_fees_paid=total_fees_paid,
        total_officers=total_officers
    )

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))
    
# --- The following routes have been commented out to provide a clean start ---
# @main.route('/register', methods=['GET', 'POST'])
# def register():
#    ...
# @main.route('/register_officer', methods=['GET', 'POST'])
# @login_required
# def register_officer():
#    ...
# @main.route('/register_student', methods=('GET', 'POST'))
# @login_required
# def register_student():
#    ...
# @main.route('/students', defaults={'student_class': None})
# @main.route('/students/<student_class>')
# @login_required
# def students(student_class):
#    ...
# @main.route('/student/<reg_number>')
# @login_required
# def student_details(reg_number):
#    ...
# @main.route('/make_payment/<reg_number>', methods=['GET', 'POST'])
# @login_required
# def make_payment(reg_number):
#    ...
# @main.route('/edit_student/<reg_number>', methods=['GET', 'POST'])
# @login_required
# def edit_student(reg_number):
#    ...
# @main.route('/search_students', methods=['GET'])
# @login_required
# def search_students():
#    ...
# @main.route('/download_receipt/<int:payment_id>')
# @login_required
# def download_receipt(payment_id):
#    ...
# @main.route('/fees')
# @login_required
# def fees():
#    ...
# @main.route('/payments')
# @login_required
# def payments():
#    ...
