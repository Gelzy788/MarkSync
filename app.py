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
from flask import make_response

# Главная страница
@app.route('/')
def main():
    # Проверяем наличие токенов в куках
    access_token = request.cookies.get('access_token')
    refresh_token = request.cookies.get('refresh_token')
    
    # Передаем информацию о наличии токенов в шаблон
    return render_template(
        'main.html', 
        title="Главная страница",
        is_authenticated=bool(access_token and refresh_token))

# Страница профиля
@app.route('/profile')
@token_required
def profile(user):
    return render_template('profile.html', user_id=user.ID, username=user.username, email=user.email, title="Профиль")


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', ssl_context=('ssl/cert.pem', 'ssl/key.pem'))