from flask import Blueprint, request, jsonify
import pandas as pd
from io import BytesIO
from app.utils.db_utils import get_db_connection
from app.models.course_model import create_course, create_course_enrollment, create_course_content
from app.config.database import DB_CONFIG

course_bp = Blueprint('course_management', __name__)

@course_bp.route('/api/courseMaster', methods=['POST'])
def create_course_master():
    data = request.get_json()
    required_fields = [
        'course_name', 'course_short_description', 'course_type',
        'course_duration_hours', 'course_duration_minutes',
        'language', 'rating', 'course_profile_image'
    ]
    
    # Check if all required fields are present
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        result = create_course(conn, data)
        return jsonify({'message': 'Course created successfully', 'course_id': result['course_id']}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    finally:
        conn.close()

@course_bp.route('/api/courseEnrollment', methods=['POST'])
def create_course_enrollment_details():
    data = request.get_json()
    required_fields = [
        'course_id', 'course_description', 'course_objective',
        'pre_requirments', 'course_level', 'roles', 'course_type'
    ]
    
    # Check if all required fields are present
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        result = create_course_enrollment(conn, data)
        return jsonify({
            'message': 'Course enrollment created successfully', 
            'enrollment_id': result['enrollment_id']
        }), 201
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        conn.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    finally:
        conn.close()

@course_bp.route('/api/courseContent/upload', methods=['POST'])
def upload_course_content():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['file']
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'Invalid file format. Please upload an Excel file'}), 400

    try:
        # Read Excel file
        df = pd.read_excel(BytesIO(file.read()))
        
        # Validate required columns
        required_columns = [
            'course_id', 'course_mastertitle_breakdown_id', 'course_subtitle_id'
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({'error': f'Missing required columns: {missing_columns}'}), 400

        # Handle empty cells and convert to string where needed
        df = df.fillna('')
        for col in df.columns:
            if col not in ['course_id', 'course_mastertitle_breakdown_id', 'course_subtitle_id']:
                df[col] = df[col].astype(str).str.strip()

        # Convert DataFrame to list of dictionaries
        course_contents = df.to_dict('records')
        
        if not course_contents:
            return jsonify({'error': 'Excel file is empty'}), 400

        conn = get_db_connection(DB_CONFIG)
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        try:
            result = create_course_content(conn, course_contents)
            return jsonify({
                'message': 'Course content uploaded successfully',
                'details': result
            }), 201
            
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 400
        except Exception as e:
            conn.rollback()
            return jsonify({'error': f'An error occurred: {str(e)}'}), 500
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'error': f'Error processing Excel file: {str(e)}'}), 400
