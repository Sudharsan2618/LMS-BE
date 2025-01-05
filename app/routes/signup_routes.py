from flask import Blueprint, request, jsonify
from app.utils.db_utils import get_db_connection
from app.models.user_model import create_user
from app.config.database import DB_CONFIG

signup_bp = Blueprint('signup', __name__)

@signup_bp.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password are required'}), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        # Create the user in the database
        user = create_user(conn, username, email, password)
        return jsonify({'message': 'Sign-up successful', 'user': user}), 201
    except Exception as e:
        if 'unique constraint' in str(e).lower():
            return jsonify({'error': 'Username or email already exists'}), 409
        else:
            return jsonify({'error': f'An error occurred: {e}'}), 500
    finally:
        conn.close()
