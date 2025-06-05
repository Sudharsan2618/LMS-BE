from flask import Blueprint, request, jsonify
from app.models.qc_batch_model import (
    create_qc_batch, 
    update_user_qc_id, 
    create_qc_user_course,
    get_qc_batch_analytics,
    add_course_to_user,
    extend_course_validity,
    get_detailed_qc_analytics
)
from app.utils.db_utils import get_db_connection
from app.config.database import DB_CONFIG
import json

qc_batch_bp = Blueprint('qc_batch', __name__)

@qc_batch_bp.route('/api/qc-batch/create', methods=['POST'])
def create_qc_batch_route():
    try:
        data = request.get_json()
        batch_name = data.get('batch_name')
        user_courses = data.get('user_courses')

        if not batch_name or not user_courses:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields: batch_name and user_courses'
            }), 400

        # Create QC batch
        qc_id = create_qc_batch(batch_name)
        if not qc_id:
            return jsonify({
                'status': 'error',
                'message': 'Failed to create QC batch'
            }), 500

        results = []
        errors = []

        # Process each user and their courses
        for user_data in user_courses:
            user_id = user_data.get('user_id')
            courses = user_data.get('courses')

            if not user_id or not courses:
                errors.append(f"Invalid data for user: {user_id}")
                continue

            # Update user's qc_id
            updated_user = update_user_qc_id(user_id, qc_id)
            if not updated_user:
                errors.append(f"Failed to update QC ID for user: {user_id}")
                continue

            # Create course associations
            user_course_results = []
            for course in courses:
                course_id = course.get('course_id')
                validity_days = course.get('validity_days')

                if not course_id or not validity_days:
                    errors.append(f"Invalid course data for user {user_id}")
                    continue

                qcuc_id = create_qc_user_course(qc_id, user_id, course_id, validity_days)
                if qcuc_id:
                    user_course_results.append({
                        'course_id': course_id,
                        'validity_days': validity_days,
                        'qcuc_id': qcuc_id
                    })
                else:
                    errors.append(f"Failed to create course association for user {user_id} and course {course_id}")

            results.append({
                'user_id': user_id,
                'courses': user_course_results
            })

        return jsonify({
            'status': 'success',
            'data': {
                'qc_id': qc_id,
                'batch_name': batch_name,
                'results': results,
                'errors': errors if errors else None
            }
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@qc_batch_bp.route('/api/qc-batch/analytics', methods=['GET'])
def get_qc_analytics():
    try:
        conn = get_db_connection(DB_CONFIG)
        if conn is None:
            return jsonify({
                'status': 'error',
                'message': 'Failed to connect to database'
            }), 500
            
        analytics_data = get_qc_batch_analytics(conn)
        
        return jsonify({
            'status': 'success',
            'data': analytics_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

@qc_batch_bp.route('/api/qc-batch/add-course', methods=['POST'])
def add_course():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        course_id = data.get('course_id')
        validity_days = data.get('validity_days')

        if not all([user_id, course_id, validity_days]):
            return jsonify({
                'status': 'error',
                'message': 'User ID, Course ID, and validity days are required'
            }), 400

        if not isinstance(validity_days, int) or validity_days <= 0:
            return jsonify({
                'status': 'error',
                'message': 'Validity days must be a positive integer'
            }), 400

        conn = get_db_connection(DB_CONFIG)
        if not conn:
            return jsonify({
                'status': 'error',
                'message': 'Failed to connect to database'
            }), 500

        qcuc_id = add_course_to_user(conn, user_id, course_id, validity_days)
        
        if not qcuc_id:
            return jsonify({
                'status': 'error',
                'message': 'Failed to add course. User might not be in a QC batch.'
            }), 400

        return jsonify({
            'status': 'success',
            'message': 'Course added successfully',
            'data': {
                'qcuc_id': qcuc_id,
                'user_id': user_id,
                'course_id': course_id,
                'validity_days': validity_days
            }
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

@qc_batch_bp.route('/api/qc-batch/extend-validity', methods=['POST'])
def extend_validity():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        course_id = data.get('course_id')
        new_validity_days = data.get('validity_days')

        if not all([user_id, course_id, new_validity_days]):
            return jsonify({
                'status': 'error',
                'message': 'User ID, Course ID, and validity days are required'
            }), 400

        if not isinstance(new_validity_days, int) or new_validity_days <= 0:
            return jsonify({
                'status': 'error',
                'message': 'Validity days must be a positive integer'
            }), 400

        conn = get_db_connection(DB_CONFIG)
        if not conn:
            return jsonify({
                'status': 'error',
                'message': 'Failed to connect to database'
            }), 500

        qcuc_id = extend_course_validity(conn, user_id, course_id, new_validity_days)
        
        if not qcuc_id:
            return jsonify({
                'status': 'error',
                'message': 'No matching user-course combination found'
            }), 404

        return jsonify({
            'status': 'success',
            'message': 'Validity period updated successfully',
            'data': {
                'qcuc_id': qcuc_id,
                'user_id': user_id,
                'course_id': course_id,
                'validity_days': new_validity_days
            }
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

@qc_batch_bp.route('/api/qc-batch/detailed-analytics', methods=['GET'])
def get_detailed_analytics():
    try:
        conn = get_db_connection(DB_CONFIG)
        if conn is None:
            return jsonify({
                'status': 'error',
                'message': 'Failed to connect to database'
            }), 500
            
        analytics_data = get_detailed_qc_analytics(conn)
        
        if analytics_data is None:
            return jsonify({
                'status': 'error',
                'message': 'Failed to fetch detailed analytics data'
            }), 500
            
        try:
            # Parse the JSON string from PostgreSQL
            parsed_data = json.loads(analytics_data)
            return jsonify({
                'status': 'success',
                'data': parsed_data
            }), 200
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Invalid data format received from database'
            }), 500
        
    except Exception as e:
        print(f"Error in get_detailed_analytics route: {str(e)}")  # Add logging
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()