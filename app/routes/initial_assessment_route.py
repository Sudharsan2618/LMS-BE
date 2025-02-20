from flask import Blueprint, request, jsonify
from app.utils.db_utils import get_db_connection
from app.config.database import DB_CONFIG
from app.models.initial_assessment_model import get_user_initial_assessment_details

user_initial_assessment_bp = Blueprint('user_initial_assessment', __name__)

@user_initial_assessment_bp.route('/api/user-initial-assessment-details', methods=['POST'])
def get_user_details_route():
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        # Insert or update the assessment results in the database
        success = get_user_initial_assessment_details(conn, user_id)
        
        if success:
            return jsonify({'message': 'Assessment results successfully recorded'}), 200
        else:
            return jsonify({'error': 'Failed to record assessment results'}), 500
    finally:
        conn.close()
