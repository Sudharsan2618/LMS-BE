from psycopg2.extras import RealDictCursor

def get_course_content_by_id(conn, course_id):
    """
    Get course content from course_content_transaction table by course_id
    """
    query = """
    SELECT 
        course_id, 
        course_mastertitle_breakdown_id, 
        course_mastertitle_breakdown, 
        course_subtitle_id, 
        course_subtitle, 
        subtitle_content, 
        subtitle_code, 
        subtitle_help_text, 
        helpfull_links
    FROM lms.course_content_transaction 
    WHERE course_id = %s
    ORDER BY course_content_id ASC
    """
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (course_id,))
        return cursor.fetchall()
