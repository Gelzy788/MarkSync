import sqlalchemy
from flask_login import UserMixin
from config import db
from datetime import datetime

# Base = sqlalchemy.declarative.declarative_base()

class Users(db.Model, UserMixin):
    __tablename__ = 'users'
    ID = db.Column(db.Integer(), primary_key=True, autoincrement=True, nullable=False)
    username = db.Column(db.String(255), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text(), nullable=True)
    avatar = db.Column(db.String(255), nullable=True)
    refresh_token = db.Column(db.String(255), nullable=True)

class Notes(db.Model):
    __tablename__ = 'notes'
    ID = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    text = db.Column(db.Text(), nullable=True)
    user_id = db.Column(db.Integer(), db.ForeignKey(
        'users.ID'))

class NotesAccess(db.Model):
    __tablename__ = 'notes_access'
    access_level = db.Column(db.String(50), nullable=False, primary_key=True)
    note_id = db.Column(db.Integer(), db.ForeignKey(
        'notes.ID'))
    user_id = db.Column(db.Integer(), db.ForeignKey(
        'user.ID'))
