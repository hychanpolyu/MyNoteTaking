from flask import Blueprint, jsonify, request, session

from src.auth import current_user, login_required
from src.models.note import Note
from src.models.user import User, db

user_bp = Blueprint('user', __name__)


def _credentials(data):
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    return username, email, password


@user_bp.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    username, email, password = _credentials(data)
    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password are required'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({'error': 'Username or email is already registered'}), 409

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    # Preserve notes created before authentication was introduced.
    Note.query.filter_by(user_id=None).update({'user_id': user.id})
    db.session.commit()
    session['user_id'] = user.id
    return jsonify(user.to_dict()), 201


@user_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401

    session.clear()
    session['user_id'] = user.id
    return jsonify(user.to_dict())


@user_bp.route('/auth/me', methods=['GET'])
def me():
    user = current_user()
    if user is None:
        return jsonify({'error': 'Authentication required'}), 401
    return jsonify(user.to_dict())


@user_bp.route('/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return '', 204


@user_bp.route('/users', methods=['GET'])
@login_required
def get_users(user):
    return jsonify([user.to_dict()])


@user_bp.route('/users', methods=['POST'])
@login_required
def create_user(_user):
    return jsonify({'error': 'Use /api/auth/register to create an account'}), 405


@user_bp.route('/users/<int:user_id>', methods=['GET'])
@login_required
def get_user(current, user_id):
    if current.id != user_id:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(current.to_dict())


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(current, user_id):
    if current.id != user_id:
        return jsonify({'error': 'User not found'}), 404
    user = current
    data = request.get_json(silent=True) or {}
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    if data.get('password'):
        user.set_password(data['password'])
    db.session.commit()
    return jsonify(user.to_dict())


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(current, user_id):
    if current.id != user_id:
        return jsonify({'error': 'User not found'}), 404
    db.session.delete(current)
    db.session.commit()
    return '', 204
