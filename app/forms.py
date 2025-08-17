from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email

# This file defines the forms that will be used to capture user input.
# The forms are created using Flask-WTF and wtforms.

class LoginForm(FlaskForm):
    """A simple form for user login."""
    # The 'Username' field requires data and must be between 2 and 50 characters.
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=2, max=50)]
    )
    # The 'Password' field requires data.
    password = PasswordField(
        'Password',
        validators=[DataRequired()]
    )
    # The submit button for the form.
    submit = SubmitField('Login')

class CreateUserForm(FlaskForm):
    """A form for creating new users."""
    # The 'Username' field requires data and must be between 2 and 50 characters.
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=2, max=50)]
    )
    # The 'Password' field requires data and must be at least 6 characters long.
    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=6)]
    )
    # The 'Role' field requires data to specify the user's role (e.g., admin, teacher).
    role = StringField(
        'Role',
        validators=[DataRequired()]
    )
    # The submit button for the form.
    submit = SubmitField('Create User')

class TeacherForm(FlaskForm):
    """
    Form to handle adding a new teacher.
    It includes fields for name, class taught, email, and phone number.
    """
    name = StringField('Name', validators=[DataRequired()])
    class_taught = StringField('Class Taught', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    submit = SubmitField('Add Teacher')

