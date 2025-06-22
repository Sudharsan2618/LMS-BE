from flask import Blueprint, request, jsonify
from app.utils.db_utils import get_db_connection
from app.models.transaction_view_model import get_course_content_by_id, get_course_questions_by_id, approve_course_content
from app.config.database import DB_CONFIG

transaction_view_bp = Blueprint('transaction_view', __name__)

@transaction_view_bp.route('/api/transaction-view/course-content/<int:course_id>', methods=['GET'])
def get_course_content_transaction(course_id):
    """
    Get course content from transaction table by course_id
    """
    try:
        conn = get_db_connection(DB_CONFIG)
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        course_content = get_course_content_by_id(conn, course_id)
        conn.close()
        
        if course_content:
            return jsonify({
                'message': 'Course content retrieved successfully',
                'course_id': course_id,
                'content_count': len(course_content),
                'data': course_content
            }), 200
        else:
            return jsonify({
                'message': 'No course content found',
                'course_id': course_id,
                'content_count': 0,
                'data': []
            }), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transaction_view_bp.route('/api/transaction-view/questions/<int:course_id>', methods=['GET'])
def get_course_questions_transaction(course_id):
    """
    Get questions and answers from course_assessment table by course_id
    """
    try:
        conn = get_db_connection(DB_CONFIG)
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        questions = get_course_questions_by_id(conn, course_id)
        conn.close()
        
        if questions:
            return jsonify({
                'message': 'Questions retrieved successfully',
                'course_id': course_id,
                'question_count': len(questions),
                'data': questions
            }), 200
        else:
            return jsonify({
                'message': 'No questions found',
                'course_id': course_id,
                'question_count': 0,
                'data': []
            }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transaction_view_bp.route('/api/transaction-view/approve-course/<int:course_id>', methods=['POST'])
def approve_course_transaction(course_id):
    """
    Approve a course by calling the process_course_content stored procedure
    """
    try:
        conn = get_db_connection(DB_CONFIG)
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        approve_course_content(conn, course_id)
        conn.close()
        
        return jsonify({
            'message': 'Course approved and content moved to main table successfully',
            'course_id': course_id
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
