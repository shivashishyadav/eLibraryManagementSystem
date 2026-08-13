# Register, Login, User profile

import jwt
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import User
from app.utils import token_required

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    if not isinstance(data, dict):
        return jsonify({'error': {'message': 'Request body must be a JSON object'}}), 400
    if not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': {'message': 'Missing required fields: username, email, password'}}), 400

    if User.query.filter((User.email == data['email']) | (User.username == data['username'])).first():
        return jsonify({'error': {'message': 'User with this email or username already exists'}}), 409

    if data.get('role', 'member') != 'member':
        return jsonify({
            'error': {
                'message': 'Public registration only creates member accounts'
            }
        }), 403

    user = User(username=data['username'], email=data['email'], role='member')
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully', 'user': {'id': user.id, 'username': user.username, 'role': user.role}}), 201

    
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not isinstance(data, dict):
        return jsonify({
            'error': {
                'message': 'Request body must be a JSON object'
            }
        }), 400

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({
            'error': {
                'message': 'Email and password are required'
            }
        }), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({
            'error': {
                'message': 'Invalid email or password'
            }
        }), 401

    payload = {
        'user_id': user.id,
        'role': user.role,
        'exp': datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
    }

    token = jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm="HS256"
    )

    return jsonify({
        'access_token': token,
        'role': user.role,
        'expires_in': 86400
    }), 200
    
    
@auth_bp.route('/me', methods=['GET'])
@token_required
def me(current_user):
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'role': current_user.role
    }), 200
