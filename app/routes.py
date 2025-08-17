# Import necessary modules from Flask and Flask-Login
import io
import os
from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    send_file,
    current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc

# For PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.lib.enums import TA_CENTER

# Import models, constants, and helper functions from the 'app' package.
from . import db, get_current_school_period
from .models import User, Student, Payment, Teacher, Fee, Class

# ✅ FIX: Define the blueprint at the very top so it can be used below.
main = Blueprint('main', __name__)

# A new filter to format currency values for display in templates.
@main.app_template_filter('format_currency')
def format_currency_filter(value):
    """
    Formats a number as Nigerian Naira (₦) with commas for thousands.
    """
    if isinstance(value, (int, float)):
        return f"₦{value:,.2f}"
    return value

def generate_reg_number():
    """
    Generates a unique registration number based on the school's short name,
    the current academic year, and a sequential number.
    Format: SCHOOL_SHORT_NAME/YY/NNNN
    Example: AAM/25/0001
    
    This is a robust approach as it queries the database to find the last
    used registration number, preventing duplicates.
    """
    try:
        current_year = datetime.now().strftime('%y')
        
        # Find the last student registered for the current year.
        # We order by descending registration number to get the highest one.
        last_student = Student.query.filter(
            Student.reg_number.like(f'{SCHOOL_SHORT_NAME}/{current_year}/%')
        ).order_by(desc(Student.reg_number)).first()

        if last_student:
            # Extract the numeric part of the last registration number
            last_number_str = last_student.reg_number.split('/')[-1]
            last_number = int(last_number_str)
            next_number = last_number + 1
        else:
            # If no student exists for the year, start from 1
            next_number = 1
        
        # Format the sequential number with leading zeros (e.g., 1 -> 0001)
        formatted_number = f'{next_number:04d}'
        
        # Combine the parts to create the new registration number
        return f'{SCHOOL_SHORT_NAME}/{current_year}/{formatted_number}'

    except Exception as e:
        print(f"Error generating registration number: {e}")
        # Return None or raise an error to prevent further execution
        return None

def get_fee_status(student_reg_number, academic_year_check, term_check):
    """
    Calculates the fee status ('Paid', 'Defaulter', or 'N/A') for a student
    for a given academic year and term.
    
    This is a great helper function that keeps the logic for determining
    status separate from the main routes.
    """
    student = Student.query.get(student_reg_number)
    
    if not student:
        return 'N/A'
    
    # Use the new Fee model to get the expected amount
    expected_fee = Fee.query.filter_by(
        student_class=student.student_class,
        term=term_check,
        academic_year=academic_year_check
    ).first()
    expected_amount = expected_fee.amount if expected_fee else 0.0

    # Use db.func.sum() for an efficient database-side aggregation.
    total_paid = db.session.query(db.func.sum(Payment.amount_paid)).filter(
        Payment.student_reg_number == student_reg_number,
        Payment.term == term_check,
        Payment.academic_year == academic_year_check
    ).scalar() or 0.0
    
    if expected_amount > 0:
        if total_paid >= expected_amount:
            return 'Paid'
        else:
            return 'Defaulter'
    else:
        return 'Paid'

@main.route('/create_first_admin')
def create_first_admin():
    """Route to create the initial admin user if one doesn't exist."""
    try:
        existing_user = User.query.filter_by(username='admin').first()
        if existing_user:
            flash('Admin user already exists. You can log in.', 'info')
            return redirect(url_for('main.login'))

        # It's good practice to use a robust password hash.
        hashed_password = generate_password_hash('admin')
        first_admin = User(username='admin', password_hash=hashed_password, role='admin')
        db.session.add(first_admin)
        db.session.commit()
        
        # Create initial classes if the table is empty
        if Class.query.count() == 0:
            initial_classes = ['JSS 1', 'JSS 2', 'JSS 3', 'SS 1', 'SS 2', 'SS 3']
            for class_name in initial_classes:
                new_class = Class(name=class_name)
                db.session.add(new_class)
            db.session.commit()
        
        flash('First admin user created successfully! And initial classes have been added. You can now log in.', 'success')
        return redirect(url_for('main.login'))
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('main.login'))

@main.route('/')
def home():
    """Redirects the root URL to the dashboard."""
    return redirect(url_for('main.dashboard'))

@main.route('/dashboard')
@login_required # Protect this route so only logged-in users can access it.
def dashboard():
    """Renders the main dashboard page with key metrics."""
    # Check the user's role and render the appropriate dashboard.
    if current_user.role == 'officer':
        return render_template('official_dashboard.html')
    
    # This is the admin dashboard logic.
    total_students = db.session.query(Student).count()
    total_fees_paid = db.session.query(db.func.sum(Payment.amount_paid)).scalar() or 0
    total_teachers = db.session.query(Teacher).count()
    total_officers = db.session.query(User).filter_by(role='officer').count()

    # Query for the most recent 5 students.
    students = Student.query.order_by(Student.admission_date.desc()).limit(5).all()
    
    current_academic_year, current_term = get_current_school_period()
    students_with_status = []
    for student in students:
        student.fee_status = get_fee_status(student.reg_number, current_academic_year, current_term)
        students_with_status.append(student)

    return render_template(
        'dashboard.html',
        students=students_with_status,
        total_students=total_students,
        total_fees_paid=total_fees_paid,
        total_teachers=total_teachers,
        total_officers=total_officers
    )

@main.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    """Handles user registration (for general users)."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'error')
        else:
            new_user = User(username=username, role='user')
            new_user.password = password
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('main.login'))
    return render_template('register.html')
    
@main.route('/register_officer', methods=['GET', 'POST'])
@login_required
def register_officer():
    """Allows an admin to register a new officer."""
    if current_user.role != 'admin':
        abort(403)
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'error')
        else:
            new_officer = User(username=username, role='officer')
            new_officer.password = password
            db.session.add(new_officer)
            db.session.commit()
            flash(f'Officer {username} created successfully!', 'success')
            return redirect(url_for('main.dashboard'))
            
    return render_template('register_officer.html')
    
# --- START of NEW CODE ---
# New route for Teacher Reports
@main.route('/teacher_reports')
@login_required
def teacher_reports():
    """Placeholder for the Teacher Reports page."""
    # This route is a placeholder. You will add logic here to generate and display reports on teachers.
    return render_template('teacher_reports.html', title="Teacher Reports")

# New route for Financial Reports
@main.route('/financial_reports')
@login_required
def financial_reports():
    """Placeholder for the Financial Reports page."""
    # This route is a placeholder. You will add logic here to generate and display financial reports.
    return render_template('financial_reports.html', title="Financial Reports")
    
# New route for Settings
@main.route('/settings')
@login_required
def settings():
    """Placeholder for the Settings page."""
    # This route is a placeholder. You will add logic here for user and system settings.
    return render_template('settings.html', title="Settings")

# New route for Fees
@main.route('/fees', methods=['GET'])
@login_required
def fees():
    """
    Manages the display of school fees.
    This route fetches all fee records from the database and passes them
    to the 'fees.html' template.
    """
    if current_user.role != 'admin':
        abort(403)

    all_fees = Fee.query.all()
    return render_template('fees.html', title='Manage Fees', fees=all_fees)

# --- END of NEW CODE ---

@main.route('/reports')
@login_required
def reports():
    """Route for the main Reports page, allowing users to select report parameters."""
    if current_user.role != 'admin':
        abort(403)
    
    current_academic_year, current_term = get_current_school_period()
    all_classes = sorted(c.name for c in Class.query.all())
    
    return render_template(
        'reports.html',
        current_academic_year=current_academic_year,
        current_term=current_term,
        classes=all_classes
    )
    
@main.route('/download_report/<report_type>')
@login_required
def download_report(report_type):
    """
    Generates and downloads a PDF report for paid or unpaid students
    based on the selected criteria.
    """
    if current_user.role != 'admin':
        abort(403)

    academic_year = request.args.get('academic_year')
    term = request.args.get('term')
    student_class = request.args.get('student_class')

    if not all([academic_year, term, student_class]):
        flash('Please select academic year, term, and class for the report.', 'error')
        return redirect(url_for('main.reports'))

    all_students_in_class = Student.query.filter_by(student_class=student_class).all()

    report_title = ""
    students_for_report = []

    if report_type == 'paid':
        report_title = f"Paid Students Report for {student_class} ({term} {academic_year})"
        students_for_report = [
            s for s in all_students_in_class
            if get_fee_status(s.reg_number, academic_year, term) == 'Paid'
        ]
    elif report_type == 'unpaid':
        report_title = f"Unpaid Students Report for {student_class} ({term} {academic_year})"
        students_for_report = [
            s for s in all_students_in_class
            if get_fee_status(s.reg_number, academic_year, term) == 'Defaulter'
        ]
    else:
        flash('Invalid report type.', 'error')
        return redirect(url_for('main.reports'))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"<b>{report_title}</b>", styles['h1']))
    story.append(Spacer(1, 0.2 * inch))

    if not students_for_report:
        story.append(Paragraph("No students found for this report.", styles['Normal']))
    else:
        for student in students_for_report:
            story.append(Paragraph(f"<b>Name:</b> {student.name}", styles['Normal']))
            story.append(Paragraph(f"<b>Reg Number:</b> {student.reg_number}", styles['Normal']))
            story.append(Paragraph(f"<b>Class:</b> {student.student_class}", styles['Normal']))
            story.append(Spacer(1, 0.1 * inch))

    doc.build(story)
    buffer.seek(0)
    
    filename = f"{report_type}_report_{student_class}_{academic_year}_{term}.pdf"
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

@main.route('/logout')
@login_required
def logout():
    """Logs out the current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))
    
@main.route('/register_student', methods=('GET', 'POST'))
@login_required
def register_student():
    """Handles student registration."""
    if current_user.role not in ['admin', 'officer']:
        abort(403)
    
    if request.method == 'POST':
        # Safely get form data to prevent KeyError
        name = request.form.get('full_name', '').strip()
        dob = request.form.get('dob', '').strip()
        gender = request.form.get('gender', '').strip()
        address = request.form.get('address', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        student_class = request.form.get('class', '').strip()
        term = request.form.get('term', '').strip()
        academic_year = request.form.get('academic_year', '').strip()
        
        # Check if all required fields are filled. This is good validation.
        if not all([name, dob, gender, address, phone, email, student_class, term, academic_year]):
            flash('All fields marked with * are required. Please fill in the form completely.', 'error')
            return redirect(url_for('main.register_student'))
        
        try:
            # Auto-generate the registration number
            reg_number = generate_reg_number()
            if not reg_number:
                flash('An error occurred while generating a registration number.', 'error')
                return redirect(url_for('main.register_student'))

            new_student = Student(
                reg_number=reg_number,
                name=name,
                dob=dob,
                gender=gender,
                address=address,
                phone=phone,
                email=email,
                student_class=student_class,
                term=term,
                academic_year=academic_year,
                admission_date=datetime.now().strftime('%Y-%m-%d')
            )
            db.session.add(new_student)
            db.session.commit()
            flash(f'Student {name} registered successfully with Reg. Number: {reg_number}', 'success')
            return redirect(url_for('main.student_details', reg_number=reg_number))
        except IntegrityError:
            db.session.rollback()
            flash(f'Database error: A student with registration number {reg_number} already exists.', 'error')
            return redirect(url_for('main.register_student'))
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {e}', 'error')
            return redirect(url_for('main.register_student'))

    classes = sorted(c.name for c in Class.query.all())
    terms = ['First Term', 'Second Term', 'Third Term']
    current_year_val = datetime.now().year
    academic_years = [f"{y}/{y+1}" for y in range(current_year_val - 2, current_year_val + 3)]

    return render_template('register_student.html', classes=classes, terms=terms, academic_years=academic_years)
    
@main.route('/students', defaults={'student_class': None})
@main.route('/students/<student_class>')
@login_required
def students(student_class):
    """
    Displays a list of students, with optional filtering by class, status, and search query.
    """
    status_filter = request.args.get('status', 'all')
    class_filter = student_class or request.args.get('class', 'all')
    term_filter = request.args.get('term', 'all')
    search_query = request.args.get('search_query', '').strip()

    students_data = Student.query
    if class_filter != 'all':
        students_data = students_data.filter_by(student_class=class_filter)
    if term_filter != 'all':
        students_data = students_data.filter_by(term=term_filter)
    if search_query:
        students_data = students_data.filter(
            (Student.name.like(f'%{search_query}%')) | 
            (Student.reg_number.like(f'%{search_query}%'))
        )
    students_data = students_data.all()
    
    current_academic_year, current_term_for_status = get_current_school_period()
    students_with_status = []
    for student in students_data:
        student.fee_status = get_fee_status(student.reg_number, current_academic_year, current_term_for_status)
        students_with_status.append(student)

    if status_filter != 'all':
        students_with_status = [s for s in students_with_status if s.fee_status == status_filter]

    all_classes = sorted(c.name for c in Class.query.all())
    all_terms = ['First Term', 'Second Term', 'Third Term']

    return render_template(
        'students.html',
        students=students_with_status,
        status_filter=status_filter,
        class_filter=class_filter,
        term_filter=term_filter,
        search_query=search_query,
        classes=all_classes,
        terms=all_terms
    )

@main.route('/student/<path:reg_number>')
@login_required
def student_details(reg_number):
    """Displays detailed information for a specific student."""
    student = Student.query.get_or_404(reg_number)
    payments = Payment.query.filter_by(student_reg_number=reg_number).all()
    
    current_academic_year, current_term = get_current_school_period()
    student_fee_status = get_fee_status(reg_number, current_academic_year, current_term)
    
    fee_breakdown = {}
    all_years_terms = set()
    
    if student.academic_year and student.term:
        all_years_terms.add((student.academic_year, student.term))
    for p in payments:
        all_years_terms.add((p.academic_year, p.term))
    all_years_terms.add((current_academic_year, current_term))
    
    for year, term in sorted(list(all_years_terms)):
        expected_fee_obj = Fee.query.filter_by(
            student_class=student.student_class,
            term=term,
            academic_year=year
        ).first()
        expected_amount = expected_fee_obj.amount if expected_fee_obj else 0.0

        total_paid_for_period = db.session.query(db.func.sum(Payment.amount_paid)).filter(
            Payment.student_reg_number == reg_number,
            Payment.term == term,
            Payment.academic_year == year
        ).scalar() or 0.0
        
        outstanding_amount = expected_amount - total_paid_for_period

        fee_breakdown[f"{term} {year}"] = {
            'expected': expected_amount,
            'paid': total_paid_for_period,
            'outstanding': outstanding_amount
        }
    
    def sort_key_for_fee_breakdown(item):
        period_str = item[0]
        parts = period_str.split(' ')
        term_name = ' '.join(parts[:-1]) if len(parts) > 1 else parts[0]
        year_part = parts[-1] if len(parts) > 1 else ""
        
        try:
            start_year = int(year_part.split('/')[0])
        except (ValueError, IndexError):
            start_year = 0
        
        term_order = ['First Term', 'Second Term', 'Third Term']
        try:
            term_index = term_order.index(term_name)
        except ValueError:
            term_index = -1
        
        return (start_year, term_index)

    sorted_fee_breakdown = sorted(fee_breakdown.items(), key=sort_key_for_fee_breakdown, reverse=True)
    sorted_fee_breakdown_dict = {k: v for k, v in sorted_fee_breakdown}

    return render_template('student_details.html',
                           student=student,
                           payments=payments,
                           fee_status=student_fee_status,
                           fee_breakdown=sorted_fee_breakdown_dict,
                           current_academic_year=current_academic_year,
                           current_term=current_term
                           )

@main.route('/make_payment/<path:reg_number>', methods=['GET', 'POST'])
@login_required
def make_payment(reg_number):
    """Handles recording a new payment for a student."""
    if current_user.role not in ['admin', 'officer']:
        abort(403)
    
    student = Student.query.get_or_404(reg_number)

    if request.method == 'POST':
        amount_str = request.form['amount_paid'].strip()
        term = request.form['term'].strip()
        academic_year = request.form['academic_year'].strip()
        recorded_by_user = current_user.id
        
        try:
            amount_paid = float(amount_str)
            if amount_paid <= 0:
                flash('Payment amount must be positive.', 'error')
            else:
                payment_date = datetime.now().strftime('%Y-%m-%d')
                new_payment = Payment(
                    student_reg_number=reg_number,
                    term=term,
                    academic_year=academic_year,
                    amount_paid=amount_paid,
                    payment_date=payment_date,
                    recorded_by=recorded_by_user
                )
                db.session.add(new_payment)
                db.session.commit()
                flash(f'Payment of ₦{amount_paid:,.2f} recorded for {student.name} for {term} {academic_year}.', 'success')
                return redirect(url_for('main.student_details', reg_number=reg_number))
        except ValueError:
            flash('Invalid amount. Please enter a valid number.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Database error: {e}', 'error')

    terms = ['First Term', 'Second Term', 'Third Term']
    current_year_val = datetime.now().year
    academic_years = [f"{y}/{y+1}" for y in range(current_year_val - 2, current_year_val + 3)]
    
    pre_selected_academic_year, pre_selected_term = get_current_school_period()

    return render_template('make_payment.html',
                           student=student,
                           terms=terms,
                           academic_years=academic_years,
                           pre_selected_term=pre_selected_term,
                           pre_selected_academic_year=pre_selected_academic_year)

@main.route('/edit_student/<path:reg_number>', methods=['GET', 'POST'])
@login_required
def edit_student(reg_number):
    """Handles editing an existing student's details."""
    student = Student.query.get_or_404(reg_number)
    
    if current_user.role != 'admin':
        abort(403)
    
    if request.method == 'POST':
        try:
            student.name = request.form['name'].strip()
            student.dob = request.form['dob'].strip()
            student.gender = request.form['gender'].strip()
            student.address = request.form['address'].strip()
            student.phone = request.form['phone'].strip()
            student.email = request.form['email'].strip()
            student.student_class = request.form['class'].strip()
            student.term = request.form['term'].strip()
            student.academic_year = request.form['academic_year'].strip()
            db.session.commit()
            flash(f'Student {student.name} updated successfully!', 'success')
            return redirect(url_for('main.student_details', reg_number=reg_number))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating student: {e}', 'error')

    classes = sorted(c.name for c in Class.query.all())
    terms = ['First Term', 'Second Term', 'Third Term']
    current_year_val = datetime.now().year
    academic_years = [f"{y}/{y+1}" for y in range(current_year_val - 2, current_year_val + 3)]

    return render_template('edit_student.html', student=student, classes=classes, terms=terms, academic_years=academic_years)

@main.route('/search_students', methods=['GET'])
@login_required
def search_students():
    """
    Handles student search requests by name or registration number.
    Renders a page with the search results.
    """
    search_query = request.args.get('query', '').strip()

    if search_query:
        # Good use of filtering with 'like' for flexible searching.
        results = Student.query.filter(
            (Student.name.like(f'%{search_query}%')) |
            (Student.reg_number.like(f'%{search_query}%'))
        ).order_by(Student.name).all()
    else:
        results = []

    return render_template('search_results.html', query=search_query, students=results)

@main.route('/download_receipt/<int:payment_id>')
@login_required
def download_receipt(payment_id):
    """
    Generates a PDF payment receipt for a given payment ID and sends it as a download.
    """
    payment = Payment.query.get_or_404(payment_id)
    student = Student.query.filter_by(reg_number=payment.student_reg_number).first_or_404()
    recorded_by_user = User.query.get_or_404(payment.recorded_by)

    # In-memory PDF generation is a clean and efficient approach.
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # School Header
    school_name = "ALFURQAN ACADEMY"
    school_address = "Galadima Road, Mai'adua"
    
    # NOTE: The following lines that attempted to load a logo have been removed to fix the OSError.
    # The receipt will now be generated without the school logo.
    
    school_name_style = ParagraphStyle(
        'SchoolName',
        parent=styles['h1'],
        alignment=TA_CENTER,
        fontSize=20,
        spaceAfter=6,
    )
    story.append(Paragraph(f"<b>{school_name}</b>", school_name_style))
    
    school_address_style = ParagraphStyle(
        'SchoolAddress',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        fontSize=12,
        spaceAfter=12,
    )
    story.append(Paragraph(school_address, school_address_style))
    story.append(Spacer(1, 0.1 * inch))


    # Title
    receipt_title_style = ParagraphStyle(
        'ReceiptTitle',
        parent=styles['h2'],
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    story.append(Paragraph("<b>Payment Receipt</b>", receipt_title_style))
    story.append(Spacer(1, 0.2 * inch))

    # Payment details
    story.append(Paragraph(f"<b>Student Name:</b> {student.name}", styles['Normal']))
    story.append(Paragraph(f"<b>Registration Number:</b> {student.reg_number}", styles['Normal']))
    story.append(Paragraph(f"<b>Class:</b> {student.student_class}", styles['Normal']))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(f"<b>Amount Paid:</b> ₦{payment.amount_paid:,.2f}", styles['Normal']))
    story.append(Paragraph(f"<b>Payment Date:</b> {payment.payment_date}", styles['Normal']))
    story.append(Paragraph(f"<b>Term:</b> {payment.term}", styles['Normal']))
    story.append(Paragraph(f"<b>Academic Year:</b> {payment.academic_year}", styles['Normal']))
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph(f"<b>Recorded By:</b> {recorded_by_user.username}", styles['Normal']))
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph("<i>Thank you for your payment.</i>", styles['Italic']))

    doc.build(story)
    buffer.seek(0)

    filename = f"receipt_{student.name.replace(' ', '_')}_{payment.id}.pdf"
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

@main.route('/teachers')
@login_required
def teachers():
    """Route for the Teachers page."""
    teachers_list = Teacher.query.all()
    return render_template('teachers.html', title='Teachers', teachers=teachers_list)

@main.route('/teachers/add', methods=['GET', 'POST'])
@login_required
def add_teacher():
    """Handles adding a new teacher."""
    if current_user.role != 'admin':
        abort(403)
    
    if request.method == 'POST':
        # Assuming you have a form for this. For this example, we'll use a simplified version.
        name = request.form['name']
        class_taught = request.form['class_taught']
        email = request.form['email']
        phone = request.form['phone']
        
        teacher = Teacher(
            name=name,
            class_taught=class_taught,
            email=email,
            phone=phone
        )
        try:
            db.session.add(teacher)
            db.session.commit()
            flash(f'Teacher {teacher.name} added successfully!', 'success')
            return redirect(url_for('main.teachers'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: A teacher with this email already exists.', 'error')
        
    return render_template('add_teacher.html', title='Add Teacher')

@main.route('/manage_classes')
@login_required
def manage_classes():
    """Admin route to manage classes."""
    if current_user.role != 'admin':
        abort(403)
    
    all_classes = Class.query.all()
    return render_template('manage_classes.html', title='Manage Classes', classes=all_classes)

@main.route('/classes/add', methods=['GET', 'POST'])
@login_required
def add_class():
    """Handles adding a new class."""
    if current_user.role != 'admin':
        abort(403)
        
    if request.method == 'POST':
        # Get the class name from the form submission
        class_name = request.form.get('class_name', '').strip()
        
        # Check if the class name is not empty
        if not class_name:
            flash('Class name cannot be empty.', 'error')
            return redirect(url_for('main.manage_classes'))
        
        # Check if a class with that name already exists
        existing_class = Class.query.filter_by(name=class_name).first()
        if existing_class:
            flash(f"Error: The class '{class_name}' already exists.", 'error')
            return redirect(url_for('main.manage_classes'))
        
        try:
            # Create a new Class object and add it to the database
            new_class = Class(name=class_name)
            db.session.add(new_class)
            db.session.commit()
            flash(f'Class "{class_name}" added successfully!', 'success')
            return redirect(url_for('main.manage_classes'))
        except Exception as e:
            # Handle any other potential database errors
            db.session.rollback()
            flash(f'An unexpected error occurred: {e}', 'error')
            return redirect(url_for('main.manage_classes'))

    # If it's a GET request, render the add class form or redirect
    return render_template('add_class.html')
