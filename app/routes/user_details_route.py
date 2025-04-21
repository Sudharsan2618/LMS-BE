from flask import Blueprint, request, jsonify
from app.utils.db_utils import get_db_connection
from app.config.database import DB_CONFIG
from app.models.user_details_model import (
    get_user_details_with_badges_and_courses,
    update_user_details,
    insert_user_details
)

userdetails_bp = Blueprint('user_details', __name__)

@userdetails_bp.route('/api/userdetails', methods=['POST'])
def get_user_details_api():
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        user_details = get_user_details_with_badges_and_courses(conn, user_id)
        if user_details:
            return jsonify({'user_details': user_details}), 200
        else:
            # Return the user_id if no user details are found
            return jsonify({'user_id': user_id, 'message': 'No user details found for the given User ID'}), 200
    finally:
        conn.close()





@userdetails_bp.route('/api/userdetails/update', methods=['PUT'])
def update_user_details_api():
    data = request.get_json()
    user_id = data.get('user_id')


    if not user_id:
        return jsonify({'error': 'User ID and update data are required'}), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        rows_updated = update_user_details(conn, data)
        if rows_updated:
            return jsonify({'message': 'User updated successfully'}), 200
        else:
            return jsonify({'error': 'No rows updated. Check if the User ID exists'}), 404
    finally:
        conn.close()


@userdetails_bp.route('/api/userdetails/insert', methods=['POST'])
def insert_user_details_api():
    data = request.get_json()
    required_fields = [
        'user_id', 'user_name', 'age', 'mobile_number', 'mail_id', 'city',
        'area_of_interest', 'highest_qualification', 'year_of_passedout',
        'designation', 'ambition', 'current_organization', 'job_title',
        'work_experience', 'linkedin_profile', 'github_profile', 'portfolio_website', 'profile_picture_url'
    ]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        inserted = insert_user_details(conn, data)
        if inserted:
            return jsonify({'message': 'User inserted successfully'}), 201
        else:
            return jsonify({'error': 'User insertion failed'}), 500
    finally:
        conn.close()
