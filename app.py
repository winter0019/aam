# app.py
from flask import Flask, render_template_string, request, redirect, url_for, flash, Blueprint
import uuid
from datetime import datetime

# --- CONFIGURATION ---
# A secret key is required for Flask sessions and flash messages.
# For a production app, this should be a complex, randomly generated string.
app = Flask(__name__)
app.secret_key = 'super_secret_key'

# Define a blueprint for our main routes to keep the code modular
main = Blueprint('main', __name__)

# Define the school short name as a constant. This makes it easy to change later.
SCHOOL_SHORT_NAME = 'AAM'

# --- IN-MEMORY DATABASE ---
# In-memory "database" to store students, payments, and fees.
# NOTE: This data is not persistent and will be reset when the server restarts.
STUDENTS = {
    "AAM/24/0001": {
        "reg_number": "AAM/24/0001",
        "name": "Abdullahi Musa",
        "dob": "2010-05-15",
        "gender": "Male",
        "address": "123 School Road",
        "phone": "08012345678",
        "email": "abdullahi@example.com",
        "student_class": "JSS1",
        "term": "First Term",
        "academic_year": "2024/2025",
        "admission_date": "2024-09-01",
        "fee_status": "Paid",
        "guardian_name": "Mr. Musa Abdullahi",
    },
    "AAM/24/0002": {
        "reg_number": "AAM/24/0002",
        "name": "Fatima Ahmed",
        "dob": "2011-02-20",
        "gender": "Female",
        "address": "456 Market Street",
        "phone": "08087654321",
        "email": "fatima@example.com",
        "student_class": "JSS2",
        "term": "First Term",
        "academic_year": "2024/2025",
        "admission_date": "2024-09-01",
        "fee_status": "Defaulter",
        "guardian_name": "Mrs. Aisha Ahmed",
    },
    "AAM/24/0003": {
        "reg_number": "AAM/24/0003",
        "name": "Umar Bello",
        "dob": "2009-08-01",
        "gender": "Male",
        "address": "789 City Avenue",
        "phone": "09011223344",
        "email": "umar@example.com",
        "student_class": "JSS1",
        "term": "Second Term",
        "academic_year": "2024/2025",
        "admission_date": "2024-09-01",
        "fee_status": "Paid",
        "guardian_name": "Mr. Bello Umar",
    },
    "AAM/23/0004": {
        "reg_number": "AAM/23/0004",
        "name": "Aisha Garba",
        "dob": "2008-11-25",
        "gender": "Female",
        "address": "101 Gwarinpa Estate",
        "phone": "07055667788",
        "email": "aisha@example.com",
        "student_class": "JSS3",
        "term": "Third Term",
        "academic_year": "2023/2024",
        "admission_date": "2023-09-01",
        "fee_status": "Paid",
        "guardian_name": "Ms. Zainab Garba",
    },
    "AAM/25/0002": {
        "reg_number": "AAM/25/0002",
        "name": "USMAN IDRIS DANGALAN",
        "dob": "2009-05-10",
        "gender": "Male",
        "address": "123 School Road, Abuja",
        "phone": "08012345678",
        "email": "usman.dangalan@example.com",
        "student_class": "SS 1",
        "term": "First Term",
        "academic_year": "2024/2025",
        "admission_date": "2024-09-01",
        "fee_status": "Paid",
        "guardian_name": "Mr. Haruna Dangalan",
    }
}
# Dummy data for payments and fees
FEES = {
    "AAM/25/0002": {
        "First Term": {"expected": 30000.00, "paid": 30000.00, "outstanding": 0.00},
        "Second Term": {"expected": 30000.00, "paid": 0.00, "outstanding": 30000.00},
        "Third Term": {"expected": 30000.00, "paid": 0.00, "outstanding": 30000.00}
    }
}

PAYMENTS = {
    "AAM/25/0002": [
        {"amount": 30000.00, "date": "2025-08-16", "term": "First Term", "academic_year": "2024/2025", "status": "Paid"},
        {"amount": 10000.00, "date": "2025-09-01", "term": "Second Term", "academic_year": "2024/2025", "status": "Partial"},
        {"amount": 0.00, "date": "2025-09-01", "term": "Third Term", "academic_year": "2024/2025", "status": "Unpaid"}
    ],
    "AAM/24/0001": [
        {"amount": 30000.00, "date": "2024-09-05", "term": "First Term", "academic_year": "2024/2025", "status": "Paid"},
    ],
    "AAM/24/0002": [], # No payments for this defaulter
    "AAM/24/0003": [
        {"amount": 30000.00, "date": "2024-09-10", "term": "Second Term", "academic_year": "2024/2025", "status": "Paid"},
    ],
    "AAM/23/0004": [
        {"amount": 30000.00, "date": "2023-09-01", "term": "First Term", "academic_year": "2023/2024", "status": "Paid"},
        {"amount": 30000.00, "date": "2023-01-05", "term": "Second Term", "academic_year": "2023/2024", "status": "Paid"},
        {"amount": 30000.00, "date": "2023-04-12", "term": "Third Term", "academic_year": "2023/2024", "status": "Paid"}
    ]
}

# --- MOCK USER FOR DEMO ---
class MockUser:
    def __init__(self, username, role):
        self.username = username
        self.role = role

# Mock user for demonstration purposes
current_user = MockUser(username="Admin User", role="admin")


# --- HTML TEMPLATES ---
# These templates are stored as Python strings. In a larger project, you would
# use separate HTML files in a 'templates' directory.
BASE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alfurqan Academy</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; }
    </style>
</head>
<body class="bg-gray-100 flex min-h-screen">
    <!-- Sidebar -->
    <aside class="w-64 bg-white p-6 shadow-md flex flex-col">
        <h1 class="text-3xl font-bold text-gray-800 mb-8">Alfurqan</h1>
        <nav class="flex-grow">
            <ul class="space-y-2">
                <li><a href="{{ url_for('main.dashboard') }}" class="flex items-center p-3 text-lg font-medium text-gray-600 hover:bg-gray-200 rounded-lg transition-colors duration-200"><i class="fas fa-home mr-3"></i>Dashboard</a></li>
                <li><a href="{{ url_for('main.students') }}" class="flex items-center p-3 text-lg font-medium text-white bg-blue-600 rounded-lg transition-colors duration-200"><i class="fas fa-user-graduate mr-3"></i>Students</a></li>
                <li><a href="{{ url_for('main.teachers') }}" class="flex items-center p-3 text-lg font-medium text-gray-600 hover:bg-gray-200 rounded-lg transition-colors duration-200"><i class="fas fa-chalkboard-teacher mr-3"></i>Teachers</a></li>
                <li><a href="{{ url_for('main.manage_classes') }}" class="flex items-center p-3 text-lg font-medium text-gray-600 hover:bg-gray-200 rounded-lg transition-colors duration-200"><i class="fas fa-school mr-3"></i>Classes</a></li>
                <li><a href="{{ url_for('main.fees') }}" class="flex items-center p-3 text-lg font-medium text-gray-600 hover:bg-gray-200 rounded-lg transition-colors duration-200"><i class="fas fa-wallet mr-3"></i>Fees & Payments</a></li>
                <li><a href="{{ url_for('main.reports') }}" class="flex items-center p-3 text-lg font-medium text-gray-600 hover:bg-gray-200 rounded-lg transition-colors duration-200"><i class="fas fa-chart-bar mr-3"></i>Reports</a></li>
                <li><a href="{{ url_for('main.settings') }}" class="flex items-center p-3 text-lg font-medium text-gray-600 hover:bg-gray-200 rounded-lg transition-colors duration-200"><i class="fas fa-cogs mr-3"></i>Settings</a></li>
            </ul>
        </nav>
        <div class="mt-8">
            <a href="{{ url_for('main.logout') }}" class="block text-center p-3 text-lg font-medium text-red-600 bg-red-100 rounded-lg hover:bg-red-200 transition-colors duration-200"><i class="fas fa-sign-out-alt mr-2"></i>Log Out</a>
        </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 p-8 overflow-y-auto">
        {% block content %}{% endblock %}
    </main>
</body>
</html>
"""

STUDENTS_LIST_HTML = """
{% extends 'base.html' %}

{% block content %}
    <header class="flex flex-col sm:flex-row justify-between items-center mb-6 space-y-4 sm:space-y-0">
        <h2 class="text-3xl font-semibold text-gray-800">Student Directory</h2>
        <div class="flex flex-col sm:flex-row items-center space-y-4 sm:space-x-4 sm:space-y-0">
            <span class="text-gray-600">Welcome, {{ current_user.username }}!</span>
            <a href="{{ url_for('main.register_student') }}" class="w-full sm:w-auto text-center bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200">
                <i class="fas fa-plus mr-2"></i>New Student
            </a>
        </div>
    </header>

    <!-- Flash Messages -->
    {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
        <div id="flash-container" class="space-y-2">
            {% for category, message in messages %}
            <div class="flash-message bg-{{ 'green' if category == 'success' else 'red' }}-500 text-white p-4 rounded-lg shadow-md transition-all duration-500 transform translate-x-full" role="alert">
                {{ message }}
            </div>
            {% endfor %}
        </div>
        <script>
            document.addEventListener('DOMContentLoaded', () => {
                const messages = document.querySelectorAll('#flash-container .flash-message');
                messages.forEach((msg, index) => {
                    setTimeout(() => {
                        msg.classList.add('show');
                    }, index * 100);
                    setTimeout(() => {
                        msg.classList.remove('show');
                        msg.classList.add('hide');
                        msg.addEventListener('transitionend', () => msg.remove());
                    }, 5000 + index * 100);
                });
            });
        </script>
    {% endif %}
    {% endwith %}

    <!-- Filter and Search Section -->
    <div class="bg-white p-6 rounded-xl shadow-lg mb-6">
        <form action="{{ url_for('main.students') }}" method="get" class="grid grid-cols-1 md:grid-cols-5 gap-4 items-center">
            <div class="md:col-span-2">
                <label for="search_query" class="sr-only">Search</label>
                <div class="relative">
                    <input type="text" id="search_query" name="search_query" value="{{ search_query }}" placeholder="Search by name or registration number..." class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <i class="fas fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
                </div>
            </div>

            <select id="class_filter" name="class" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="all" {% if class_filter == 'all' %}selected{% endif %}>All Classes</option>
                {% for class_name in classes %}
                <option value="{{ class_name }}" {% if class_name == class_filter %}selected{% endif %}>{{ class_name }}</option>
                {% endfor %}
            </select>

            <select id="term_filter" name="term" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="all" {% if term_filter == 'all' %}selected{% endif %}>All Terms</option>
                {% for term_name in terms %}
                <option value="{{ term_name }}" {% if term_name == term_filter %}selected{% endif %}>{{ term_name }}</option>
                {% endfor %}
            </select>
            
            <select id="status_filter" name="status" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="all" {% if status_filter == 'all' %}selected{% endif %}>All Statuses</option>
                <option value="Paid" {% if status_filter == 'Paid' %}selected{% endif %}>Paid</option>
                <option value="Defaulter" {% if status_filter == 'Defaulter' %}selected{% endif %}>Defaulter</option>
            </select>
        </form>
    </div>

    <!-- Student List Table -->
    <div class="bg-white rounded-xl shadow-lg overflow-hidden">
        {% if students %}
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Reg. Number</th>
                    <th class="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Name</th>
                    <th class="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Class</th>
                    <th class="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Admission Date</th>
                    <th class="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Fee Status</th>
                    <th class="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
                {% for student in students %}
                <tr>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ student.reg_number }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{{ student.name }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{{ student.student_class }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{{ student.admission_date }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm">
                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full
                            {% if student.fee_status == 'Paid' %}bg-green-100 text-green-800{% elif student.fee_status == 'Defaulter' %}bg-red-100 text-red-800{% else %}bg-gray-100 text-gray-800{% endif %}">
                            {{ student.fee_status }}
                        </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <a href="{{ url_for('main.student_details', reg_number=student.reg_number) }}" 
                           class="text-blue-600 hover:text-blue-900 mr-2">Details</a>
                        {% if current_user.role in ['admin', 'officer'] %}
                        <a href="{{ url_for('main.make_payment', reg_number=student.reg_number) }}" class="text-green-600 hover:text-green-900">Payment</a>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="p-6 text-center text-gray-500">
            <p>No students found matching your criteria.</p>
        </div>
        {% endif %}
    </div>
{% endblock %}
"""

STUDENT_DETAILS_HTML = """
{% extends 'base.html' %}

{% block content %}
<div class="container mx-auto p-6 bg-gray-100 min-h-screen font-sans">
    <div class="max-w-4xl mx-auto bg-white p-8 rounded-xl shadow-lg space-y-6">

        <!-- Student Header -->
        <div class="flex items-center justify-between border-b pb-4">
            <div class="flex items-center space-x-4">
                <img src="https://placehold.co/128x128/e5e7eb/7f8c8d?text=Photo" alt="Student Photo" class="w-16 h-16 rounded-full border-2 border-gray-200">
                <div>
                    <h1 class="text-2xl font-bold text-green-700">{{ student.name }}</h1>
                    <p class="text-gray-500 text-sm">Student ID: {{ student.reg_number }}</p>
                </div>
            </div>
            <span class="px-4 py-2 rounded-lg bg-green-100 text-green-700 text-sm font-semibold">
                {{ student.student_class }}
            </span>
        </div>

        <!-- Basic Info -->
        <div>
            <h2 class="text-xl font-semibold text-gray-700 mb-3">📌 Personal Information</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="p-4 bg-gray-50 rounded-lg">
                    <p class="text-sm text-gray-500">Full Name</p>
                    <p class="font-medium text-gray-800">{{ student.name }}</p>
                </div>
                <div class="p-4 bg-gray-50 rounded-lg">
                    <p class="text-sm text-gray-500">Date of Birth</p>
                    <p class="font-medium text-gray-800">{{ student.dob }}</p>
                </div>
                <div class="p-4 bg-gray-50 rounded-lg">
                    <p class="text-sm text-gray-500">Gender</p>
                    <p class="font-medium text-gray-800">{{ student.gender }}</p>
                </div>
                <div class="p-4 bg-gray-50 rounded-lg">
                    <p class="text-sm text-gray-500">Guardian</p>
                    <p class="font-medium text-gray-800">{{ student.guardian_name }}</p>
                </div>
            </div>
        </div>

        <!-- Academic Info -->
        <div>
            <h2 class="text-xl font-semibold text-gray-700 mb-3">📖 Academic Information</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="p-4 bg-gray-50 rounded-lg">
                    <p class="text-sm text-gray-500">Class</p>
                    <p class="font-medium text-gray-800">{{ student.student_class }}</p>
                </div>
                <div class="p-4 bg-gray-50 rounded-lg">
                    <p class="text-sm text-gray-500">Admission Date</p>
                    <p class="font-medium text-gray-800">{{ student.admission_date }}</p>
                </div>
            </div>
        </div>

        <!-- Payments -->
        <div>
            <h2 class="text-xl font-semibold text-gray-700 mb-3">💰 Payment Records</h2>
            <table class="w-full text-left border-collapse">
                <thead>
                    <tr class="bg-green-100 text-green-800">
                        <th class="px-4 py-2">Date</th>
                        <th class="px-4 py-2">Amount</th>
                        <th class="px-4 py-2">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for payment in payments %}
                    <tr class="border-b">
                        <td class="px-4 py-2">{{ payment.date }}</td>
                        <td class="px-4 py-2">₦{{ '%.2f'|format(payment.amount) }}</td>
                        <td class="px-4 py-2">
                            <span class="px-2 py-1 text-sm rounded-lg
                                {% if payment.status == 'Paid' %}
                                    bg-green-100 text-green-700
                                {% elif payment.status == 'Partial' %}
                                    bg-yellow-100 text-yellow-700
                                {% else %}
                                    bg-red-100 text-red-700
                                {% endif %}">
                                {{ payment.status }}
                            </span>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="3" class="px-4 py-4 text-center text-gray-500">No payments recorded yet.</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <!-- Actions -->
        <div class="flex flex-col sm:flex-row justify-end space-y-2 sm:space-y-0 sm:space-x-3 pt-4 border-t">
            <a href="{{ url_for('main.edit_student', reg_number=student.reg_number) }}" 
               class="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 text-center">
                Edit Details
            </a>
            <a href="{{ url_for('main.students') }}" 
               class="px-4 py-2 rounded-lg bg-gray-200 text-gray-700 hover:bg-gray-300 text-center">
                Back to Students
            </a>
        </div>
    </div>
</div>
{% endblock %}
"""

REGISTER_STUDENT_HTML = """
{% extends 'base.html' %}

{% block content %}
<div class="form-container bg-white p-8 rounded-xl shadow-lg w-full max-w-2xl mx-auto">
    <h2 class="text-3xl font-bold text-center text-gray-800 mb-6">Register New Student</h2>
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            <div id="flash-messages" class="mb-4 space-y-2">
                {% for category, message in messages %}
                    <div class="p-4 rounded-lg flex items-center justify-between {% if category == 'error' %}bg-red-100 text-red-700{% elif category == 'success' %}bg-green-100 text-green-700{% endif %}">
                        <span class="text-sm font-medium">{{ message }}</span>
                    </div>
                {% endfor %}
            </div>
        {% endif %}
    {% endwith %}
    <form action="{{ url_for('main.register_student') }}" method="POST" class="space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
                <label for="name" class="block text-sm font-medium text-gray-700 mb-1">Full Name *</label>
                <input type="text" id="name" name="name" required class="w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 transition duration-150 ease-in-out">
            </div>
            <div>
                <label for="dob" class="block text-sm font-medium text-gray-700 mb-1">Date of Birth *</label>
                <input type="date" id="dob" name="dob" required class="w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 transition duration-150 ease-in-out">
            </div>
            <div>
                <label for="gender" class="block text-sm font-medium text-gray-700 mb-1">Gender *</label>
                <select id="gender" name="gender" required class="w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 transition duration-150 ease-in-out">
                    <option value="">Select Gender</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                </select>
            </div>
            <div>
                <label for="address" class="block text-sm font-medium text-gray-700 mb-1">Address *</label>
                <input type="text" id="address" name="address" required class="w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 transition duration-150 ease-in-out">
            </div>
            <div>
                <label for="phone" class="block text-sm font-medium text-gray-700 mb-1">Phone Number *</label>
                <input type="tel" id="phone" name="phone" required class="w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 transition duration-150 ease-in-out">
            </div>
            <div>
                <label for="email" class="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                <input type="email" id="email" name="email" required class="w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 transition duration-150 ease-in-out">
            </div>
            <div>
                <label for="student_class" class="block text-sm font-medium text-gray-700 mb-1">Class *</label>
                <select id="student_class" name="student_class" required class="w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 transition duration-150 ease-in-out">
                    <option value="">Select Class</option>
                    {% for c in classes %}<option value="{{ c }}">{{ c }}</option>{% endfor %}
                </select>
            </div>
            <div>
                <label for="term" class="block text-sm font-medium text-gray-700 mb-1">Term *</label>
                <select id="term" name="term" required class="w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 transition duration-150 ease-in-out">
                    <option value="">Select Term</option>
                    {% for t in terms %}<option value="{{ t }}">{{ t }}</option>{% endfor %}
                </select>
            </div>
            <div>
                <label for="academic_year" class="block text-sm font-medium text-gray-700 mb-1">Academic Year *</label>
                <select id="academic_year" name="academic_year" required class="w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-150 ease-in-out">
                    <option value="">Select Academic Year</option>
                    {% for y in academic_years %}<option value="{{ y }}">{{ y }}</option>{% endfor %}
                </select>
            </div>
        </div>
        <button type="submit" class="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg shadow-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition duration-150 ease-in-out">
            Register Student
        </button>
    </form>
</div>
{% endblock %}
"""

# --- HELPER FUNCTIONS ---
# This counter is a simple way to generate unique serial numbers.
# In a real application, you would use a database to manage this.
REG_NUMBER_COUNTER = 5
def generate_reg_number(academic_year):
    """
    Generates a unique registration number based on the school's short name
    and the academic year.
    Example: AAM/25/0006
    """
    global REG_NUMBER_COUNTER
    REG_NUMBER_COUNTER += 1
    year = academic_year.split('/')[0][-2:]
    serial_number = str(REG_NUMBER_COUNTER).zfill(4)
    # Use the SCHOOL_SHORT_NAME constant for flexibility
    return f"{SCHOOL_SHORT_NAME}/{year}/{serial_number}"


# --- ROUTES ---
@app.route('/')
def index():
    # A simple redirect to the students' list page for the demo
    return redirect(url_for('main.students'))

@main.route('/students')
def students():
    # Get filters from the request query string
    search_query = request.args.get('search_query', '').lower()
    class_filter = request.args.get('class', 'all')
    term_filter = request.args.get('term', 'all')
    status_filter = request.args.get('status', 'all')

    # Apply filters to the student data
    filtered_students = []
    for reg_number, student in STUDENTS.items():
        # Apply search filter
        if search_query and \
           search_query not in student['name'].lower() and \
           search_query not in student['reg_number'].lower():
            continue

        # Apply class filter
        if class_filter != 'all' and student['student_class'] != class_filter:
            continue

        # Apply term filter
        if term_filter != 'all' and student['term'] != term_filter:
            continue
        
        # Apply status filter
        if status_filter != 'all' and student['fee_status'] != status_filter:
            continue

        filtered_students.append(student)

    # Sort students by registration number
    filtered_students.sort(key=lambda s: s['reg_number'])

    # Define available options for the filters
    classes = sorted(list(set(s['student_class'] for s in STUDENTS.values())))
    terms = sorted(list(set(s['term'] for s in STUDENTS.values())))
    
    return render_template_string(
        STUDENTS_LIST_HTML,
        students=filtered_students,
        classes=classes,
        terms=terms,
        search_query=search_query,
        class_filter=class_filter,
        term_filter=term_filter,
        status_filter=status_filter,
        current_user=current_user,
        url_for=url_for
    )

@main.route('/register_student', methods=['GET', 'POST'])
def register_student():
    # Define class, term, and academic year options for the form
    classes = ['JSS1', 'JSS2', 'JSS3', 'SSS1', 'SSS2', 'SSS3', 'SS 1', 'SS 2', 'SS 3']
    terms = ['First Term', 'Second Term', 'Third Term']
    academic_years = ['2023/2024', '2024/2025', '2025/2026']

    if request.method == 'POST':
        # Get data from the form
        name = request.form['name']
        dob = request.form['dob']
        gender = request.form['gender']
        address = request.form['address']
        phone = request.form['phone']
        email = request.form['email']
        student_class = request.form['student_class']
        term = request.form['term']
        academic_year = request.form['academic_year']
        guardian_name = "N/A" # Default for new students

        # Generate a unique registration number
        reg_number = generate_reg_number(academic_year)

        # Create a new student dictionary
        student_data = {
            'reg_number': reg_number,
            'name': name,
            'dob': dob,
            'gender': gender,
            'address': address,
            'phone': phone,
            'email': email,
            'student_class': student_class,
            'term': term,
            'academic_year': academic_year,
            'admission_date': datetime.now().strftime('%Y-%m-%d'),
            'fee_status': 'Defaulter', # Default status for a new student
            'guardian_name': guardian_name
        }
        # Add the new student to our in-memory "database"
        STUDENTS[reg_number] = student_data
        flash('Student registered successfully!', 'success')
        return redirect(url_for('main.student_details', reg_number=reg_number))

    return render_template_string(
        REGISTER_STUDENT_HTML,
        title="Register New Student",
        classes=classes,
        terms=terms,
        academic_years=academic_years,
        current_user=current_user,
        url_for=url_for
    )

@main.route('/student/<reg_number>')
def student_details(reg_number):
    # Retrieve student data and payments
    student = STUDENTS.get(reg_number)
    student_payments = PAYMENTS.get(reg_number, [])
    
    # Render the student details page with the data
    return render_template_string(
        STUDENT_DETAILS_HTML,
        title=f"Details for {student.get('name') if student else 'Student'}",
        student=student,
        payments=student_payments,
        current_user=current_user,
        url_for=url_for
    )

# Placeholder routes for the other pages in your sidebar
@main.route('/dashboard')
def dashboard():
    return render_template_string(BASE_HTML + '<p class="text-center text-gray-500">Dashboard functionality goes here.</p>', title="Dashboard", current_user=current_user, url_for=url_for)

@main.route('/teachers')
def teachers():
    return render_template_string(BASE_HTML + '<p class="text-center text-gray-500">Teachers functionality goes here.</p>', title="Teachers", current_user=current_user, url_for=url_for)

@main.route('/manage_classes')
def manage_classes():
    return render_template_string(BASE_HTML + '<p class="text-center text-gray-500">Manage Classes functionality goes here.</p>', title="Manage Classes", current_user=current_user, url_for=url_for)

@main.route('/fees')
def fees():
    return render_template_string(BASE_HTML + '<p class="text-center text-gray-500">Fees & Payments functionality goes here.</p>', title="Fees & Payments", current_user=current_user, url_for=url_for)

@main.route('/reports')
def reports():
    return render_template_string(BASE_HTML + '<p class="text-center text-gray-500">Reports functionality goes here.</p>', title="Reports", current_user=current_user, url_for=url_for)

@main.route('/settings')
def settings():
    return render_template_string(BASE_HTML + '<p class="text-center text-gray-500">Settings functionality goes here.</p>', title="Settings", current_user=current_user, url_for=url_for)

@main.route('/logout')
def logout():
    flash("You have been logged out.", "success")
    # In a real app, this would clear the user session.
    # We redirect to a public page for now.
    return redirect(url_for('main.students'))

@main.route('/edit_student/<reg_number>')
def edit_student(reg_number):
    return render_template_string(BASE_HTML + '<p class="text-center text-gray-500">Edit Student functionality goes here.</p>', title="Edit Student", current_user=current_user, url_for=url_for)

@main.route('/download_receipt/<receipt_id>')
def download_receipt(receipt_id):
    return render_template_string(BASE_HTML + f'<p class="text-center text-gray-500">Download receipt {receipt_id} functionality goes here.</p>', title="Download Receipt", current_user=current_user, url_for=url_for)

@main.route('/make_payment/<reg_number>')
def make_payment(reg_number):
    return render_template_string(BASE_HTML + f'<p class="text-center text-gray-500">Make payment for {reg_number} functionality goes here.</p>', title="Make Payment", current_user=current_user, url_for=url_for)

# --- APPLICATION ENTRY POINT ---
app.register_blueprint(main)

if __name__ == '__main__':
    # Run the application in debug mode for development
    app.run(debug=True)
