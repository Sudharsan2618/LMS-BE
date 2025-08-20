from psycopg2.extras import RealDictCursor

def get_course_ppt_url(conn, course_id):
    """
    Get PPT URL for a specific course from course_master table
    
    :param conn: Database connection
    :param course_id: ID of the course
    :return: Dictionary with ppt_url or None if not found
    """
    query = "SELECT ppt_url FROM lms.course_master WHERE course_id = %s"
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (course_id,))
        result = cursor.fetchone()
        return result
