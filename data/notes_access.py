from config import db


class NotesAccess(db.Model):
    __tablename__ = 'notes_access'
    access_level = db.Column(db.String(50), nullable=False, primary_key=True)
    note_id = db.Column(db.Integer(), db.ForeignKey(
        'notes.ID'))
    user_id = db.Column(db.Integer(), db.ForeignKey(
        'user.ID'))