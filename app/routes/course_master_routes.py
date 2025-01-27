from flask import Blueprint, jsonify
from app.utils.db_utils import get_db_connection
from app.config.database import DB_CONFIG
from app.models.course_master_model import get_courses

course_bp = Blueprint('course', __name__)

@course_bp.route('/api/course-master', methods=['GET'])
def fetch_courses():
    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        courses = get_courses(conn)
        return jsonify({'courses': courses}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()
