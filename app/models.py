from flask_login import UserMixin
from . import db, bcrypt

class User(db.Model, UserMixin):
    """
    Represents a user in the system, with roles and a secure password.
    Inherits from `db.Model` and `UserMixin` for Flask-Login functionality.
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(64), default='user', nullable=False)

    @property
    def password(self):
        """Prevents access to password property"""
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        """Hashes the password before storing it"""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Checks if the provided password matches the stored hash"""
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Student(db.Model):
    """
    Represents a student and their demographic information.
    """
    __tablename__ = 'students'
    
    reg_number = db.Column(db.String(20), primary_key=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.String(10), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    student_class = db.Column(db.String(50), nullable=False)
    term = db.Column(db.String(50), nullable=False)
    academic_year = db.Column(db.String(10), nullable=False)
    admission_date = db.Column(db.String(10), nullable=False)
    
    # Define a relationship with the Payment model.
    # `back_populates` links the two ends of the relationship.
    payments = db.relationship('Payment', back_populates='student', lazy=True)

    def __repr__(self):
        return f'<Student {self.reg_number} - {self.name}>'

class Teacher(db.Model):
    """
    Represents a teacher.
    """
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_taught = db.Column(db.String(50))
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    
    def __repr__(self):
        return f'<Teacher {self.name}>'

class Payment(db.Model):
    """
    Represents a fee payment made by a student.
    """
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_reg_number = db.Column(db.String(20), db.ForeignKey('students.reg_number'), nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    term = db.Column(db.String(50), nullable=False)
    academic_year = db.Column(db.String(10), nullable=False)
    payment_date = db.Column(db.String(10), nullable=False)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Define a relationship to the student who made the payment.
    student = db.relationship('Student', back_populates='payments')
    # Define a relationship to the user who recorded the payment.
    recorder = db.relationship('User', backref='payments_recorded')

    def __repr__(self):
        return f'<Payment {self.id} for {self.student_reg_number}>'

# New Fee Model to support dynamic fee management
class Fee(db.Model):
    """
    Represents the fee amount for a specific class, term, and academic year.
    This replaces the hardcoded FEE_STRUCTURE dictionary.
    """
    __tablename__ = 'fees'

    id = db.Column(db.Integer, primary_key=True)
    student_class = db.Column(db.String(50), nullable=False)
    term = db.Column(db.String(50), nullable=False)
    academic_year = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('student_class', 'term', 'academic_year', name='_class_term_year_uc'),
    )

    def __repr__(self):
        return f"<Fee {self.student_class} - {self.term} - {self.academic_year}>"

# New Class Model to support dynamic class management
class Class(db.Model):
    """
    Represents a class in the school (e.g., JSS 1, SS 3).
    This allows admins to add classes dynamically.
    """
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Class {self.name}>'
