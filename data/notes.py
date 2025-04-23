from config import db


class Notes(db.Model):
    __tablename__ = 'notes'
    ID = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    text = db.Column(db.Text(), nullable=True)
    user_id = db.Column(db.Integer(), db.ForeignKey(
        'users.ID'))