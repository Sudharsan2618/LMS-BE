from flask import Blueprint, jsonify, request
from app.utils.db_utils import get_db_connection
from app.models.questions_model import fetch_initial_assessment_questions_by_tab_id
from app.config.database import DB_CONFIG

initial_assessment_questions_bp = Blueprint('questions', __name__)

@initial_assessment_questions_bp.route('/api/initial_assessment_questions', methods=['GET'])
def get_initial_assessment_questions():
    tab_id = request.args.get('tab_id')

    if not tab_id:
        return jsonify({'error': 'Tab ID is required'}), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        questions = fetch_initial_assessment_questions_by_tab_id(conn, tab_id)
        if not questions:
            return jsonify({'error': 'No questions found for the provided Tab ID'}), 404

        # Format response
        formatted_questions = [
            {
                "question_id": question['question_id'],
                "sequence_id": question['sequence_id'],
                "question": question['question'],
                "options": [
                    question['option_a'],
                    question['option_b'],
                    question['option_c'],
                    question['option_d']
                ]
            }
            for question in questions
        ]

        return jsonify({'tab_id': tab_id, 'questions': formatted_questions}), 200
    finally:
        conn.close()