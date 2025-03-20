from flask import Flask, render_template, request, flash, redirect, url_for
from flask_login import logout_user, login_required, current_user, login_user
from flask_wtf.csrf import CSRFProtect
from database import *
from config import *
from models import *
from forms import *

login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

def authenticate_user(email, password):
    user = Users.query.filter_by(email=email).first() 
    if user and user.check_password(password):
        return user
    return None

@app.route('/')
def main():
    pass

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit(): 
        username = form.username.data
        email = form.email.data
        password = form.password.data

        res = add_user(username, email, password) 
        if res == 500:
            flash('Аккаунт успешно создан!', 'success')
            return redirect(url_for('login')) 
        else:
            flash('Ошибка создания аккаунта. Аккаунт с такой почтой уже существует!', 'error')
            print('Ошибка создания аккаунта. Аккаунт с такой почтой уже существует!', 'error')

    return render_template('register.html', form=form, title="Регистрация")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = authenticate_user(email, password) 
        if user:
            login_user(user)
            flash('Вы успешно вошли', 'success')
            return redirect(url_for('main'))
        else:
            flash('Неверный email или пароль.', 'error')
    return render_template('login.html', form=form, title="Вход в аккаунт")

@app.route('/profile')
@login_required
def profile_info():
    return render_template('profile.html', title="Профиль", user=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта.', 'success')
    return redirect(url_for('main'))


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')