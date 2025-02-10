from flask import Blueprint, request, jsonify
from app.utils.db_utils import get_db_connection
from app.models.course_assessment_model import find_answer_by_question_id
from app.config.database import DB_CONFIG

course_assessment_bp = Blueprint('course_assessment', __name__)

@course_assessment_bp.route('/api/check_answer', methods=['POST'])
def check_answer():
    data = request.get_json()
    question_id = data.get('question_id')
    option_text = data.get('option_text')

    if not question_id or not option_text:
        return jsonify({'error': 'Question ID and Option Text are required'}), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        correct_answer = find_answer_by_question_id(conn, question_id)
        if not correct_answer:
            return jsonify({'error': 'Question ID not found'}), 404

        if correct_answer['answer'].strip().lower() == option_text.strip().lower():
            return jsonify({'result': 'Correct'}), 200
        else:
            return jsonify({'result': 'False'}), 200
    finally:
        conn.close()
