from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
import os
from dotenv import load_dotenv
load_dotenv()
from pathlib import Path

# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()

def create_app():
    # Task 8 & 9: 
    # Prevent CSRF attacks 
    csrf = CSRFProtect()
    app = Flask(__name__)
    csrf.init_app(app)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///photos.db'
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JS access to cookies.
    # Task 8 & 9: 
    # Prevents cookies from being sent with cross-site POST requests
    # Absence of the session cookies will prevent POST requests from 
        # third party malicious websites from being successful
        # as the session will not be recognised
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  

    CWD = Path(os.path.dirname(__file__))
    app.config['UPLOAD_DIR'] = CWD / "uploads"

    db.init_app(app)

    # blueprint for non-auth parts of app
    from .main import main as main_blueprint
    from .auth import auth as auth_blueprint
    from .searchfeature import searchfeature as search_blueprint
    
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(search_blueprint)

    return app
