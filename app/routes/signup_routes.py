from flask import Blueprint, request, jsonify
from app.utils.db_utils import get_db_connection
from app.models.user_model import create_user, validate_unique_key
from app.config.database import DB_CONFIG

signup_bp = Blueprint('signup', __name__)

@signup_bp.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    unique_key = data.get('unique_key')

    if not username or not email or not password or not unique_key:
        return jsonify({'error': 'Username, email, password, and unique key are required'}), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        # Attempt to create the user with unique key
        result = create_user(conn, username, email, password, unique_key)
        
        if "error" in result:  # Check if the result contains an error message
            return jsonify({'error': result['error']}), 409  # Conflict: Email already exists
        
        return jsonify({'message': 'Sign-up successful', 'user': result}), 201  # User created successfully
    except Exception as e:
        return jsonify({'error': f'An error occurred: {e}'}), 500
    finally:
        conn.close()

@signup_bp.route('/api/validate-key', methods=['POST'])
def validate_key():
    data = request.get_json()
    unique_key = data.get('unique_key')

    if not unique_key:
        return jsonify({'error': 'Unique key is required'}), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        is_valid = validate_unique_key(conn, unique_key)
        return jsonify({'valid': is_valid}), 200
    except Exception as e:
        return jsonify({'error': f'An error occurred: {e}'}), 500
    finally:
        conn.close()
