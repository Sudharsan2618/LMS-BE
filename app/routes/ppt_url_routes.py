from flask import Blueprint, jsonify
from app.utils.db_utils import get_db_connection
from app.config.database import DB_CONFIG
from app.models.ppt_url_model import get_course_ppt_url

ppt_url_bp = Blueprint('ppt_url', __name__)

@ppt_url_bp.route('/api/course-ppt-url/<int:course_id>', methods=['GET'])
def get_course_ppt_url_route(course_id):
    """
    Get PPT URL for a specific course by course_id
    """
    try:
        conn = get_db_connection(DB_CONFIG)
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        result = get_course_ppt_url(conn, course_id)
        conn.close()
        
        if result and result['ppt_url']:
            return jsonify({
                'course_id': course_id,
                'ppt_url': result['ppt_url'],
                'status': 'success'
            }), 200
        else:
            return jsonify({
                'course_id': course_id,
                'ppt_url': None,
                'status': 'not_found',
                'message': 'No PPT URL found for this course'
            }), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
