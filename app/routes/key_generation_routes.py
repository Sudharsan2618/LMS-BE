from flask import Blueprint, request, jsonify, send_file
from app.utils.db_utils import get_db_connection
from app.config.database import DB_CONFIG
import uuid
import csv
import io

key_generation_bp = Blueprint('key_generation', __name__)

@key_generation_bp.route('/api/generate-keys', methods=['POST'])
def generate_keys():
    data = request.get_json()
    num_users = data.get('num_users')
    
    if not num_users or not isinstance(num_users, int) or num_users <= 0:
        return jsonify({'error': 'Valid number of users is required'}), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()
        generated_keys = []

        # Generate and insert unique keys
        for _ in range(num_users):
            unique_key = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO lms.new_login (code, used) VALUES (%s, %s)",
                (unique_key, "no")
            )
            generated_keys.append([unique_key])

        conn.commit()

        # Create CSV in memory
        si = io.StringIO()
        writer = csv.writer(si)
        writer.writerow(['Unique Key'])  # Header
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
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
