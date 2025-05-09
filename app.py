from flask import Flask, render_template, request, flash, redirect, url_for
from flask_login import logout_user, login_required, current_user, login_user
from flask_wtf.csrf import CSRFProtect
from flask_wtf.csrf import CSRFError
from werkzeug.utils import secure_filename
import os
import subprocess

from database import *
from config import *
from models import *
from forms import *
import whisper

login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

def authenticate_user(email, password):
    user = Users.query.filter_by(email=email).first() 
    if user and user.check_password(password):
        return user
    return None

def add_voice_message(message):
    try:
        new_message = VoiceMessages(text=message, user_id=current_user.id)
        db.session.add(new_message)
        db.session.commit()
        return 500  # Успешно
    except Exception as e:
        print(f"Ошибка сохранения сообщения: {e}")
        return 401  # Ошибка

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


@app.route('/record_voice_message', methods=['GET', 'POST'])
@csrf.exempt
@login_required
def record_voice_message():
    if request.method == 'POST':
        # Отладочные сообщения
        print("Method:", request.method)
        print("Headers:", request.headers)
        print("Files:", request.files)
        print("Form:", request.form)
        print("Data:", request.data)
        print("request.files:", request.files)
        print("request.form:", request.form)
        print("request.content_type:", request.content_type)
        if 'audio' not in request.files:
            return {"error": "Файл 'audio' не найден"}, 400

        audio_file = request.files['audio']
        filename = secure_filename(audio_file.filename)

        os.makedirs('temp', exist_ok=True)  # <- Создаем папку, если нет
        audio_path = os.path.join('temp', filename)
        audio_file.save(audio_path)

        try:
            converted_path = "temp/recording.wav"
            subprocess.run(["ffmpeg", "-y", "-i", audio_path, converted_path])
            
            # Загрузка модели Whisper
            model = whisper.load_model("base")
            result = model.transcribe(converted_path)
            transcription = result['text']
            return {"transcription": transcription}, 200
        except Exception as e:
            return {"error": str(e)}, 500
        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)

    return render_template('record_voice_message.html', title="Запись голосового сообщения")


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)