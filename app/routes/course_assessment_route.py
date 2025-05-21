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
        return jsonify({
            'status': 'error',
            'message': 'Question ID and Option Text are required'
        }), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({
            'status': 'error',
            'message': 'Database connection failed'
        }), 500

    try:
        question_data = find_answer_by_question_id(conn, question_id)
        if not question_data:
            return jsonify({
                'status': 'error',
                'message': 'Question not found'
            }), 404

        # Compare the provided option text with the stored answer
        is_correct = option_text.strip().lower() == question_data['answer'].strip().lower()
        
        return jsonify({
            'status': 'success',
            'is_correct': is_correct,
            'question': question_data['question'],
            'correct_answer': question_data['answer']
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    finally:
        conn.close()
