from flask import Flask, render_template, request, flash, redirect, url_for
from database import *
from config import *
from models import *

login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route('/')
def main():
    pass

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')

        if password != confirm_password:
            flash('Пароли не совпадают!', 'error')
            return redirect(url_for('register'))
        
        # try:
        res = add_user(username, email, password)
        if res == 500:
            print("аккаунт добавлен")
        else:
            db.session.rollback()
            print('Ошибка при регистрации: такой пользователь или email уже существует.', 'error')
            return redirect(url_for('register'))

    return render_template('register.html', title="Регистрация")

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')