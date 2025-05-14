from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import update
from archive.autorisation import *
from config import *
from data.__all_models import *

# # Добавление пользователя в бд
# def add_user(username, email, password):
#     hashed_password = generate_password_hash(password)
#     new_user = Users(email=email, password=hashed_password, username=username)
#     db.session.add(new_user)
#     try:
#         db.session.commit()
#         return 200
#     except Exception as e:
#         print("ERROR", e)
#         return 401

# # Получение id пользователя для авторизации 
# def login_user_db(email, password):
#     user = Users.query.filter_by(email=email).first()
#     if user and check_password_hash(user.password, password):
#         return user.ID, 200
#     else:
#         return "Пользователь не найден"
    
# Добавление в бд refresh токен профиля
# def add_refresh_token_db(email, refresh_token):
#     stmt = (
#         update(Users)
#         # Используем атрибут напрямую
#         .where(Users.email == email)
#         .values(
#             refresh_token = refresh_token
#         )
#     )

#     try:
#         db.session.execute(stmt)  # Выполняем запрос
#         db.session.commit()  # Зафиксируйте изменения
#         return True
#     except Exception as e:
#         print('ОТКАТЫВАЮ ИЗМЕНЕНИЯ...', e)
#         db.session.rollback()  # Откатите изменения в случае ошибки
#         return str(e)
