from psycopg2.extras import RealDictCursor

def get_course_data(conn, course_id, user_id):
    query = "SELECT * FROM get_course_data(%s, %s)"
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (course_id, user_id))
        return cursor.fetchall()


def update_or_insert_course_progress(conn, user_id, course_id, course_subtitle_id, course_mastertitle_breakdown_id, course_progress, course_subtitle_progress):
    update_query = """
    UPDATE lms.user_course_progress
    SET course_progress = %s, course_subtitle_progress = %s
    WHERE user_id = %s AND course_id = %s AND course_subtitle_id = %s AND course_mastertitle_breakdown_id = %s
    """
    
    insert_query = """
    INSERT INTO lms.user_course_progress(
        ucp_id, user_id, course_id, course_subtitle_id, course_progress, course_subtitle_progress, course_mastertitle_breakdown_id)
    VALUES (DEFAULT, %s, %s, %s, %s, %s, %s)
    RETURNING ucp_id, user_id, course_id, course_subtitle_id, course_progress, course_subtitle_progress, course_mastertitle_breakdown_id
    """
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Attempt to update first
        cursor.execute(update_query, (
            course_progress, course_subtitle_progress, 
            user_id, course_id, course_subtitle_id, course_mastertitle_breakdown_id
        ))
        if cursor.rowcount > 0:  # If rows were updated
            conn.commit()
            return {'action': 'update', 'rows_affected': cursor.rowcount}

        # If no rows were updated, insert a new record
        cursor.execute(insert_query, (
            user_id, course_id, course_subtitle_id, 
            course_progress, course_subtitle_progress, course_mastertitle_breakdown_id
        ))
        conn.commit()
        return {'action': 'insert', 'data': cursor.fetchone()}