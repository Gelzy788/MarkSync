from flask_login import UserMixin
from config import db


class Users(db.Model, UserMixin):
    __tablename__ = 'users'
    ID = db.Column(db.Integer(), primary_key=True, autoincrement=True, nullable=False)
    username = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text(), nullable=True)
    avatar = db.Column(db.String(255), nullable=True)
    refresh_token = db.Column(db.String(256))

    def get_id(self):
        return str(self.ID)
    
    def get_refresh_token(self):
        return str(self.refresh_token)