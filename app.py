from autorisation import *
# from archive.database import *
from config import *
from data.__all_models import *
from forms.register_form import *
from data import auth_blueprint

from flask import Flask, render_template, request, flash, redirect, url_for, jsonify

app.register_blueprint(auth_blueprint)

@app.route('/')
def main():
    return render_template('main.html', title="Главная страница")

@app.route('/profile')
@token_required
def profile(user):
    # user = get_user()
    return render_template('profile.html', username=user.username, email=user.email, title="Профиль")


@app.route('/protected')
@token_required
def protected(user):
    user = get_user()
    return jsonify({'message': f'Hello, {user.username}! This is a protected API endpoint.'})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')

