from flask import Blueprint, jsonify
from app.utils.db_utils import get_db_connection
from app.config.database import DB_CONFIG
from app.models.home_header_model import get_home_headers

home_bp = Blueprint('home', __name__)

@home_bp.route('/api/home-headers', methods=['GET'])
def fetch_home_headers():
    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        headers = get_home_headers(conn)
        return jsonify({'headers': headers}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()
