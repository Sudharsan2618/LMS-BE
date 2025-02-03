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

def find_course_by_id(conn, course_id):
    query = """
    SELECT course_id, course_description, course_objective, pre_requirments, course_level, roles, course_type
    FROM lms.course_enrollment
    WHERE course_id = %s
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (course_id,))
        return cursor.fetchone()
    
def enroll_user_in_course(conn, user_id, course_id):
    insert_query = """
    INSERT INTO lms.user_course_enrollment (user_id, course_id, enrollment_date)
    VALUES (%s, %s, CURRENT_DATE)
    RETURNING enrollment_id, user_id, course_id, enrollment_date
    """
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(insert_query, (user_id, course_id))
        conn.commit()
        return cursor.fetchone()