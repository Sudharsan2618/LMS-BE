from flask import Blueprint, jsonify, request
from app.models.course_master_model import get_batch_analytics_data
from app.utils.db_utils import get_db_connection
from app.config.database import DB_CONFIG
from app.models.user_model import find_admin_by_email

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