from flask import Blueprint, request, jsonify
from app.utils.db_utils import get_db_connection
from app.config.database import DB_CONFIG
from app.models.user_persona_model import get_user_persona

user_bp = Blueprint('user', __name__)

@user_bp.route('/api/user/persona', methods=['POST'])
def get_user_persona_api():
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        user_persona = get_user_persona(conn, user_id)
        if user_persona:
            return jsonify({'user_persona': user_persona}), 200
        else:
            return jsonify({'error': 'User persona not found for the given User ID'}), 404
    finally:
        conn.close()
