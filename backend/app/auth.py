import os
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, g


JWT_SECRET = os.getenv('JWT_SECRET', 'plantos-dev-secret-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '8'))


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except (ValueError, TypeError):
        return False


def generate_token(user_id: int, login: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        'sub': str(user_id),
        'login': login,
        'role': role,
        'iat': now,
        'exp': now + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def _extract_token():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    return auth_header.split(' ', 1)[1].strip()


def requires_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _extract_token()
        if not token:
            return jsonify({"erro": "Token de autenticação ausente"}), 401
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"erro": "Token expirado"}), 401
        except jwt.PyJWTError:
            return jsonify({"erro": "Token inválido"}), 401

        g.current_user = {
            'id': int(payload['sub']),
            'login': payload['login'],
            'role': payload['role'],
        }
        return fn(*args, **kwargs)
    return wrapper


def requires_role(*roles):
    def decorator(fn):
        @wraps(fn)
        @requires_auth
        def wrapper(*args, **kwargs):
            if g.current_user['role'] not in roles:
                return jsonify({
                    "erro": f"Acesso negado: requer perfil {', '.join(roles)}"
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
