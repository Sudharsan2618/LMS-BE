from flask import Blueprint, request, jsonify
from app.utils.db_utils import get_db_connection
from app.models.user_model import  find_user_by_email
from app.config.database import DB_CONFIG

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/login', methods=['POST'])
def login_with_email():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        user = find_user_by_email(conn, email, password)
        print(user)
        if user:
            return jsonify({'message': 'Login successful', 'user': user}), 200
        else:
            return jsonify({'error': 'Invalid email or password'}), 401
    finally:
        conn.close()
