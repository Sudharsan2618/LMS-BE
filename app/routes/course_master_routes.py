from flask import Blueprint, jsonify, request
from app.utils.db_utils import get_db_connection
from app.config.database import DB_CONFIG
from app.models.course_master_model import get_courses
from app.models.course_master_model import find_course_by_id, enroll_user_in_course

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
        

courseenrollment_bp = Blueprint('courseenrollment', __name__)

@courseenrollment_bp.route('/api/course/enrollment_details', methods=['POST'])
def get_course_enrollment_details():
    data = request.get_json()
    course_id = data.get('course_id')

    if not course_id:
        return jsonify({'error': 'Course ID is required'}), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        course = find_course_by_id(conn, course_id)
        if course:
            return jsonify({'course': course}), 200
        else:
            return jsonify({'error': 'Course not found'}), 404
    finally:
        conn.close()

userenrollment_bp = Blueprint('userenrollment', __name__)

@userenrollment_bp.route('/api/course/user_enroll', methods=['POST'])
def enroll_user():
    data = request.get_json()
    user_id = data.get('user_id')
    course_id = data.get('course_id')

    if not user_id or not course_id:
        return jsonify({'error': 'User ID and Course ID are required'}), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        enrollment = enroll_user_in_course(conn, user_id, course_id)
        if enrollment:
            return jsonify({'message': 'User enrolled successfully', 'enrollment': enrollment}), 200
        else:
            return jsonify({'error': 'Enrollment failed'}), 500
    finally:
        conn.close()