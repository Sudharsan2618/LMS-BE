from psycopg2.extras import RealDictCursor

def get_courses(conn):
    query = """
    SELECT 
        course_id, 
        course_name, 
        course_short_description, 
        course_type, 
        course_duration_hours, 
        course_duration_minutes, 
        course_status, 
        course_progress, 
        language, 
        rating 
    FROM lms.course_master
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        return cursor.fetchall()  # Fetch all rows as dictionaries
