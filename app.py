from config import *
from data.__all_models import *
from data.users import Users
from data.notes import Notes
from data.notes_access import NotesAccess
from forms.register_form import *
from data import auth_blueprint, notes_blueprint
from data.utils import convert_diagrams, convert_tasks, token_required
import markdown2
from data.utils import extract_diagrams, generate_pdf_from_markdown
from flask import render_template, request, jsonify, send_file

# Загрузка микро-приложений
app.register_blueprint(auth_blueprint)
app.register_blueprint(notes_blueprint)

# Главная страница
@app.route('/')
def main():
    return render_template('main.html', title="Главная страница")

# Страница профиля
@app.route('/profile')
@token_required
def profile(user):
    return render_template('profile.html', username=user.username, email=user.email, title="Профиль")


# Страница с заметками
@app.route('/marks', methods=['GET', 'POST'])
@token_required
def marks(user):
    files = Notes.query.filter_by(user_id=user.ID).all()
    notes_accesses = NotesAccess.query.filter_by(user_id=user.ID).all()
    for i in notes_accesses:
        note = Notes.query.filter_by(ID=i.note_id).first()
        if note:
            files.append(note)
    
    text = ''
    html = ''
    if request.method == 'POST':
        text = request.form['text']
        text = convert_tasks(text)
        text = convert_diagrams(text)
        html = markdown2.markdown(text, extras=["fenced-code-blocks", "tables", "strike"])
    print([i.ID for i in files])
    return render_template('editor.html', text=text, html=html, files=files)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', ssl_context=('ssl/cert.pem', 'ssl/key.pem'))