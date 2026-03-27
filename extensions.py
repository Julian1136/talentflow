from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, CSRFError

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()