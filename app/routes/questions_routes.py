from flask import Blueprint, jsonify, request
from app.utils.db_utils import get_db_connection
from app.models.questions_model import fetch_initial_assessment_questions_by_tab_id
from app.config.database import DB_CONFIG

initial_assessment_questions_bp = Blueprint('questions', __name__)

@initial_assessment_questions_bp.route('/api/initial_assessment_questions', methods=['POST'])
def post_initial_assessment_questions():
    data = request.get_json()  # Get the data from the request body

    tab_id = data.get('tab_id')
    user_id = data.get('user_id')

    if not tab_id or not user_id:
        return jsonify({'error': 'Both Tab ID and User ID are required'}), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        # Fetch questions with options and responses for the given tab_id and user_id
        questions = fetch_initial_assessment_questions_by_tab_id(conn, tab_id, user_id)

        if not questions:
            return jsonify({'error': 'No questions found for the provided Tab ID'}), 404

        # Extract the tab_name from the first question (since it should be the same for all questions in the same tab)
        tab_name = questions[0]['tab_name']

        # Format the response with question details and associated options
        formatted_questions = [
            {
                "question_id": question['question_id'],
                "question": question['question'],
                "options": question['options'],
                "selected_option": question['selected_option']
            }
            for question in questions
        ]

        # Return the tab_name along with the questions
        return jsonify({
            'tab_name': tab_name,
            'tab_id': tab_id,
            'user_id': user_id,
            'questions': formatted_questions
        }), 200

    finally:
        conn.close()
