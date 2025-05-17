from flask import Blueprint, request, jsonify
from app.utils.db_utils import get_db_connection
from app.models.user_model import  find_user_by_email, find_admin_by_email
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
        # First check in users table
        user = find_user_by_email(conn, email, password)
        if user:
            return jsonify({'message': 'Login successful', 'user': user}), 200

        # If not found in users, check in admin table
        admin = find_admin_by_email(conn, email, password)
        if admin:
            return jsonify({'message': 'Login successful', 'user': admin}), 200

        return jsonify({'error': 'Invalid email or password'}), 401
    finally:
        conn.close()
