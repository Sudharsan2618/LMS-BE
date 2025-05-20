from flask import Blueprint, jsonify, request
from app.utils.db_utils import get_db_connection
from app.config.database import DB_CONFIG
from app.models.course_master_model import get_courses, find_course_by_id, enroll_user_in_course, get_user_courses_with_validity
from psycopg2.extras import RealDictCursor

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

@course_bp.route('/api/user-courses', methods=['GET'])
def fetch_user_courses():
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'User ID must be a number'}), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    cursor = None
    try:
        # Check if user exists
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT user_id, batch_id FROM lms.users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user['batch_id']:
            return jsonify({'error': 'User is not assigned to any batch'}), 404

        # Get courses
        courses = get_user_courses_with_validity(conn, user_id)
        
        if not courses:
            return jsonify({
                'courses': []
            }), 200

        return jsonify({
            'courses': courses
        }), 200

    except Exception as e:
        print(f"Error in fetch_user_courses: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        conn.close()

courseenrollment_bp = Blueprint('courseenrollment', __name__)

@courseenrollment_bp.route('/api/course/enrollment_details', methods=['POST'])
def get_course_enrollment_details():
    data = request.get_json()
    course_id = data.get('course_id')
    user_id = data.get('user_id')

    if not course_id:
        return jsonify({'error': 'Course ID is required'}), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        course = find_course_by_id(conn, user_id,course_id)
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