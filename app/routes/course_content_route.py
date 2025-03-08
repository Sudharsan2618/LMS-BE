from flask import Blueprint, request, jsonify
from app.utils.db_utils import get_db_connection
from app.models.course_content_model import get_course_data, update_or_insert_course_progress, user_course_status
from app.config.database import DB_CONFIG

course_content_bp = Blueprint('course_content', __name__)

@course_content_bp.route('/api/course-content', methods=['POST'])
def fetch_course_content():
    data = request.get_json()
    course_id = data.get('course_id')
    user_id = data.get('user_id')

    if not course_id or not user_id:
        return jsonify({'error': 'Course ID and User ID are required'}), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        course_content = get_course_data(conn, course_id, user_id)
        if course_content:
            return jsonify({'message': 'Course content fetched successfully', 'data': course_content}), 200
        else:
            return jsonify({'error': 'No course content found for the provided IDs'}), 404
    finally:
        conn.close()


@course_content_bp.route('/api/course-progress', methods=['POST'])
def update_or_insert_progress():
    data = request.get_json()
    user_id = data.get('user_id')
    course_id = data.get('course_id')
    course_subtitle_id = data.get('course_subtitle_id')
    course_mastertitle_breakdown_id = data.get('course_mastertitle_breakdown_id')
    course_subtitle_progress = data.get('course_subtitle_progress')

    if not all([user_id, course_id, course_subtitle_id, course_mastertitle_breakdown_id, course_subtitle_progress]):
        return jsonify({'error': 'All fields are required'}), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        result = update_or_insert_course_progress(
            conn, user_id, course_id, course_subtitle_id, 
            course_mastertitle_breakdown_id, course_subtitle_progress
        )
        return jsonify({'message': 'Operation successful', 'data': result}), 200
    finally:
        conn.close()


@course_content_bp.route('/api/userCourseStatus', methods=['POST'])
def get_user_course_status():
    data = request.get_json()
    user_id = data.get('user_id')
    course_id = data.get('course_id')


    if not all([user_id, course_id]):
        return jsonify({'error': 'All fields are required'}), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        result = user_course_status(
            conn, user_id, course_id
        )
        return jsonify({'message': 'Operation successful', 'data': result}), 200
    finally:
        conn.close()
