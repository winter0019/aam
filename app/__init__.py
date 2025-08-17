import os
import secrets
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()

# Models (only existing ones)
from .models import User, Student, Payment, Teacher

# Fee structure (class, term) -> amount
FEE_STRUCTURE = {
    ('JSS 1', 'First Term'): 25000.00,
    ('JSS 1', 'Second Term'): 20000.00,
    ('JSS 1', 'Third Term'): 20000.00,
    ('JSS 2', 'First Term'): 27000.00,
    ('JSS 2', 'Second Term'): 22000.00,
    ('JSS 2', 'Third Term'): 22000.00,
    ('JSS 3', 'First Term'): 30000.00,
    ('JSS 3', 'Second Term'): 25000.00,
    ('JSS 3', 'Third Term'): 25000.00,
    ('SS 1', 'First Term'): 35000.00,
    ('SS 1', 'Second Term'): 30000.00,
    ('SS 1', 'Third Term'): 30000.00,
    ('SS 2', 'First Term'): 37000.00,
    ('SS 2', 'Second Term'): 32000.00,
    ('SS 2', 'Third Term'): 32000.00,
    ('SS 3', 'First Term'): 40000.00,
    ('SS 3', 'Second Term'): 35000.00,
    ('SS 3', 'Third Term'): 35000.00,
}

def get_current_school_period():
    """
    Determines the current academic year and term based on the current month.
    """
    now = datetime.now()
    month = now.month
    
    if 9 <= month <= 12:
        academic_year = f"{now.year}/{now.year + 1}"
        term = "First Term"
    elif 1 <= month <= 4:
        academic_year = f"{now.year - 1}/{now.year}"
        term = "Second Term"
    else: # 5 <= month <= 8
        academic_year = f"{now.year - 1}/{now.year}"
        term = "Third Term"
        
    return {
        'academic_year': academic_year,
        'term': term
    }

def create_app():
    app = Flask(__name__, instance_relative_config=True) # Use instance_relative_config
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace(
            "postgresql://", "postgresql+psycopg2://", 1
        )
    else:
        # The key fix: Point to 'site.db' inside the 'instance' folder
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'site.db')

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Init extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    login_manager.login_view = 'main.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Currency formatting filter
    @app.template_filter('format_currency')
    def format_currency_filter(value):
        try:
            return f"₦{float(value):,.2f}"
        except (ValueError, TypeError):
            return "₦0.00"

    # Register blueprint
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    return app

# App instance for running directly
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
