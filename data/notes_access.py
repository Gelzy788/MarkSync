from config import db


# Класс таблицы notes_access
class NotesAccess(db.Model):
    __tablename__ = 'notes_access'
    id = db.Column(db.Integer, primary_key=True)  # Добавляем автоинкрементный ID
    access_level = db.Column(db.String(50), nullable=False)
    note_id = db.Column(db.Integer(), db.ForeignKey('notes.ID'))
    user_id = db.Column(db.Integer(), db.ForeignKey('users.ID'))
    
    # Добавляем уникальный индекс для предотвращения дублирования
    __table_args__ = (
        db.UniqueConstraint('note_id', 'user_id', name='_note_user_uc'),
    )