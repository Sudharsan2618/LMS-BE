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
        # Attempt to create the user
        result = create_user(conn, username, email, password)
        
        if "error" in result:  # Check if the result contains an error message
            return jsonify({'error': result['error']}), 409  # Conflict: Email already exists
        
        return jsonify({'message': 'Sign-up successful', 'user': result}), 201  # User created successfully
    except Exception as e:
        return jsonify({'error': f'An error occurred: {e}'}), 500
    finally:
        conn.close()
