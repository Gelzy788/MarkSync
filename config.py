from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'e3f0f3eae8e4f8f2e0fdeff6fcfdefeaf2e6f9'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://gelzy:Azizalinegm145!@185.247.185.193/MarkSync'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
# csrf = CSRFProtect(app)