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

def get_course_questions_by_id(conn, course_id):
    """
    Get questions and answers from course_assessment table by course_id
    """
    query = """
    SELECT question, answer FROM lms.course_assessment WHERE course_id = %s
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (course_id,))
        return cursor.fetchall()

def approve_course_content(conn, course_id):
    """
    Call the process_course_content stored procedure for course approval
    """
    with conn.cursor() as cursor:
        cursor.execute("CALL process_course_content(%s)", (course_id,))
        conn.commit()
