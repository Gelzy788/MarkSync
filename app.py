from flask import Flask, render_template, request, flash, redirect, url_for
from flask_login import logout_user, login_required, current_user
from autorisation import *
from database import *
from config import *
from models import *
from forms import *

login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route('/')
def main():
    return render_template('main.html', title="Главная страница")

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
        
        res = add_user(username, email, password)
        if res == 200:
            return redirect(url_for('login'))
        else:
            db.session.rollback()
            flash('Пользователь с такой почтой уже существует', 'error')
            return redirect(url_for('register'))

    return render_template('register.html', title="Регистрация")

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        res = login_user_db(email, password)
        if res[1] == 200:
            access_token = generate_access_token(res[0])
            refresh_token = generate_refresh_token(res[0])# <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            add_refresh_token_db(email, refresh_token)
            response = make_response(render_template('main.html', title="Главная страница"))
            save_tokens(response, access_token, refresh_token)
            return response
        else:
            flash('Неверный email или пароль.', 'error')

    return render_template('login.html', form=form, title="Вход в аккаунт")

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

@app.route('/logout')
def logout():
    response = make_response(redirect('/'))
    response.set_cookie('access_token', '', expires=0)  # установка expires=0 удаляет куки
    response.set_cookie('refresh_token', '', expires=0)  # установка expires=0 удаляет куки
    return response

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')

