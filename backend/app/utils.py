"""Shared authentication and role-check helpers."""

import jwt
from functools import wraps
from flask import request, jsonify, current_app
from app.models import User

def token_required(f):
    """Require a valid JWT and pass its user to the route."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'error': {'message': 'Access token is missing', 'type': 'auth_error'}}), 401

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': {'message': 'Invalid user token', 'type': 'auth_error'}}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': {'message': 'Token has expired', 'type': 'auth_error'}}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': {'message': 'Invalid token', 'type': 'auth_error'}}), 401

        return f(current_user, *args, **kwargs)
    return decorated

def roles_required(*roles):
    """Allow the route only for the listed user roles."""
    def decorator(f):
        @wraps(f)
        def decorated(current_user, *args, **kwargs):
            if current_user.role not in roles:
                return jsonify({'error': {'message': f'Access restricted to roles: {list(roles)}', 'type': 'forbidden'}}), 403
            return f(current_user, *args, **kwargs)
        return decorated
    return decorator
