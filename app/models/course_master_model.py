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
        language, 
        rating 
    FROM lms.course_master
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        return cursor.fetchall()  # Fetch all rows as dictionaries

def find_course_by_id(conn, course_id):
    query = """
    SELECT c.course_id, m.course_name, c.course_description, c.course_objective, c.pre_requirments, c.course_level, c.roles, c.course_type
    FROM lms.course_enrollment c
	join lms.course_master as m on m.course_id = c.course_id
    WHERE c.course_id = %s
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