from flask import Flask, request, jsonify, make_response
import datetime
import jwt
from config import *

def generate_access_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token

def generate_refresh_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)  # Refresh token действителен 7 дней
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token

def save_tokens(response, access_token, refresh_token):
    response.set_cookie(
        'access_token',
        access_token,
        httponly=True,  # Куки недоступны через JavaScript
        secure=True,    # Куки передаются только по HTTPS (в production)
        samesite='Strict'   # Защита от CSRF-атак
    )

    response.set_cookie(
        'refresh_token',
        refresh_token,
        httponly=True,  # Куки недоступны через JavaScript
        secure=True,    # Куки передаются только по HTTPS (в production)
        samesite='Strict'   # Защита от CSRF-атак
    )

    print("Токены сохранены!", response)
    return response

@app.route("/update_token", methods=['POST'])
def update_access_token():
    refresh_token = request.cookies.get('refresh_token')

    if not refresh_token:
        return jsonify({'message': 'Refresh token is missing!'}), 403

    try:
        data = jwt.decode(refresh_token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = data['user_id']

        # Генерируем новый access token
        new_access_token = generate_access_token(user_id)
        response = make_response(jsonify({'message': 'Token refreshed successfully!'}))
        return save_tokens(response, new_access_token, refresh_token)

    except:
        return jsonify({'message': 'Refresh token is invalid or expired!'}), 403

# def login_tokens(id, ):
