from . import auth_blueprint
from .auth_services import *
from forms.register_form import RegistrationForm
from forms.login_form import LoginForm

from flask import render_template, request, redirect, url_for, flash, make_response


# Страница регистрации
@auth_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')

        if password != confirm_password:
            flash('Пароли не совпадают!', 'error')
            return redirect(url_for('auth.register'))
        
        res = add_user(username, email, password)
        if res == 200:
            return redirect(url_for('auth.login'))
        else:
            db.session.rollback()
            flash('Пользователь с такой почтой уже существует', 'error')
            return redirect(url_for('auth.register'))

    return render_template('register.html', title="Регистрация")


# Страница входа в аккаунт
@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        res = login_user_db(email, password)
        if res[1] == 200:
            access_token = generate_access_token(res[0])
            refresh_token = generate_refresh_token(res[0])
            add_refresh_token_db(email, refresh_token)
            
            # Создаем редирект на главную страницу с куками
            response = make_response(redirect(url_for('main')))
            response.set_cookie('access_token', access_token, httponly=True, secure=True, samesite='Strict')
            response.set_cookie('refresh_token', refresh_token, httponly=True, secure=True, samesite='Strict')
            return response
        else:
            flash('Неверный email или пароль.', 'error')

    return render_template('login.html', form=form, title="Вход в аккаунт")


# Выход из аккаунта
@auth_blueprint.route('/logout')
def logout():
    response = make_response(redirect('/'))
    response.set_cookie('access_token', '', expires=0)  # установка expires=0 удаляет куки
    response.set_cookie('refresh_token', '', expires=0)  # установка expires=0 удаляет куки
    return response
