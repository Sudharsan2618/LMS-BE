from flask import Blueprint, request, jsonify
from app.utils.db_utils import get_db_connection
from app.models.transaction_view_model import get_course_content_by_id, get_course_questions_by_id, approve_course_content
from app.models.ppt_generation_model import generate_ppt_for_course
from app.config.database import DB_CONFIG

transaction_view_bp = Blueprint('transaction_view', __name__)

@transaction_view_bp.route('/api/transaction-view/course-content/<int:course_id>', methods=['GET'])
def get_course_content_transaction(course_id):
    """
    Get course content from transaction table by course_id
    """
    try:
        conn = get_db_connection(DB_CONFIG)
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        course_content = get_course_content_by_id(conn, course_id)
        conn.close()
        
        if course_content:
            return jsonify({
                'message': 'Course content retrieved successfully',
                'course_id': course_id,
                'content_count': len(course_content),
                'data': course_content
            }), 200
        else:
            return jsonify({
                'message': 'No course content found',
                'course_id': course_id,
                'content_count': 0,
                'data': []
            }), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transaction_view_bp.route('/api/transaction-view/questions/<int:course_id>', methods=['GET'])
def get_course_questions_transaction(course_id):
    """
    Get questions and answers from course_assessment table by course_id
    """
    try:
        conn = get_db_connection(DB_CONFIG)
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        questions = get_course_questions_by_id(conn, course_id)
        conn.close()
        
        if questions:
            return jsonify({
                'message': 'Questions retrieved successfully',
                'course_id': course_id,
                'question_count': len(questions),
                'data': questions
            }), 200
        else:
            return jsonify({
                'message': 'No questions found',
                'course_id': course_id,
                'question_count': 0,
                'data': []
            }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transaction_view_bp.route('/api/transaction-view/approve-course/<int:course_id>', methods=['POST'])
def approve_course_transaction(course_id):
    """
    Approve a course by calling the process_course_content stored procedure
    and generate PPT with S3 upload and database update
    """
    try:
        conn = get_db_connection(DB_CONFIG)
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Step 1: Approve course content
        approve_course_content(conn, course_id)
        
        # Step 2: Generate PPT with full workflow (S3 upload + DB update)
        try:
            ppt_result = generate_ppt_for_course(
                course_id=course_id,
                filename=None,  # Auto-generate filename
                template_path=None,  # Use default template
                max_slides=30,
                upload_to_cloud=True
            )
            
            response_data = {
                'message': 'Course approved and PPT generated successfully',
                'course_id': course_id,
                'ppt_filename': ppt_result['filename'],
                'ppt_url': ppt_result['cloud_url'],
                'ppt_generated': True
            }
            
            if ppt_result['cloud_url']:
                response_data['ppt_status'] = 'Uploaded to S3 and database updated'
            else:
                response_data['ppt_status'] = 'Generated locally only (S3 upload failed)'
                response_data['local_path'] = ppt_result['local_path']
            
        except Exception as ppt_error:
            # Course approval succeeded, but PPT generation failed
            response_data = {
                'message': 'Course approved successfully, but PPT generation failed',
                'course_id': course_id,
                'ppt_generated': False,
                'ppt_error': str(ppt_error)
            }
        
        conn.close()
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
