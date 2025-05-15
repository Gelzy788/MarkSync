from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
# авторизация MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://gelzy:Azizalinegm145!@185.247.185.193/MarkSync'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Секретный ключ
app.config['SECRET_KEY'] = '012259938c080b981098d67f328138f1cb624b0a84b3e4ad391f2c89fc645aaa'
# Секретный ключ для access токена
ACCESS_TOKEN_SECRET_KEY = 'bd9fb0336fca367efcee6ddae2dc707ccf2a55d3f2477f222157563b1f0b6e71'
# секретный ключ для refresh токена
REFRESH_TOKEN_SECRET_KEY = 'c80a73442699651fc4297eda6691f2960714a66225b7d31cf8daa4c4ab78f3dd'
ACCESS_TOKEN_EXPIRATION_TIME = 1  # Время жизни access токена в минутах
REFRESH_TOKEN_EXPIRATION_TIME = 30  # Время жизни refresh токена в днях
db = SQLAlchemy(app)
