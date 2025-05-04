from autorisation import *
from config import *
from data.__all_models import *
from forms.register_form import *
from data import auth_blueprint
# временно
from main import convert_diagrams, convert_tasks
import markdown2

from flask import Flask, render_template, request, flash, redirect, url_for, jsonify

app.register_blueprint(auth_blueprint)

@app.route('/')
def main():
    return render_template('main.html', title="Главная страница")

@app.route('/profile')
@token_required
def profile(user):
    return render_template('profile.html', username=user.username, email=user.email, title="Профиль")


@app.route('/protected')
@token_required
def protected(user):
    return jsonify({'message': f'Hello, {user.username}! This is a protected API endpoint.'})


@app.route('/marks', methods=['GET', 'POST'])
@token_required
def marks(user):
    files = Notes.query.filter_by(user_id=user.ID).all()
    text = ''
    html = ''
    if request.method == 'POST':
        text = request.form['text']
        text = convert_tasks(text)
        text = convert_diagrams(text)
        html = markdown2.markdown(text, extras=["fenced-code-blocks", "tables", "strike"])
    return render_template('editor.html', text=text, html=html, files=files)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')

