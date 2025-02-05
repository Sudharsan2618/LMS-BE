from flask import Blueprint, jsonify
from app.utils.db_utils import get_db_connection
from app.config.database import DB_CONFIG
from app.models.ebook_model import get_ebook_details

ebook_bp = Blueprint('ebook', __name__)

@ebook_bp.route('/api/ebooks', methods=['GET'])
def fetch_ebook_details():
    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        ebooks = get_ebook_details(conn)
        if ebooks:
            return jsonify({'ebooks': ebooks}), 200
        else:
            return jsonify({'message': 'No eBooks found'}), 404
    finally:
        conn.close()
