from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'e3f0f3eae8e4f8f2e0fdeff6fcfdefeaf2e6f9'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://gelzy:Azizalinegm145!@185.247.185.193/MarkSync'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '012259938c080b981098d67f328138f1cb624b0a84b3e4ad391f2c89fc645aaa'
ACCESS_TOKEN_SECRET_KEY = 'bd9fb0336fca367efcee6ddae2dc707ccf2a55d3f2477f222157563b1f0b6e71'
REFRESH_TOKEN_SECRET_KEY = 'c80a73442699651fc4297eda6691f2960714a66225b7d31cf8daa4c4ab78f3dd'
ACCESS_TOKEN_EXPIRATION_TIME = 1 # В минутах
REFRESH_TOKEN_EXPIRATION_TIME = 30 # В днях
db = SQLAlchemy(app)
# login_manager = LoginManager()
# csrf = CSRFProtect(app)