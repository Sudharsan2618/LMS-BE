from flask import Blueprint, jsonify, request
from app.models.course_master_model import get_batch_analytics_data
from app.utils.db_utils import get_db_connection
from app.config.database import DB_CONFIG
from app.models.user_model import find_admin_by_email, get_all_users
from app.models.batch_model import create_login_key
import csv
import io

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/api/admin/batch-analytics', methods=['GET'])
def get_batch_analytics():
    try:
        # Verify admin token
        conn = get_db_connection(DB_CONFIG)
        if conn is None:
            return jsonify({
                'status': 'error',
                'message': 'Failed to connect to database'
            }), 500
            
        analytics_data = get_batch_analytics_data(conn)
        
        if analytics_data is None:
            return jsonify({
                'status': 'error',
                'message': 'Failed to fetch batch analytics data'
            }), 500
            
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

@admin_bp.route('/api/admin/generate-user-keys', methods=['POST'])
def generate_user_keys():
    try:
        data = request.get_json()
        batch_id = data.get('batch_id')
        num_users = data.get('num_users', 1)  # Default to 1 if not specified

        if not batch_id:
            return jsonify({
                'status': 'error',
                'message': 'Batch ID is required'
            }), 400

        if not isinstance(num_users, int) or num_users <= 0:
            return jsonify({
                'status': 'error',
                'message': 'Number of users must be a positive integer'
            }), 400

        # Generate keys
        generated_keys = []
        for _ in range(num_users):
            key_id = create_login_key(batch_id)
            if key_id:
                generated_keys.append([key_id])

        # Create CSV in memory
        si = io.StringIO()
        writer = csv.writer(si)
        writer.writerow(['Key ID'])  # Header
        writer.writerows(generated_keys)
        
        # Create the response
        output = io.BytesIO()
        output.write(si.getvalue().encode())
        output.seek(0)
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully generated {len(generated_keys)} keys',
            'keys': generated_keys
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@admin_bp.route('/api/admin/extend-validity', methods=['POST'])
def extend_validity():
    try:
        data = request.get_json()
        batch_id = data.get('batch_id')
        course_id = data.get('course_id')
        validity_days = data.get('validity_days')

        if not all([batch_id, course_id, validity_days]):
            return jsonify({
                'status': 'error',
                'message': 'Batch ID, Course ID, and validity days are required'
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

        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE lms.batch_course 
                    SET validity = %s
                    WHERE batch_id = %s AND course_id = %s
                    RETURNING batch_id, course_id, validity
                    """,
                    (validity_days, batch_id, course_id)
                )
                updated_record = cursor.fetchone()
                conn.commit()

                if not updated_record:
                    return jsonify({
                        'status': 'error',
                        'message': 'No matching batch-course combination found'
                    }), 404

                return jsonify({
                    'status': 'success',
                    'message': 'Validity period updated successfully',
                    'data': {
                        'batch_id': updated_record[0],
                        'course_id': updated_record[1],
                        'validity_days': updated_record[2]
                    }
                }), 200

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@admin_bp.route('/api/admin/users', methods=['GET'])
def get_users():
    try:
        conn = get_db_connection(DB_CONFIG)
        if conn is None:
            return jsonify({
                'status': 'error',
                'message': 'Failed to connect to database'
            }), 500
            
        users = get_all_users(conn)
        
        return jsonify({
            'status': 'success',
            'data': users
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    finally:
        if 'conn' in locals():
            conn.close() 