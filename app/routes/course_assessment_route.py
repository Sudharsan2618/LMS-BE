from flask import Blueprint, request, jsonify
from app.utils.db_utils import get_db_connection
from app.models.course_assessment_model import find_answer_by_question_and_option
from app.config.database import DB_CONFIG

course_assessment_bp = Blueprint('course_assessment', __name__)

@course_assessment_bp.route('/api/check_answer', methods=['POST'])
def check_answer():
    data = request.get_json()
    question_id = data.get('question_id')
    option_id = data.get('option_id')
    option_text = data.get('option_text')  # Keeping this for backward compatibility

    if not question_id or not option_id:
        return jsonify({
            'status': 'error',
            'message': 'Question ID and Option ID are required'
        }), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({
            'status': 'error',
            'message': 'Database connection failed'
        }), 500

    try:
        # Check if the option_id matches the answer for this question
        answer_data = find_answer_by_question_and_option(conn, question_id, option_id)
        
        # If we found a matching answer, it means the option_id is correct
        is_correct = answer_data is not None
        
        return jsonify({
            'status': 'success',
            'is_correct': is_correct,
            'question': answer_data['question'] if answer_data else None,
            'selected_option': option_text
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    finally:
        conn.close()
