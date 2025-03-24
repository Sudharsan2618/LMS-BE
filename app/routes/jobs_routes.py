from flask import Blueprint, jsonify
from app.utils.db_utils import get_db_connection
from app.models.jobs_model import get_all_jobs
from app.config.database import DB_CONFIG

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('/api/jobs', methods=['GET'])
def fetch_all_jobs():
    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        jobs = get_all_jobs(conn)
        return jsonify({'jobs': jobs}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()
