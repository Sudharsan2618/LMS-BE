from flask import Blueprint, jsonify, request
from app.utils.db_utils import get_db_connection
from app.models.assessment_submission_model import submit_assessment_and_enroll_certificate
from app.config.database import DB_CONFIG

assessment_submission_bp = Blueprint('assessment_submission', __name__)

@assessment_submission_bp.route('/api/submit-assessment', methods=['POST'])
def submit_assessment():
    data = request.get_json()

    user_id = data.get('user_id')
    course_id = data.get('course_id')
    answers = data.get('answers')

    if not all([user_id, course_id, answers]):
        return jsonify({'error': 'user_id, course_id, and answers are required'}), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        success = submit_assessment_and_enroll_certificate(conn, user_id, course_id, answers)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Assessment submitted and certificate enrolled successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to submit assessment or enroll certificate'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

    finally:
        conn.close() 