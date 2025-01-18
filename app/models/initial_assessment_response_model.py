from psycopg2.extras import RealDictCursor

def upsert_initial_assessment_response(conn, user_id, question_id, selected_option_id, tab_id):
    query_update = """
    UPDATE lms.initial_assessment_responses
    SET selected_option_id = %s, tab_id = %s
    WHERE user_id = %s AND question_id = %s
    """
    
    query_insert = """
    INSERT INTO lms.initial_assessment_responses (user_id, question_id, selected_option_id, tab_id)
    VALUES (%s, %s, %s, %s)
    """

    with conn.cursor() as cursor:
        # Try to update the record first
        cursor.execute(query_update, (selected_option_id, tab_id, user_id, question_id))
        if cursor.rowcount == 0:  # If no row was updated, perform insert
            cursor.execute(query_insert, (user_id, question_id, selected_option_id, tab_id))
        conn.commit()
