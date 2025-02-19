from flask import Blueprint, request, jsonify
from app.utils.db_utils import get_db_connection
from app.config.database import DB_CONFIG
from app.models.initial_assessment_model import get_user_initial_assessment_details

user_initial_assessment_bp = Blueprint('user_initial_assessment', __name__)

@user_initial_assessment_bp.route('/api/user-initial-assessment-details', methods=['POST'])
def get_user_details_route():
    # Extract user_id from the request header
    data=request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({'error': 'user_id is required in the request body'}), 400
        
    user_id = data['user_id']

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        user_details = get_user_initial_assessment_details(conn, user_id)
        if user_details:
            return jsonify({'message': 'User details fetched successfully', 'user': user_details}), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    finally:
        conn.close()