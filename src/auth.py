from functools import wraps

from flask import jsonify, session

from src.models.user import User


def current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        user = current_user()
        if user is None:
            session.pop('user_id', None)
            return jsonify({'error': 'Authentication required'}), 401
        return view(user, *args, **kwargs)

    return wrapped_view
