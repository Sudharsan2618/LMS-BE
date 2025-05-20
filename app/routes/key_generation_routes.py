from flask import Blueprint, request, jsonify, send_file
from app.utils.db_utils import get_db_connection
from app.config.database import DB_CONFIG
from app.models.batch_model import create_batch, associate_course_with_batch, create_login_key
import uuid
import csv
import io

key_generation_bp = Blueprint('key_generation', __name__)

@key_generation_bp.route('/api/generate-keys', methods=['POST'])
def generate_keys():
    data = request.get_json()
    num_users = data.get('num_users')
    batch_name = data.get('batch_name')
    course_ids = data.get('course_ids')  # Now expecting an array of course IDs
    validity_days = data.get('validity_days')
    
    if not all([num_users, batch_name, course_ids, validity_days]):
        return jsonify({'error': 'Missing required fields: num_users, batch_name, course_ids, validity_days'}), 400
    
    if not isinstance(num_users, int) or num_users <= 0:
        return jsonify({'error': 'Valid number of users is required'}), 400

    if not isinstance(course_ids, list) or len(course_ids) == 0:
        return jsonify({'error': 'course_ids must be a non-empty array'}), 400

    try:
        # Create batch
        batch_id = create_batch(batch_name)
        if not batch_id:
            return jsonify({'error': 'Failed to create batch'}), 500

        # Associate each course with the batch
        for course_id in course_ids:
            bc_id = associate_course_with_batch(batch_id, course_id, validity_days)
            if not bc_id:
                return jsonify({'error': f'Failed to associate course {course_id} with batch'}), 500

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
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name='generated_keys.csv'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500
