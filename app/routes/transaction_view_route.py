from flask import Blueprint, request, jsonify
from app.utils.db_utils import get_db_connection
from app.models.transaction_view_model import get_course_content_by_id
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
