from psycopg2.extras import RealDictCursor

def get_course_data(conn, course_id, user_id):
    query = "SELECT * FROM get_course_data(%s, %s)"
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (user_id, course_id))
        return cursor.fetchall()


def update_or_insert_course_progress(conn, user_id, course_id, course_subtitle_id, course_mastertitle_breakdown_id, course_subtitle_progress):
    procedure_call = """
    SELECT manage_user_course_progress(%s, %s, %s, %s, %s);
    """
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Call the stored procedure
        cursor.execute(procedure_call, (
            user_id, 
            course_id, 
            course_subtitle_id, 
            course_subtitle_progress, 
            course_mastertitle_breakdown_id
        ))
        
        # Fetch the returned average progress from the function
        result = cursor.fetchone()
        conn.commit()
        
        return {
            'action': 'stored_procedure_call',
            'average_progress': result['manage_user_course_progress']
        }
