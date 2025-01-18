from flask import Blueprint, jsonify, request
from app.utils.db_utils import get_db_connection
from app.models.initial_assessment_response_model import upsert_initial_assessment_response
from app.config.database import DB_CONFIG

initial_assessment_responses_bp = Blueprint('responses', __name__)

@initial_assessment_responses_bp.route('/api/initial_assessment_response', methods=['POST'])
def post_initial_assessment_response():
    data = request.get_json()  # Get the data from the request body

    user_id = data.get('user_id')
    question_id = data.get('question_id')
    selected_option_id = data.get('selected_option_id')
    tab_id = data.get('tab_id')

    # Check if all required fields are provided
    if not user_id or not question_id or not selected_option_id or not tab_id:
        return jsonify({'error': 'User ID, Question ID, Selected Option ID, and Tab ID are required'}), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        # Perform upsert (insert or update) operation
        upsert_initial_assessment_response(conn, user_id, question_id, selected_option_id, tab_id)
        
        # Return success response
        return jsonify({'message': 'Response successfully saved or updated'}), 200

    finally:
        conn.close()
